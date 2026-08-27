"""Tests for db.py. Run: python -m unittest -v test_db"""

import os
import pathlib
import tempfile
import time
import unittest

# Must be set before importing db -- it opens the database at import time.
_TMP = pathlib.Path(tempfile.mkdtemp(prefix="lanyard-test-"))
os.environ["LANYARD_DB"] = str(_TMP / "test.db")
os.environ.setdefault("EMAIL_PEPPER", "test-pepper")

import db  # noqa: E402

EMAIL = "student@sheridancollege.ca"
OTHER = "other@sheridancollege.ca"
HOUR = 3600


class Base(unittest.TestCase):
    """Fresh, empty tables before every test."""

    @classmethod
    def setUpClass(cls):
        db.init()

    def setUp(self):
        for table in ("guild_config", "pending", "verified"):
            db.conn.execute(f"DELETE FROM {table}")

    def now(self):
        return int(time.time())

    def count(self, table):
        return db.conn.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]


class TestHashing(Base):
    def test_normalizes_case_and_whitespace(self):
        self.assertEqual(
            db.email_key("  STUDENT@Sheridancollege.CA "), db.email_key(EMAIL)
        )

    def test_different_emails_differ(self):
        self.assertNotEqual(db.email_key(EMAIL), db.email_key(OTHER))

    def test_is_not_reversible_to_plaintext(self):
        h = db.email_key(EMAIL)
        self.assertNotIn("sheridancollege", h)
        self.assertNotIn("student", h)

    def test_shape_is_sha256_hex(self):
        h = db.email_key(EMAIL)
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in h))

    def test_pepper_actually_participates(self):
        import hashlib

        self.assertNotEqual(
            db.code_key("123456"), hashlib.sha256(b"123456").hexdigest()
        )

    def test_code_key_is_deterministic(self):
        self.assertEqual(db.code_key("012345"), db.code_key(" 012345 "))

    def test_leading_zero_codes_survive(self):
        self.assertNotEqual(db.code_key("000123"), db.code_key("123"))


class TestGuildConfig(Base):
    def test_set_then_get(self):
        db.set_guild_role(1, 99)
        self.assertEqual(db.get_guild_role(1), 99)

    def test_unset_guild_is_none(self):
        self.assertIsNone(db.get_guild_role(12345))

    def test_rerunning_verify_repoints_role(self):
        db.set_guild_role(1, 99)
        db.set_guild_role(1, 100)
        self.assertEqual(db.get_guild_role(1), 100)
        self.assertEqual(self.count("guild_config"), 1)

    def test_guilds_are_independent(self):
        db.set_guild_role(1, 99)
        db.set_guild_role(2, 100)
        self.assertEqual((db.get_guild_role(1), db.get_guild_role(2)), (99, 100))


class TestPending(Base):
    def test_create_then_get_roundtrips(self):
        db.create_pending(7, db.email_key(EMAIL), db.code_key("111111"), self.now() + 900)
        row = db.get_pending(7)
        self.assertEqual(row["email_hash"], db.email_key(EMAIL))
        self.assertEqual(row["code_hash"], db.code_key("111111"))
        self.assertEqual(row["attempts"], 0)

    def test_missing_user_is_none(self):
        self.assertIsNone(db.get_pending(404))

    def test_expired_reads_as_missing(self):
        db.create_pending(7, db.email_key(EMAIL), db.code_key("111111"), self.now() - 1)
        self.assertIsNone(db.get_pending(7))

    def test_expiry_boundary_is_exclusive(self):
        # expires_at == now is already expired (WHERE expires_at > now).
        db.create_pending(7, db.email_key(EMAIL), db.code_key("111111"), self.now())
        self.assertIsNone(db.get_pending(7))

    def test_resend_replaces_code_and_resets_attempts(self):
        db.create_pending(7, db.email_key(EMAIL), db.code_key("111111"), self.now() + 900)
        db.bump_attempts(7)
        db.bump_attempts(7)
        db.create_pending(7, db.email_key(EMAIL), db.code_key("222222"), self.now() + 900)
        row = db.get_pending(7)
        self.assertEqual(row["attempts"], 0)
        self.assertEqual(row["code_hash"], db.code_key("222222"))
        self.assertEqual(self.count("pending"), 1, "resend must not create a second row")

    def test_old_code_stops_working_after_resend(self):
        db.create_pending(7, db.email_key(EMAIL), db.code_key("111111"), self.now() + 900)
        db.create_pending(7, db.email_key(EMAIL), db.code_key("222222"), self.now() + 900)
        self.assertNotEqual(db.get_pending(7)["code_hash"], db.code_key("111111"))

    def test_bump_returns_running_total(self):
        db.create_pending(7, db.email_key(EMAIL), db.code_key("111111"), self.now() + 900)
        self.assertEqual([db.bump_attempts(7) for _ in range(3)], [1, 2, 3])

    def test_bump_on_missing_user_returns_zero(self):
        self.assertEqual(db.bump_attempts(404), 0)

    def test_clear_removes_row(self):
        db.create_pending(7, db.email_key(EMAIL), db.code_key("111111"), self.now() + 900)
        db.clear_pending(7)
        self.assertIsNone(db.get_pending(7))

    def test_clear_on_missing_user_is_harmless(self):
        db.clear_pending(404)  # must not raise

    def test_users_do_not_collide(self):
        db.create_pending(7, db.email_key(EMAIL), db.code_key("111111"), self.now() + 900)
        db.create_pending(8, db.email_key(OTHER), db.code_key("222222"), self.now() + 900)
        db.clear_pending(7)
        self.assertIsNotNone(db.get_pending(8))


