from datetime import timedelta

class PendingStore:
    def __init__(self, ttl_minutes=15):
        self._entries = {}
        self._ttl = timedelta(minutes=ttl_minutes)

    def save(self, user_id, code, now):
        self._entries[user_id] = {'code': code,
                                  'expiry': now + self._ttl}

    def get(self, user_id):
        return self._entries.get(user_id)

    def clear(self, user_id):
        self._entries.pop(user_id, None)