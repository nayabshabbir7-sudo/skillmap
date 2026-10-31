"""SkillMap database layer.

Two backends, chosen automatically:
  * SQLite     - default (local file, great for development).
  * PostgreSQL - used when DATABASE_URL is set (environment variable or
                 Streamlit secret). This gives permanent cloud storage.

Every row of progress data belongs to a user account.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta

DB_PATH = os.environ.get("SKILLMAP_DB") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "skillmap_app.db"
)

PBKDF2_ITERATIONS = 200_000
MAX_FAILED_ATTEMPTS = 5
LOCK_SECONDS = 300
SESSION_DAYS = 14

USERNAME_RE = re.compile(r"^[a-z0-9_.]{3,20}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_\-]{20,100}$")

CATEGORY_SKILL = "skill"
CATEGORY_TASK = "task"
CATEGORY_INTERVIEW = "interview"


# -------------------- BACKEND SELECTION --------------------
_database_url = None
_url_checked = False
_pool = None
_pool_lock = threading.Lock()
_last_used = {}  # id(raw connection) -> time of last use (PostgreSQL only)


def get_database_url():
    """Return the PostgreSQL URL, or None when SQLite should be used."""
    global _database_url, _url_checked

    if _url_checked:
        return _database_url

    url = os.environ.get("DATABASE_URL")

    if not url:
        try:
            import streamlit as st

            url = st.secrets.get("DATABASE_URL")
        except Exception:  # no secrets file / streamlit not installed
            url = None

    url = (url or "").strip() or None
    if url and url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    _database_url = url
    _url_checked = True
    return url


def set_database_url(url):
    """Force a backend (used by tests). Pass None for SQLite."""
    global _database_url, _url_checked, _pool

    with _pool_lock:
        if _pool is not None:
            try:
                _pool.closeall()
            except Exception:
                pass
        _pool = None

    _last_used.clear()
    _database_url = url
    _url_checked = True


def backend_label():
    if get_database_url():
        return "PostgreSQL (permanent cloud database)"
    return "SQLite (local file)"


def _integrity_errors():
    errors = (sqlite3.IntegrityError,)
    if get_database_url():
        import psycopg2

        errors += (psycopg2.IntegrityError,)
    return errors


def _connection_errors():
    if get_database_url():
        import psycopg2

        return (psycopg2.OperationalError, psycopg2.InterfaceError)
    return ()


def _get_pool():
    global _pool

    if _pool is None:
        with _pool_lock:
            if _pool is None:
                from psycopg2.pool import ThreadedConnectionPool

                _pool = ThreadedConnectionPool(
                    1,
                    10,
                    get_database_url(),
                    connect_timeout=10,
                    keepalives=1,
                    keepalives_idle=30,
                )
    return _pool


def _checkout(pool):
    """Get a live PostgreSQL connection (idle ones are pinged first)."""
    for _ in range(3):
        raw = pool.getconn()
        try:
            if raw.closed:
                raise ConnectionError("closed")

            idle = time.time() - _last_used.get(id(raw), 0)
            if idle > 20:
                cursor = raw.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                raw.rollback()
            return raw
        except Exception:
            _last_used.pop(id(raw), None)
            pool.putconn(raw, close=True)

    return pool.getconn()


class _Connection:
    """Small wrapper so the rest of the code can use one style of SQL ('?')."""

    def __init__(self, raw, is_postgres):
        self.raw = raw
        self.is_postgres = is_postgres
        self._cursors = []

    def execute(self, sql, params=()):
        if not self.is_postgres:
            return self.raw.execute(sql, params)

        from psycopg2.extras import RealDictCursor

        cursor = self.raw.cursor(cursor_factory=RealDictCursor)
        self._cursors.append(cursor)
        cursor.execute(sql.replace("?", "%s"), params)
        return cursor

    def close_cursors(self):
        for cursor in self._cursors:
            try:
                cursor.close()
            except Exception:
                pass
        self._cursors = []


@contextmanager
def get_connection():
    if not get_database_url():
        raw = sqlite3.connect(DB_PATH, timeout=15)
        raw.row_factory = sqlite3.Row
        raw.execute("PRAGMA foreign_keys = ON")
        connection = _Connection(raw, False)
        try:
            yield connection
            raw.commit()
        except Exception:
            raw.rollback()
            raise
        finally:
            raw.close()
        return

    pool = _get_pool()
    raw = _checkout(pool)
    connection = _Connection(raw, True)
    broken = False
    try:
        yield connection
        raw.commit()
    except Exception as error:
        try:
            raw.rollback()
        except Exception:
            broken = True
        if isinstance(error, _connection_errors()):
            broken = True
        raise
    finally:
        connection.close_cursors()
        if broken:
            _last_used.pop(id(raw), None)
        else:
            _last_used[id(raw)] = time.time()
        pool.putconn(raw, close=broken)


def create_database():
    is_postgres = bool(get_database_url())
    primary_key = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"

    statements = [
        f"""
        CREATE TABLE IF NOT EXISTS users (
            id {primary_key},
            username TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            weekly_goal_hours DOUBLE PRECISION NOT NULL DEFAULT 5,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until DOUBLE PRECISION NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS progress (
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            category TEXT NOT NULL,
            role TEXT NOT NULL,
            item TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            note TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, category, role, item)
        )
        """,
        f"""
        CREATE TABLE IF NOT EXISTS study_logs (
            id {primary_key},
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            log_date TEXT NOT NULL,
            role TEXT NOT NULL,
            topic TEXT NOT NULL,
            minutes INTEGER NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_study_user_date ON study_logs (user_id, log_date)",
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at DOUBLE PRECISION NOT NULL,
            created_at TEXT NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id)",
    ]

    if not is_postgres:
        folder = os.path.dirname(DB_PATH)
        if folder:
            os.makedirs(folder, exist_ok=True)

    with get_connection() as connection:
        if not is_postgres:
            connection.execute("PRAGMA journal_mode = WAL")
        for statement in statements:
            connection.execute(statement)


