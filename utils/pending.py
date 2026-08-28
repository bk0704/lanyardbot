from pending_store import PendingStore

_store = PendingStore()

def save_pending(user_id, code, now):
    _store.save(user_id, code, now)

def get_pending(user_id):
    return _store.get(user_id)

def clear_pending(user_id):
    _store.clear(user_id)