# Contributing to LanyardBot

Thanks for taking a look. This is a small project, so the bar is mostly "does
it work and is it clear."

## What you need to run it

LanyardBot talks to three external services, and you need your own credentials
for each. None of them cost anything at the scale this needs.

| What | Where to get it |
| --- | --- |
| A Discord bot token | [Discord Developer Portal](https://discord.com/developers/applications) — create an application, add a bot, copy the token |
| A Resend API key | [resend.com](https://resend.com) — the free tier is enough, but you can only send to your own verified address until you add a domain |
| A Postgres database | [Neon](https://neon.tech) has a free tier; any Postgres works |

You also need a Discord server you control to test in. **Do not test against a
real community server.**

## Setup

```bash
git clone https://github.com/bk0704/lanyardbot.git
cd lanyardbot
python -m venv venv
venv/Scripts/activate        # Windows;  source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
```

Create a `.env` in the project root with all five variables:

```
DISCORD_TOKEN='your-bot-token'
RESEND_API_KEY='re_...'
EMAIL_FROM='noreply@yourdomain.com'
ALLOWED_DOMAIN='@yourschool.edu'
DATABASE_URL='postgresql://user:pass@host/db?sslmode=require'
```

All five are required and validated at startup — the bot refuses to start with
a clear error if any is missing or blank. `ALLOWED_DOMAIN` must keep its
leading `@`.

The database needs one table:

```sql
CREATE TABLE guild_config (
    guild_id BIGINT PRIMARY KEY,
    role_id  BIGINT NOT NULL
);
```

Then:

```bash
python bot.py
```

Invite the bot with the **Manage Roles** permission, and make sure its role sits
**above** the role it will be granting, or every assignment fails.

Slash commands sync globally on startup and can take up to an hour to appear.
While developing, sync to your test guild instead for instant availability.

## Before you open a pull request

- `python -m compileall bot.py lanyard.py utils modals views commands` passes
- The bot starts and the full flow works in your test server: `/verify`, click
  Verify, enter an address, receive a code, enter it, get the role
- Restart the bot and click a stale button — it should give a real message, not
  "This interaction failed"

CI runs a build and import check on every PR.

## Things worth knowing

- **Verification is security-sensitive.** Anything touching code generation,
  code checking, rate limiting or the domain check deserves extra care. If a
  change relaxes one of those, say so in the PR and explain why.
- **Never log an address or a one-time code.** Logs go to the host's log stream.
- **Fail closed.** Verification paths grant a role; if a state is unrecognised,
  refuse rather than continue.
- Times are timezone-aware UTC throughout. `datetime.now(timezone.utc)`, never
  naive datetimes — the pending store rejects them outright.

## Reporting a security problem

Don't open a public issue. See [SECURITY.md](SECURITY.md).
