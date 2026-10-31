import os
import tempfile
import unittest
from datetime import date, timedelta

_tmp = tempfile.mkdtemp()
os.environ["SKILLMAP_DB"] = os.path.join(_tmp, "test.db")

import database as db  # noqa: E402


class DatabaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db.create_database()

    def make_user(self, name):
        ok, msg = db.create_user(name, "Password123", "Test User")
        self.assertTrue(ok, msg)
        ok, msg, user = db.authenticate(name, "Password123")
        self.assertTrue(ok, msg)
        return user

    def test_signup_validation(self):
        self.assertFalse(db.create_user("a", "Password123")[0])
        self.assertFalse(db.create_user("bad name!", "Password123")[0])
        self.assertFalse(db.create_user("validname", "short1")[0])
        self.assertFalse(db.create_user("validname", "onlyletters")[0])

    def test_duplicate_username(self):
        self.make_user("dupuser")
        ok, msg = db.create_user("DupUser", "Password123")
        self.assertFalse(ok)
        self.assertIn("taken", msg)

    def test_login_and_lockout(self):
        self.make_user("lockme")
        self.assertFalse(db.authenticate("lockme", "wrong")[0])
        for _ in range(db.MAX_FAILED_ATTEMPTS):
            db.authenticate("lockme", "wrong")
        ok, msg, _ = db.authenticate("lockme", "Password123")
        self.assertFalse(ok)
        self.assertIn("Too many", msg)

    def test_progress_is_per_user(self):
        a = self.make_user("user_a")
        b = self.make_user("user_b")
        db.set_done(a["id"], "skill", "Python Intern", "Functions", True)
        self.assertTrue(db.get_progress_map(a["id"], "skill", "Python Intern")["Functions"])
        self.assertEqual(db.get_progress_map(b["id"], "skill", "Python Intern"), {})

    def test_note_and_done_do_not_overwrite_each_other(self):
        u = self.make_user("notes_user")
        db.set_note(u["id"], "task", "R", "T", "https://example.com")
        db.set_done(u["id"], "task", "R", "T", True)
        self.assertEqual(db.get_notes_map(u["id"], "task", "R")["T"], "https://example.com")
        self.assertTrue(db.get_progress_map(u["id"], "task", "R")["T"])

    def test_reset_progress(self):
        u = self.make_user("reset_user")
        db.set_done(u["id"], "skill", "R", "S", True)
        db.reset_progress(u["id"], "R")
        self.assertEqual(db.get_progress_map(u["id"], "skill", "R"), {})

    def test_study_logs_and_streak(self):
        u = self.make_user("study_user")
        today = date.today()
        for offset in (0, 1, 2, 4):
            ok, msg = db.add_study_log(u["id"], today - timedelta(days=offset), "R", "T", 30)
            self.assertTrue(ok, msg)
        summary = db.get_study_summary(u["id"])
        self.assertEqual(summary["streak"], 3)
        self.assertEqual(summary["total_minutes"], 120)
        self.assertEqual(len(db.get_daily_minutes(u["id"], 14)), 14)
        self.assertFalse(db.add_study_log(u["id"], today + timedelta(days=1), "R", "T", 30)[0])
        self.assertFalse(db.add_study_log(u["id"], today, "R", "T", 0)[0])

    def test_delete_log_only_own(self):
        a = self.make_user("log_a")
        b = self.make_user("log_b")
        db.add_study_log(a["id"], date.today(), "R", "T", 10)
        log_id = db.get_study_logs(a["id"])[0]["id"]
        db.delete_study_log(b["id"], log_id)
        self.assertEqual(len(db.get_study_logs(a["id"])), 1)
        db.delete_study_log(a["id"], log_id)
        self.assertEqual(len(db.get_study_logs(a["id"])), 0)

    def test_profile_and_password(self):
        u = self.make_user("prof_user")
        self.assertTrue(db.update_profile(u["id"], "New Name", 8)[0])
        self.assertEqual(db.get_user(u["id"])["full_name"], "New Name")
        self.assertFalse(db.update_profile(u["id"], "", 8)[0])
        self.assertFalse(db.update_profile(u["id"], "X", 500)[0])
        self.assertFalse(db.change_password(u["id"], "bad", "Newpass123")[0])
        self.assertTrue(db.change_password(u["id"], "Password123", "Newpass123")[0])
        self.assertTrue(db.authenticate("prof_user", "Newpass123")[0])

    def test_delete_user_cascades(self):
        u = self.make_user("gone_user")
        db.set_done(u["id"], "skill", "R", "S", True)
        db.add_study_log(u["id"], date.today(), "R", "T", 10)
        db.delete_user(u["id"])
        self.assertIsNone(db.get_user(u["id"]))
        self.assertEqual(db.get_progress_map(u["id"], "skill", "R"), {})
        self.assertEqual(db.get_study_logs(u["id"]), [])


    def test_sessions(self):
        u = self.make_user("sess_user")
        token = db.create_session(u["id"])
        self.assertEqual(db.get_user_by_session(token)["username"], "sess_user")
        self.assertIsNone(db.get_user_by_session("x" * 30))
        self.assertIsNone(db.get_user_by_session("bad token!"))
        db.delete_session(token)
        self.assertIsNone(db.get_user_by_session(token))

    def test_expired_session(self):
        u = self.make_user("sess_exp")
        token = db.create_session(u["id"], days=-1)
        self.assertIsNone(db.get_user_by_session(token))

    def test_password_change_ends_sessions(self):
        u = self.make_user("sess_pw")
        token = db.create_session(u["id"])
        self.assertTrue(db.change_password(u["id"], "Password123", "Newpass123")[0])
        self.assertIsNone(db.get_user_by_session(token))

    def test_get_role_progress(self):
        u = self.make_user("role_prog")
        db.set_done(u["id"], "skill", "R", "S1", True)
        db.set_note(u["id"], "task", "R", "T1", "https://x.y")
        data = db.get_role_progress(u["id"], "R")
        self.assertEqual(data["skill"]["S1"], (True, ""))
        self.assertEqual(data["task"]["T1"], (False, "https://x.y"))
        self.assertEqual(db.get_role_progress(u["id"], "OTHER"), {})


if __name__ == "__main__":
    unittest.main()
