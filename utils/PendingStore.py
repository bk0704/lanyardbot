from datetime import timedelta

class PendingStore:
    def __init__(self, ttl_minutes=15):
        self._entries = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def save(self, user_id, code, now):
        self._entries[user_id] = {'code': code,
                                  'expiry': now + self._ttl}

