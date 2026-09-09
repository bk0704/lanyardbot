import string

import utils.pending as pe
from utils.config import ALLOWED_DOMAIN
from utils.pending import clear_pending

#: Re-exported so callers and tests that read ``validate.DOMAIN`` keep working.
DOMAIN = ALLOWED_DOMAIN

#: The bare hostname. Compared exactly, so a leading '@' on ALLOWED_DOMAIN is no
#: longer what keeps look-alike domains out: removeprefix is a no-op without it
#: and the comparison stays exact either way.
ALLOWED_HOST = DOMAIN.removeprefix('@')

#: Characters that would let one string carry two recipients, smuggle a display
#: name, or inject headers if the transport is ever swapped for raw SMTP. Resend
#: is a JSON API today, so that last one is latent rather than live -- which is
#: exactly why it is worth blocking at the boundary now.
_FORBIDDEN = frozenset('\r\n\t ,;<>"()[]\x5c')  # \x5c is a backslash

#: Deliberately narrower than RFC 5322: institutional addresses do not need the
#: full grammar. Add characters here if real addresses are ever rejected -- an
#: apostrophe, for instance, if the college issues o'brien@ style addresses.
_LOCAL_ALLOWED = frozenset(string.ascii_lowercase + string.digits + '._%+-')

MAX_EMAIL_LENGTH = 254  # RFC 5321 total
MAX_LOCAL_LENGTH = 64   # RFC 5321 local part


def is_valid_email(email):
    """True only for a single, well-formed address on the configured domain.

    Parses rather than suffix-matches. The old ``endswith`` check constrained
    only the tail of the string, so anything at all could precede the domain --
    including a second address, interior whitespace, or an empty local part.

    ``.strip()`` runs first so a non-string argument still raises AttributeError
    rather than being silently rejected.
    """
    email = email.strip().lower()
    if not email or len(email) > MAX_EMAIL_LENGTH:
        return False
    if not _FORBIDDEN.isdisjoint(email):
        return False
    if email.count('@') != 1:
        return False
    local, _, domain = email.partition('@')
    if not local or len(local) > MAX_LOCAL_LENGTH:
        return False
    if not _LOCAL_ALLOWED.issuperset(local):
        return False
    return domain == ALLOWED_HOST


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
