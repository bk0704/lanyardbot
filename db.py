"""SQLite storage for LanyardBot: guild config, pending OTPs, verified users."""

import sqlite3


# --- setup -----------------------------------------------------------------

def init() -> None:
    """Create all three tables if absent. Idempotent; call from setup_hook."""
    ...


# --- hashing ---------------------------------------------------------------

def email_key(email: str) -> str:
    """Peppered HMAC of the normalized (stripped, lowercased) address."""
    ...


def code_key(code: str) -> str:
    """Peppered HMAC of the OTP. Same pepper as email_key."""
    ...


# --- guild config ----------------------------------------------------------

def set_guild_role(guild_id: int, role_id: int) -> None:
    """Set the verified role for a guild. Upsert: re-running /verify repoints it."""
    ...


def get_guild_role(guild_id: int) -> int | None:
    """Role id for a guild, or None if /verify was never run there."""
    ...


# --- pending OTPs ----------------------------------------------------------

def create_pending(
    discord_id: int, email_hash: str, code_hash: str, expires_at: int
) -> None:
    """Store a pending OTP. Upsert on discord_id, resetting attempts to 0."""
    ...


def get_pending(discord_id: int) -> sqlite3.Row | None:
    """Unexpired pending row, or None. Expiry is filtered in the WHERE clause."""
    ...


def bump_attempts(discord_id: int) -> int:
    """Increment the failed-attempt counter and return the new value."""
    ...


def clear_pending(discord_id: int) -> None:
    """Drop a user's pending OTP."""
    ...


# --- verified users --------------------------------------------------------

def is_email_used(email_hash: str) -> bool:
    """True if this address has already verified some account."""
    ...


def mark_verified(discord_id: int, email_hash: str) -> bool:
    """Record the verification and clear the pending row, atomically.

    Returns False if the address was already used (IntegrityError).
    """
    ...


# --- maintenance -----------------------------------------------------------

def purge_expired() -> int:
    """Delete expired pending rows. Returns the number removed."""
    ...
