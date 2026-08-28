import os

from dotenv import load_dotenv
import utils.pending as pe
from utils.pending import clear_pending

load_dotenv()
DOMAIN = os.getenv('ALLOWED_DOMAIN')

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
    if submitted != _pending['code']: return 'wrong'
    clear_pending(user_id)
    return 'ok'
