from datetime import timedelta, timezone

class PendingStore:
    def __init__(self, ttl_minutes=15):
        self._entries = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def save(self, user_id, code, now):
        if now.tzinfo is None or now.tzinfo.utcoffset(now) is None:
            raise ValueError('now must be timezone-aware; '
                             'use datetime.now(timezone.utc)')
        now = now.astimezone(timezone.utc)
        self._entries[user_id] = {'code': code,
                                  'expiry': now + self._ttl}

    def get(self, user_id):
        return self._entries.get(user_id)

    def clear(self, user_id):
        self._entries.pop(user_id, None)