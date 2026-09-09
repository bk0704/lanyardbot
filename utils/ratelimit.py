"""In-memory sliding-window rate limiting for outbound verification codes.

Issuing a code is the expensive, abusable half of verification: it sends real
mail from a verified sending domain to an address the requester chose, and it
hands the requester a fresh budget of guesses. Without a limit here, the attempt
cap in :mod:`utils.pending_store` is worth little -- an attacker simply requests
another code.

Timestamps are supplied by the caller rather than read from the clock, matching
:meth:`utils.pending_store.PendingStore.save`, so the whole module is testable
without sleeping.

State is per-process and is lost on restart. That is acceptable: an attacker
cannot force a restart, and the durable half of the defence is the attempt cap.
"""

from collections import deque
from datetime import timedelta, timezone


def _as_utc(now):
    if now.tzinfo is None or now.tzinfo.utcoffset(now) is None:
        raise ValueError('now must be timezone-aware; '
                         'use datetime.now(timezone.utc)')
    return now.astimezone(timezone.utc)


class RateLimiter:
    """Allows ``limit`` events per ``per_minutes`` window, per key."""

    def __init__(self, limit, per_minutes):
        self._limit = limit
        self._window = timedelta(minutes=per_minutes)
        self._hits = {}
        self._last_sweep = None

    def _prune(self, key, now):
        """Drop timestamps that have aged out; return the live deque or None.

        Only touches ``key``. A key nobody uses again is not reached here at
        all, which is what :meth:`_maybe_sweep` exists to handle.
        """
        hits = self._hits.get(key)
        if hits is None:
            return None
        cutoff = now - self._window
        while hits and hits[0] <= cutoff:
            hits.popleft()
        if not hits:
            del self._hits[key]
            return None
        return hits

    def retry_after(self, key, now):
        """Seconds to wait before this key is allowed, or None if allowed now."""
        now = _as_utc(now)
        hits = self._prune(key, now)
        if hits is None or len(hits) < self._limit:
            return None
        return (hits[0] + self._window - now).total_seconds()

    def _maybe_sweep(self, now):
        """Drop every fully-expired key, at most once per window.

        _prune only cleans the key it is handed, so a user or address that
        never comes back leaves its deque behind forever. Sweeping on a timer
        bounds the dict by *active* keys rather than by every key ever seen,
        without a background task and without evicting anything still live --
        an LRU bound would drop keys that are still inside their window, which
        turns a memory issue into a limit an attacker can flush deliberately.
        """
        if self._last_sweep is None:
            self._last_sweep = now
            return
        if now - self._last_sweep < self._window:
            return
        cutoff = now - self._window
        # A deque is append-ordered, so if the newest entry has aged out they
        # all have.
        expired = [k for k, hits in self._hits.items() if not hits or hits[-1] <= cutoff]
        for key in expired:
            del self._hits[key]
        self._last_sweep = now

    def record(self, key, now):
        """Charge one event against ``key``."""
        now = _as_utc(now)
        self._maybe_sweep(now)
        self._prune(key, now)
        self._hits.setdefault(key, deque()).append(now)


#: At most one code a minute per Discord user -- stops rapid-fire clicking.
USER_COOLDOWN = RateLimiter(limit=1, per_minutes=1)

#: At most five codes an hour per Discord user -- stops sustained grinding.
USER_HOURLY = RateLimiter(limit=5, per_minutes=60)

#: At most three codes an hour to any one address, no matter who asked. This is
#: the limit that stops the bot being used to flood one person's inbox.
EMAIL_HOURLY = RateLimiter(limit=3, per_minutes=60)


def retry_after_for_send(user_id, email, now):
    """Longest wait across every limit, or None if the send may proceed.

    Deliberately separate from :func:`record_send`: all three limits must be
    consulted before any of them is charged, or a request rejected by the
    address limit would still have consumed the requester's own quota.
    """
    waits = [
        USER_COOLDOWN.retry_after(user_id, now),
        USER_HOURLY.retry_after(user_id, now),
        EMAIL_HOURLY.retry_after(email, now),
    ]
    waits = [wait for wait in waits if wait is not None]
    return max(waits) if waits else None


def record_send(user_id, email, now):
    """Charge a send against every limit."""
    USER_COOLDOWN.record(user_id, now)
    USER_HOURLY.record(user_id, now)
    EMAIL_HOURLY.record(email, now)


def describe_wait(seconds):
    """Render a wait as a short phrase for a user-facing message."""
    seconds = max(1, int(seconds + 0.5))
    if seconds < 60:
        return f'{seconds} second{"s" if seconds != 1 else ""}'
    minutes = (seconds + 59) // 60
    return f'{minutes} minute{"s" if minutes != 1 else ""}'
