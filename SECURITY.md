# Security Policy

LanyardBot gates access to Discord servers, so a flaw here can let someone into
a server they should not be in. Reports are taken seriously.

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Use GitHub's private reporting instead:
[Report a vulnerability](https://github.com/bk0704/lanyardbot/security/advisories/new).
That opens a private thread visible only to the maintainer.

Anything that lets someone obtain the verified role without controlling a
mailbox on the configured domain is in scope, as is anything that exposes a
one-time code, an email address, or a credential.

Please include what you did, what happened, and what you expected. A proof of
concept helps a lot. Test against your own server — never against someone
else's.

## What to expect

This is a solo, unpaid project, so I cannot promise a response time. I will
acknowledge your report when I see it and tell you whether I plan to fix it.
If you would like credit in the fix, say so and I will include it.

## Out of scope

- Anything requiring the Discord bot token, the Resend key, or database
  credentials to already be compromised
- Discord's own rate limits, or the deliverability of the mail provider
- Social engineering of server admins

## Running your own instance

If you deploy this yourself, you are responsible for your own secrets. Do not
commit a `.env` file, and set the environment variables through your host.
