from datetime import timedelta, timezone

#: Wrong guesses allowed per issued code before the code is discarded. Six
#: digits is only 10**6, so an unbounded retry loop makes the code guessable;
#: the cap is what turns the length into a real constraint.
DEFAULT_MAX_ATTEMPTS = 5


class PendingStore:
    def __init__(self, ttl_minutes=15, max_attempts=DEFAULT_MAX_ATTEMPTS):
        self._entries = {}
        self._ttl = timedelta(minutes=ttl_minutes)
        self._max_attempts = max_attempts
        self._last_sweep = None

    def save(self, user_id, code, now):
        if now.tzinfo is None or now.tzinfo.utcoffset(now) is None:
            raise ValueError('now must be timezone-aware; '
                             'use datetime.now(timezone.utc)')
        now = now.astimezone(timezone.utc)
        self._maybe_sweep(now)
        # 'attempts' is reset here rather than carried over, so re-requesting a
        # code deliberately grants a fresh budget.
        self._entries[user_id] = {'code': code,
                                  'expiry': now + self._ttl,
                                  'attempts': 0}

    def _maybe_sweep(self, now):
        """Drop every expired entry, at most once per TTL.

        Expiry is otherwise only enforced on the redemption path, so a user who
        requests a code and never submits it leaves a plaintext code resident
        until the process restarts. This bounds the store by users with a code
        in flight rather than by everyone who ever started verifying, and keeps
        dead secrets from lingering in memory.
        """
        if self._last_sweep is None:
            self._last_sweep = now
            return
        if now - self._last_sweep < self._ttl:
            return
        expired = [uid for uid, entry in self._entries.items() if now > entry['expiry']]
        for user_id in expired:
            del self._entries[user_id]
        self._last_sweep = now

    def get(self, user_id):
        return self._entries.get(user_id)

    def register_failure(self, user_id):
        """Record a wrong guess and return how many attempts remain.

        Returns 0 once the cap is reached, discarding the entry so the code
        cannot be guessed any further. Also returns 0 when there is no entry to
        charge, so callers can treat 0 uniformly as "no attempts left".

        The cap lives here rather than in the caller because this class already
        owns the entry's shape and lifetime.
        """
        entry = self._entries.get(user_id)
        if entry is None:
            return 0
        entry['attempts'] += 1
        if entry['attempts'] >= self._max_attempts:
            self.clear(user_id)
            return 0
        return self._max_attempts - entry['attempts']

    def clear(self, user_id):
        self._entries.pop(user_id, None)