# -------------------- PASSWORDS --------------------
def _hash_password(password, salt_bytes):
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt_bytes,
        PBKDF2_ITERATIONS,
    ).hex()


def validate_password(password):
    """Return an error message, or None when the password is acceptable."""
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if len(password) > 128:
        return "Password is too long (maximum 128 characters)."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "Password must contain at least one letter and one number."
    return None


def normalize_username(username):
    return (username or "").strip().lower()


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _row_to_user(row):
    return {
        "id": row["id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "weekly_goal_hours": float(row["weekly_goal_hours"]),
        "created_at": row["created_at"],
    }


# -------------------- USERS --------------------
def create_user(username, password, full_name=""):
    username = normalize_username(username)

    if not USERNAME_RE.match(username):
        return False, (
            "Username must be 3-20 characters and can only contain "
            "letters, numbers, dots or underscores."
        )

    error = validate_password(password or "")
    if error:
        return False, error

    full_name = (full_name or "").strip()[:60] or username

    salt = secrets.token_bytes(16)
    password_hash = _hash_password(password, salt)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users
                    (username, full_name, password_hash, salt, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, full_name, password_hash, salt.hex(), _now()),
            )
    except _integrity_errors():
        return False, "That username is already taken."

    return True, "Account created successfully."


def authenticate(username, password):
    """Return (ok, message, user_dict_or_None)."""
    username = normalize_username(username)
    password = password or ""
    generic_error = "Invalid username or password."

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if row is None:
            # Same amount of work as a real check (avoids user enumeration by timing)
            _hash_password(password, b"0" * 16)
            return False, generic_error, None

        now = time.time()
        if row["locked_until"] and row["locked_until"] > now:
            minutes = int((row["locked_until"] - now) // 60) + 1
            return (
                False,
                f"Too many failed attempts. Try again in about {minutes} minute(s).",
                None,
            )

        expected = row["password_hash"]
        actual = _hash_password(password, bytes.fromhex(row["salt"]))

        if hmac.compare_digest(expected, actual):
            connection.execute(
                "UPDATE users SET failed_attempts = 0, locked_until = 0 WHERE id = ?",
                (row["id"],),
            )
            return True, "Logged in.", _row_to_user(row)

        attempts = row["failed_attempts"] + 1
        locked_until = 0
        if attempts >= MAX_FAILED_ATTEMPTS:
            locked_until = now + LOCK_SECONDS
            attempts = 0

        connection.execute(
            "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
            (attempts, locked_until, row["id"]),
        )

    return False, generic_error, None


def get_user(user_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return _row_to_user(row) if row else None


def update_profile(user_id, full_name, weekly_goal_hours):
    full_name = (full_name or "").strip()[:60]
    if not full_name:
        return False, "Name cannot be empty."

    try:
        weekly_goal_hours = float(weekly_goal_hours)
    except (TypeError, ValueError):
        return False, "Weekly goal must be a number."

    if not 1 <= weekly_goal_hours <= 80:
        return False, "Weekly goal must be between 1 and 80 hours."

    with get_connection() as connection:
        connection.execute(
            "UPDATE users SET full_name = ?, weekly_goal_hours = ? WHERE id = ?",
            (full_name, weekly_goal_hours, user_id),
        )
    return True, "Profile updated."


def change_password(user_id, old_password, new_password):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if row is None:
            return False, "Account not found."

        actual = _hash_password(old_password or "", bytes.fromhex(row["salt"]))
        if not hmac.compare_digest(row["password_hash"], actual):
            return False, "Current password is incorrect."

        error = validate_password(new_password or "")
        if error:
            return False, error

        salt = secrets.token_bytes(16)
        connection.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
            (_hash_password(new_password, salt), salt.hex(), user_id),
        )
        # Log the account out everywhere else after a password change
        connection.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    return True, "Password changed successfully."


def delete_user(user_id):
    with get_connection() as connection:
        connection.execute("DELETE FROM users WHERE id = ?", (user_id,))


# -------------------- PROGRESS (skills / tasks / interview) --------------------
def set_done(user_id, category, role, item, done):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO progress (user_id, category, role, item, done, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, category, role, item)
            DO UPDATE SET done = excluded.done, updated_at = excluded.updated_at
            """,
            (user_id, category, role, item, int(bool(done)), _now()),
        )


def set_note(user_id, category, role, item, note):
    note = (note or "").strip()[:500]
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO progress (user_id, category, role, item, note, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, category, role, item)
            DO UPDATE SET note = excluded.note, updated_at = excluded.updated_at
            """,
            (user_id, category, role, item, note, _now()),
        )


