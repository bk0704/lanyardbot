"""SQLite storage for LanyardBot: guild config, pending OTPs, verified users."""

import contextlib
import hashlib
import hmac
import os
import pathlib
import sqlite3
import time

from dotenv import load_dotenv

load_dotenv()

# Bracket, not .get() -- a missing pepper should crash at import, not silently
# hash against None and corrupt every row written this session.
PEPPER = os.environ["EMAIL_PEPPER"].encode()

# Overridable so tests can point at a throwaway file, and so a deploy host
# can put the database on a mounted volume.
DB_PATH = pathlib.Path(
    os.environ.get("LANYARD_DB", pathlib.Path(__file__).parent / "lanyard.db")
)

conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")

SCHEMA = """
CREATE TABLE IF NOT EXISTS guild_config (
    guild_id INTEGER PRIMARY KEY,
    role_id  INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS pending (
    discord_id INTEGER PRIMARY KEY,
    email_hash TEXT    NOT NULL,
    code_hash  TEXT    NOT NULL,
    expires_at INTEGER NOT NULL,
    attempts   INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS verified (
    discord_id  INTEGER PRIMARY KEY,
    email_hash  TEXT    NOT NULL UNIQUE,
    verified_at INTEGER NOT NULL
);
"""


# --- setup -----------------------------------------------------------------

def init() -> None:
    """Create all three tables if absent. Idempotent; call from setup_hook."""
    conn.executescript(SCHEMA)


@contextlib.contextmanager
def _tx():
    """A real transaction.

    `with conn:` is a no-op under isolation_level=None, since autocommit means
    there is never an implicit transaction for it to commit. Use this instead
    whenever two statements must land together or not at all.
    """
    conn.execute("BEGIN")
    try:
        yield conn
    except Exception:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")


# --- hashing ---------------------------------------------------------------

def _h(value: str) -> str:
    return hmac.new(PEPPER, value.encode(), hashlib.sha256).hexdigest()


def email_key(email: str) -> str:
    """Peppered HMAC of the normalized (stripped, lowercased) address."""
    return _h(email.strip().lower())


def code_key(code: str) -> str:
    """Peppered HMAC of the OTP. Same pepper as email_key."""
    return _h(code.strip())


# --- guild config ----------------------------------------------------------

def set_guild_role(guild_id: int, role_id: int) -> None:
    """Set the verified role for a guild. Upsert: re-running /verify repoints it."""
    conn.execute(
        """
        INSERT INTO guild_config (guild_id, role_id) VALUES (?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET role_id = excluded.role_id
        """,
        (guild_id, role_id),
    )


def get_guild_role(guild_id: int) -> int | None:
    """Role id for a guild, or None if /verify was never run there."""
    row = conn.execute(
        "SELECT role_id FROM guild_config WHERE guild_id = ?", (guild_id,)
    ).fetchone()
    return row["role_id"] if row else None


# --- pending OTPs ----------------------------------------------------------

def create_pending(
    discord_id: int, email_hash: str, code_hash: str, expires_at: int
) -> None:
    """Store a pending OTP. Upsert on discord_id, resetting attempts to 0."""
    conn.execute(
        """
        INSERT INTO pending (discord_id, email_hash, code_hash, expires_at, attempts)
        VALUES (?, ?, ?, ?, 0)
        ON CONFLICT(discord_id) DO UPDATE SET
            email_hash = excluded.email_hash,
            code_hash  = excluded.code_hash,
            expires_at = excluded.expires_at,
            attempts   = 0
        """,
        (discord_id, email_hash, code_hash, expires_at),
    )


def get_pending(discord_id: int) -> sqlite3.Row | None:
    """Unexpired pending row, or None. Expiry is filtered in the WHERE clause."""
    return conn.execute(
        "SELECT * FROM pending WHERE discord_id = ? AND expires_at > ?",
        (discord_id, int(time.time())),
    ).fetchone()


def bump_attempts(discord_id: int) -> int:
    """Increment the failed-attempt counter and return the new value."""
    row = conn.execute(
        "UPDATE pending SET attempts = attempts + 1 WHERE discord_id = ? "
        "RETURNING attempts",
        (discord_id,),
    ).fetchone()
    return row["attempts"] if row else 0


def clear_pending(discord_id: int) -> None:
    """Drop a user's pending OTP."""
    conn.execute("DELETE FROM pending WHERE discord_id = ?", (discord_id,))


# --- verified users --------------------------------------------------------

def is_email_used(email_hash: str) -> bool:
    """True if this address has already verified some account."""
    return conn.execute(
        "SELECT 1 FROM verified WHERE email_hash = ?", (email_hash,)
    ).fetchone() is not None


def mark_verified(discord_id: int, email_hash: str) -> bool:
    """Record the verification and clear the pending row, atomically.

    Returns False if the address was already used (IntegrityError).
    """
    try:
        with _tx():
            # ON CONFLICT(discord_id) handles the same user verifying again --
            # re-running the flow after losing the role updates their row
            # instead of raising. It deliberately does NOT cover the
            # email_hash UNIQUE violation, so a second person claiming an
            # address still raises and returns False.
            conn.execute(
                """
                INSERT INTO verified (discord_id, email_hash, verified_at)
                VALUES (?, ?, ?)
                ON CONFLICT(discord_id) DO UPDATE SET
                    email_hash  = excluded.email_hash,
                    verified_at = excluded.verified_at
                """,
                (discord_id, email_hash, int(time.time())),
            )
            conn.execute("DELETE FROM pending WHERE discord_id = ?", (discord_id,))
        return True
    except sqlite3.IntegrityError:
        # email_hash belongs to someone else. The ROLLBACK inside _tx already
        # undid the insert, so nothing partial survives.
        return False


# --- maintenance -----------------------------------------------------------

def purge_expired() -> int:
    """Delete expired pending rows. Returns the number removed."""
    cur = conn.execute(
        "DELETE FROM pending WHERE expires_at <= ?", (int(time.time()),)
    )
    return cur.rowcount
