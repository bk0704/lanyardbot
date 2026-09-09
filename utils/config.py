"""Central configuration for LanyardBot.

This is the single place ``.env`` is loaded and the single place environment
variables are read. Importing this module validates the entire configuration up
front and exits with a readable summary if anything is missing or malformed.

That ordering matters. ``utils.mailer`` reads ``RESEND_API_KEY`` with a bare
subscript at import time, so a missing variable would otherwise surface as an
opaque ``KeyError`` during cog loading -- after Railway has already burned its
restart budget. Worse, an *empty* ``ALLOWED_DOMAIN`` makes the domain check
``email.endswith('')``, which accepts every address on earth. Both fail loudly
here instead.

Import this module before anything else that needs configuration.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

#: Every variable the bot needs to start. Add ``EMAIL_PEPPER`` here when the
#: verified-user table lands -- it must never be absent once rows exist.
REQUIRED = (
    'DISCORD_TOKEN',
    'RESEND_API_KEY',
    'EMAIL_FROM',
    'ALLOWED_DOMAIN',
    'DATABASE_URL',
)


def validate(env):
    """Return a list of human-readable configuration problems.

    An empty list means the configuration is usable. All problems are collected
    rather than raising on the first, so one deploy cycle surfaces every issue.

    Error strings never include the value of a secret. ``DISCORD_TOKEN``,
    ``RESEND_API_KEY`` and ``DATABASE_URL`` are only ever named, never echoed,
    because these messages land in Railway's log stream.
    """
    errors = []

    for name in REQUIRED:
        value = env.get(name)
        if value is None or not value.strip():
            errors.append(f'{name} is missing or empty')

    domain = (env.get('ALLOWED_DOMAIN') or '').strip()
    if domain:
        if not domain.startswith('@'):
            errors.append(
                f"ALLOWED_DOMAIN must start with '@' (got {domain!r}) -- without "
                "it the domain check also accepts look-alike domains such as "
                "'evil' + the configured suffix"
            )
        elif '.' not in domain[1:]:
            errors.append(
                f'ALLOWED_DOMAIN does not look like a domain (got {domain!r})'
            )

    database_url = (env.get('DATABASE_URL') or '').strip()
    if database_url and not database_url.startswith(('postgres://', 'postgresql://')):
        errors.append(
            'DATABASE_URL must be a postgres:// or postgresql:// DSN '
            '(value not shown -- it contains credentials)'
        )

    email_from = (env.get('EMAIL_FROM') or '').strip()
    if email_from and '@' not in email_from:
        errors.append(f'EMAIL_FROM does not contain an address (got {email_from!r})')

    return errors


def require(env=None):
    """Validate ``env`` and abort the process if it is unusable."""
    env = os.environ if env is None else env
    errors = validate(env)
    if not errors:
        return
    sys.stderr.write('LanyardBot cannot start -- configuration problems:\n')
    for error in errors:
        sys.stderr.write(f'  - {error}\n')
    sys.stderr.write(
        '\nSet these in .env for local runs, or in the Railway service variables.\n'
    )
    raise SystemExit(1)


require()

DISCORD_TOKEN = os.environ['DISCORD_TOKEN'].strip()
RESEND_API_KEY = os.environ['RESEND_API_KEY'].strip()
EMAIL_FROM = os.environ['EMAIL_FROM'].strip()
DATABASE_URL = os.environ['DATABASE_URL'].strip()

#: Lower-cased so the comparison in :mod:`utils.validate` cannot be defeated by
#: a stray capital in the deploy console.
ALLOWED_DOMAIN = os.environ['ALLOWED_DOMAIN'].strip().lower()
