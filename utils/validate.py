import utils.pending as pe
from utils.config import ALLOWED_DOMAIN
from utils.pending import clear_pending

#: Re-exported so callers and tests that read ``validate.DOMAIN`` keep working.
DOMAIN = ALLOWED_DOMAIN

def is_valid_email(email):
    email = email.strip().lower()
    if email.endswith(DOMAIN): return True
    return False

def check_code(user_id, submitted, now):
    _pending = pe.get_pending(user_id)
    if _pending is None: return 'none'

    submitted = submitted.strip()

    if now > _pending['expiry']:
        clear_pending(user_id)
        return 'expired'
    if submitted != _pending['code']:
        # register_failure discards the entry once the cap is reached, so a
        # 'locked' result also means the code is already gone.
        remaining = pe.register_failure(user_id)
        return 'wrong' if remaining > 0 else 'locked'
    clear_pending(user_id)
    return 'ok'
