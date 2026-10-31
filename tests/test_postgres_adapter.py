"""Tests the PostgreSQL code path of database.py with a fake psycopg2.

The fake driver is backed by SQLite, so this checks the adapter logic
(placeholder translation, pooling, dict rows, reconnect handling, schema
variant) but NOT real PostgreSQL behaviour. Always do one real test with
your Neon / Supabase database too (see README).
"""

import importlib.util
import os
import sqlite3
import sys
import tempfile
import types
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_fake_psycopg2(db_file):
    fake = types.ModuleType("psycopg2")
    pool_mod = types.ModuleType("psycopg2.pool")
    extras_mod = types.ModuleType("psycopg2.extras")

    class IntegrityError(Exception):
        pass

    class OperationalError(Exception):
        pass

    class InterfaceError(Exception):
        pass

    class RealDictCursor:
        pass

    class FakeCursor:
        def __init__(self, conn):
            self._cur = conn._raw.cursor()

        def execute(self, sql, params=()):
            assert "?" not in sql, "placeholders must be translated to %s"
            sql = sql.replace("%s", "?").replace(
                "SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT"
            )
            try:
                self._cur.execute(sql, params)
            except sqlite3.IntegrityError as error:
                raise IntegrityError(str(error))

        def _dict(self, row):
            names = [d[0] for d in self._cur.description]
            return dict(zip(names, row))

        def fetchone(self):
            row = self._cur.fetchone()
            return self._dict(row) if row else None

        def fetchall(self):
            return [self._dict(r) for r in self._cur.fetchall()]

        def close(self):
            self._cur.close()

    class FakeConn:
        def __init__(self):
            self._raw = sqlite3.connect(db_file)
            self._raw.execute("PRAGMA foreign_keys = ON")
            self.closed = 0

        def cursor(self, cursor_factory=None):
            return FakeCursor(self)

        def commit(self):
            self._raw.commit()

        def rollback(self):
            self._raw.rollback()

        def close(self):
            self._raw.close()
            self.closed = 1

    class ThreadedConnectionPool:
        instances = []

        def __init__(self, minconn, maxconn, dsn, **kwargs):
            self.dsn = dsn
            self.free = []
            self.closed_by_pool = 0
            ThreadedConnectionPool.instances.append(self)

        def getconn(self):
            return self.free.pop() if self.free else FakeConn()

        def putconn(self, conn, close=False):
            if close:
                conn.close()
                self.closed_by_pool += 1
            else:
                self.free.append(conn)

        def closeall(self):
            for conn in self.free:
                conn.close()

    fake.IntegrityError = IntegrityError
    fake.OperationalError = OperationalError
    fake.InterfaceError = InterfaceError
    pool_mod.ThreadedConnectionPool = ThreadedConnectionPool
    extras_mod.RealDictCursor = RealDictCursor
    fake.pool = pool_mod
    fake.extras = extras_mod
    return fake, pool_mod, extras_mod, ThreadedConnectionPool


class PostgresAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_file = os.path.join(tempfile.mkdtemp(), "fakepg.db")
        fake, pool_mod, extras_mod, cls.Pool = build_fake_psycopg2(cls.db_file)
        cls._saved = {k: sys.modules.get(k) for k in ("psycopg2", "psycopg2.pool", "psycopg2.extras")}
        sys.modules["psycopg2"] = fake
        sys.modules["psycopg2.pool"] = pool_mod
        sys.modules["psycopg2.extras"] = extras_mod

        spec = importlib.util.spec_from_file_location(
            "database_pg", os.path.join(ROOT, "database.py")
        )
        cls.db = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.db)
        cls.db.set_database_url("postgresql://user:pw@host/dbname")
        cls.db.create_database()

    @classmethod
    def tearDownClass(cls):
        cls.db.set_database_url(None)
        for key, value in cls._saved.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value

    def test_backend_label(self):
        self.assertIn("PostgreSQL", self.db.backend_label())

    def test_full_flow(self):
        db = self.db
        ok, msg = db.create_user("pg_user", "Password123", "PG User")
        self.assertTrue(ok, msg)
        self.assertFalse(db.create_user("pg_user", "Password123")[0])  # duplicate -> IntegrityError path
        ok, msg, user = db.authenticate("pg_user", "Password123")
        self.assertTrue(ok, msg)

        db.set_done(user["id"], "skill", "R", "S", True)
        db.set_note(user["id"], "task", "R", "T", "https://x.y")
        self.assertTrue(db.get_progress_map(user["id"], "skill", "R")["S"])
        self.assertEqual(db.get_role_progress(user["id"], "R")["task"]["T"], (False, "https://x.y"))

        from datetime import date
        self.assertTrue(db.add_study_log(user["id"], date.today(), "R", "T", 25)[0])
        summary = db.get_study_summary(user["id"])
        self.assertEqual((summary["total_minutes"], summary["streak"]), (25, 1))

        token = db.create_session(user["id"])
        self.assertEqual(db.get_user_by_session(token)["username"], "pg_user")
        db.delete_user(user["id"])
        self.assertIsNone(db.get_user_by_session(token))  # cascade removed the session

    def test_dead_connection_is_replaced(self):
        db = self.db
        pool = self.Pool.instances[-1]
        self.assertTrue(pool.free, "a connection should be waiting in the pool")
        pool.free[0].closed = 1  # simulate Neon closing an idle connection
        db.create_user("pg_user2", "Password123")
        self.assertTrue(db.authenticate("pg_user2", "Password123")[0])


if __name__ == "__main__":
    unittest.main()