def get_progress_map(user_id, category, role):
    """Return {item: bool} for one user / category / role."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT item, done FROM progress
            WHERE user_id = ? AND category = ? AND role = ?
            """,
            (user_id, category, role),
        ).fetchall()
    return {row["item"]: bool(row["done"]) for row in rows}


def get_notes_map(user_id, category, role):
    """Return {item: note} for one user / category / role."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT item, note FROM progress
            WHERE user_id = ? AND category = ? AND role = ?
            """,
            (user_id, category, role),
        ).fetchall()
    return {row["item"]: row["note"] for row in rows}


def get_role_progress(user_id, role):
    """One query for everything of a role: {category: {item: (done, note)}}."""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT category, item, done, note FROM progress
            WHERE user_id = ? AND role = ?
            """,
            (user_id, role),
        ).fetchall()

    result = {}
    for row in rows:
        result.setdefault(row["category"], {})[row["item"]] = (
            bool(row["done"]),
            row["note"],
        )
    return result


def reset_progress(user_id, role):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM progress WHERE user_id = ? AND role = ?",
            (user_id, role),
        )


# -------------------- STUDY LOGS --------------------
def add_study_log(user_id, log_date, role, topic, minutes, note=""):
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return False, "Minutes must be a number."

    if not 1 <= minutes <= 720:
        return False, "Minutes must be between 1 and 720."

    if isinstance(log_date, (date, datetime)):
        log_date = log_date.isoformat()[:10]

    try:
        parsed = date.fromisoformat(str(log_date))
    except ValueError:
        return False, "Invalid date."

    if parsed > date.today():
        return False, "You cannot log a session in the future."

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO study_logs
                (user_id, log_date, role, topic, minutes, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                parsed.isoformat(),
                role,
                (topic or "Other").strip()[:80],
                minutes,
                (note or "").strip()[:200],
                _now(),
            ),
        )
    return True, "Study session saved."


def get_study_logs(user_id, limit=None):
    query = """
        SELECT id, log_date, role, topic, minutes, note
        FROM study_logs
        WHERE user_id = ?
        ORDER BY log_date DESC, id DESC
    """
    params = [user_id]
    if limit:
        query += " LIMIT ?"
        params.append(int(limit))

    with get_connection() as connection:
        rows = connection.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def delete_study_log(user_id, log_id):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM study_logs WHERE id = ? AND user_id = ?",
            (log_id, user_id),
        )


def get_daily_minutes(user_id, days=14):
    """Return [(date, minutes)] for the last `days` days (zeros included)."""
    today = date.today()
    start = today - timedelta(days=days - 1)

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT log_date, SUM(minutes) AS total
            FROM study_logs
            WHERE user_id = ? AND log_date >= ?
            GROUP BY log_date
            """,
            (user_id, start.isoformat()),
        ).fetchall()

    totals = {row["log_date"]: row["total"] for row in rows}
    result = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        result.append((day, int(totals.get(day.isoformat(), 0))))
    return result


