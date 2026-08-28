# `utils`

Stateless helpers behind LanyardBot's `/verify` flow: domain validation, OTP
generation, and short-lived storage of pending codes. Nothing here imports
`discord` — every function takes plain values and returns plain values, so the
whole package is testable without a bot running.

## Modules

| Module | Responsibility |
| --- | --- |
| `validate.py` | Email domain check, and checking a submitted OTP |
| `generator.py` | Generating the 6-digit OTP |
| `pending.py` | Module-level API for the pending-OTP store |
| `pending_store.py` | `PendingStore` class — the actual storage |

---

## `validate.py`

### `is_valid_email(email) -> bool`

Returns `True` if `email` ends with the allowed domain. Input is stripped and
lowercased first, so `"  Student@SheridanCollege.CA "` passes.

This is a **domain check, not an address check** — `"@sheridancollege.ca"` on its
own returns `True`. Real validation is the code emailed to the address, so a
malformed local part simply never receives anything.

The domain comes from the `ALLOWED_DOMAIN` environment variable, read once at
import via `python-dotenv`. It must be lowercase, since the comparison happens
after `email` is lowercased.

### `check_code(user_id, submitted, now) -> str`

Checks a submitted OTP against the stored one. Returns exactly one of:

| Result | Meaning | Entry cleared? |
| --- | --- | --- |
| `'none'` | No pending code for this user | — |
| `'expired'` | Past the 15-minute window | yes |
| `'wrong'` | Code doesn't match | **no** — user can retry |
| `'ok'` | Match, within the window | yes |

Checks happen in that order, so an expired entry reports `'expired'` even if the
submitted code was also wrong. `submitted` is stripped, so trailing whitespace
from a pasted code is forgiven. `now` must be timezone-aware (see below).

`'wrong'` deliberately leaves the entry in place — that's what lets a user
mistype without having to request a whole new code. Note that this also means
there is currently **no attempt limit**; see Known limits.

---

## `generator.py`

### `generate_code() -> str`

Returns a 6-character string of digits, e.g. `"042317"`.

A **string, not an int**, so leading zeros survive. Uses `secrets`, not
`random` — these codes are a security boundary, and `random` is predictable
from observed output.

---

## `pending.py`

Thin module-level wrappers over one shared `PendingStore` instance, so the
modal that saves a code and the modal that checks it see the same data.

```python
save_pending(user_id, code, now)   # -> None, overwrites any existing entry
get_pending(user_id)               # -> {'code': str, 'expiry': datetime} | None
clear_pending(user_id)             # -> None, no error if nothing is stored
```

`get_pending` returns `None` for an unknown user — that's a normal outcome, not
an error, so callers should use an `if` rather than a `try`.

---

## `pending_store.py`

### `PendingStore(ttl_minutes=15)`

An in-memory dict of `user_id -> {'code', 'expiry'}`, with `.save()`, `.get()`,
and `.clear()` methods matching the wrappers above.

Instantiate it directly to get isolated state — that's what the tests do, and
it's the seam for swapping in a Redis- or SQLite-backed store later without
touching any call site.

`.save()` **raises `ValueError` on a naive datetime** and normalizes aware input
to UTC.

---

## The `now` convention

Every function taking a `now` expects a **timezone-aware UTC** datetime:

```python
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

Two reasons. Passing `now` in rather than calling the clock internally makes
expiry testable at fixed instants. And keeping it UTC avoids a DST bug: a local
timezone would give you one hour a year where codes live 75 minutes and another
where they die in 15.

A naive datetime raises `ValueError` in `save_pending` and `TypeError` in
`check_code`.

## Configuration

`ALLOWED_DOMAIN` in `.env`, lowercase, including the `@`:

```
ALLOWED_DOMAIN='@sheridancollege.ca'
```

## Typical flow

```python
from datetime import datetime, timezone
from utils.validate import is_valid_email, check_code
from utils.generator import generate_code
from utils.pending import save_pending

now = datetime.now(timezone.utc)

if is_valid_email(email):
    code = generate_code()
    save_pending(user_id, code, now)
    # ... email the code ...

result = check_code(user_id, submitted, datetime.now(timezone.utc))
if result == 'ok':
    ...  # assign the verified role
```

## Tests

```
python -m pytest tests
```

`tests/utils/` covers each module. Tests that touch pending state swap
`pending._store` for a fresh `PendingStore` via an autouse fixture, so no state
leaks between them.

## Known limits

- **Pending codes are in memory only.** A bot restart drops every unverified
  code; users just click Verify again.
- **Expired entries are never swept.** They're only cleared when checked, so a
  user who never submits leaves a dict entry behind until restart.
- **No attempt limit.** `'wrong'` keeps the entry, so a code can be guessed
  repeatedly within its 15-minute window.