class TestMarkVerified(Base):
    def setUp(self):
        super().setUp()
        self.E = db.email_key(EMAIL)

    def test_happy_path(self):
        db.create_pending(1, self.E, db.code_key("111111"), self.now() + 900)
        self.assertTrue(db.mark_verified(1, self.E))
        self.assertIsNone(db.get_pending(1), "pending must be consumed")
        self.assertTrue(db.is_email_used(self.E))

    def test_alt_account_with_same_email_is_rejected(self):
        db.mark_verified(1, self.E)
        self.assertFalse(db.mark_verified(2, self.E))
        self.assertEqual(self.count("verified"), 1)

    def test_rejected_attempt_leaves_no_partial_write(self):
        db.mark_verified(1, self.E)
        db.create_pending(2, self.E, db.code_key("222222"), self.now() + 900)
        db.mark_verified(2, self.E)
        self.assertIsNone(
            db.conn.execute("SELECT 1 FROM verified WHERE discord_id = 2").fetchone()
        )
        self.assertIsNotNone(db.get_pending(2), "rollback must restore the pending row")

    def test_same_user_reverifying_succeeds(self):
        db.mark_verified(1, self.E)
        self.assertTrue(db.mark_verified(1, self.E))
        self.assertEqual(self.count("verified"), 1)

    def test_same_user_new_address_updates_in_place(self):
        db.mark_verified(1, self.E)
        self.assertTrue(db.mark_verified(1, db.email_key(OTHER)))
        self.assertEqual(self.count("verified"), 1)
        self.assertTrue(db.is_email_used(db.email_key(OTHER)))
        self.assertFalse(db.is_email_used(self.E), "old address is released")

    def test_race_exactly_one_winner(self):
        # Both callers passed is_email_used() before either committed.
        self.assertFalse(db.is_email_used(self.E))
        results = [db.mark_verified(3, self.E), db.mark_verified(4, self.E)]
        self.assertEqual(sorted(results), [False, True])

    def test_works_without_a_pending_row(self):
        self.assertTrue(db.mark_verified(1, self.E))

    def test_does_not_touch_other_users_pending(self):
        db.create_pending(2, db.email_key(OTHER), db.code_key("222222"), self.now() + 900)
        db.mark_verified(1, self.E)
        self.assertIsNotNone(db.get_pending(2))

    def test_unused_email_is_not_reported_used(self):
        self.assertFalse(db.is_email_used(db.email_key("nobody@sheridancollege.ca")))


class TestPurge(Base):
    def test_removes_only_expired(self):
        db.create_pending(1, db.email_key(EMAIL), db.code_key("111111"), self.now() - 1)
        db.create_pending(2, db.email_key(OTHER), db.code_key("222222"), self.now() + HOUR)
        self.assertEqual(db.purge_expired(), 1)
        self.assertIsNotNone(db.get_pending(2))

    def test_returns_zero_when_nothing_expired(self):
        db.create_pending(1, db.email_key(EMAIL), db.code_key("111111"), self.now() + HOUR)
        self.assertEqual(db.purge_expired(), 0)

    def test_empty_table_is_safe(self):
        self.assertEqual(db.purge_expired(), 0)


class TestTransaction(Base):
    def test_rollback_undoes_partial_work(self):
        with self.assertRaises(RuntimeError):
            with db._tx():
                db.conn.execute("INSERT INTO guild_config VALUES (1, 99)")
                raise RuntimeError("boom")
        self.assertEqual(self.count("guild_config"), 0)

    def test_commit_persists(self):
        with db._tx():
            db.conn.execute("INSERT INTO guild_config VALUES (1, 99)")
        self.assertEqual(db.get_guild_role(1), 99)


class TestInit(Base):
    def test_is_idempotent(self):
        db.init()
        db.init()

    def test_does_not_wipe_existing_rows(self):
        db.set_guild_role(1, 99)
        db.init()
        self.assertEqual(db.get_guild_role(1), 99)


if __name__ == "__main__":
    unittest.main(verbosity=2)