def get_study_summary(user_id):
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    with get_connection() as connection:
        totals = connection.execute(
            """
            SELECT COALESCE(SUM(minutes), 0) AS total_minutes,
                   COUNT(*) AS sessions,
                   COALESCE(SUM(CASE WHEN log_date >= ? THEN minutes ELSE 0 END), 0) AS week_minutes
            FROM study_logs
            WHERE user_id = ?
            """,
            (week_start.isoformat(), user_id),
        ).fetchone()

        dates = {
            row["log_date"]
            for row in connection.execute(
                "SELECT DISTINCT log_date FROM study_logs WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        }

    streak = 0
    if today.isoformat() in dates:
        cursor_day = today
    elif (today - timedelta(days=1)).isoformat() in dates:
        cursor_day = today - timedelta(days=1)
    else:
        cursor_day = None

    while cursor_day is not None and cursor_day.isoformat() in dates:
        streak += 1
        cursor_day -= timedelta(days=1)

    return {
        "total_minutes": int(totals["total_minutes"]),
        "sessions": int(totals["sessions"]),
        "week_minutes": int(totals["week_minutes"]),
        "streak": streak,
    }


# -------------------- LOGIN SESSIONS (stay logged in after refresh) --------------------
def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id, days=SESSION_DAYS):
    """Create a login session and return the secret token (only its hash is stored)."""
    token = secrets.token_urlsafe(32)
    now = time.time()

    with get_connection() as connection:
        connection.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
        connection.execute(
            """
            INSERT INTO sessions (token_hash, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (_token_hash(token), user_id, now + days * 86400, _now()),
        )
    return token


def get_user_by_session(token):
    if not token or not TOKEN_RE.match(token):
        return None

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT u.*, s.expires_at AS session_expires
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ?
            """,
            (_token_hash(token),),
        ).fetchone()

        if row is None:
            return None

        if row["session_expires"] < time.time():
            connection.execute(
                "DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),)
            )
            return None

    return _row_to_user(row)


def delete_session(token):
    if not token:
        return
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),)
        )