# Security policy

SearchMirror is self-hosted software that holds provider API keys for the
people who run it. A vulnerability here can spend someone's money or expose
their credentials, so security reports are taken seriously and answered.

## Reporting a vulnerability

**Do not open a public issue.** Report privately through GitHub's
[Report a vulnerability](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
form on this repository, or email <mdali.sheik1613@gmail.com>.

Useful reports contain: what an attacker can do, the smallest steps that
reproduce it, and the version or commit you tested. A working exploit is not
required and never necessary — a clear description of the flaw is enough.

You will get an acknowledgement within a few days. If a fix is needed, the
advisory is published once it ships, and you are credited unless you ask not to
be.

## Scope

**In scope** — anything in this repository: the Django API (`backend/`), the
ranking engine (`engine/`), the React application (`app/`), the shared modules
(`shared/`), and the Docker configuration.

Particularly interesting:

- **Cross-account access.** Ownership is enforced in middleware
  (`backend/account/ownership.py`), not per view, because 56 views once
  identified the account from an unvalidated `userid` in the request body. Any
  path that reads another account's data is a serious bug.
- **Credential exposure.** Provider keys are encrypted at rest with an
  authenticated envelope (`shared/keycrypto.py`) keyed by `SERP_KEY_SECRET`,
  and API responses mask them. A key appearing in a response, a log, an error
  page or an export is a serious bug.
- **Spending someone else's key.** An account with no key of its own must not
  fall back to the instance key unless the operator set
  `ALLOW_INSTANCE_FALLBACK=true`. Any path that bills the operator silently is
  a serious bug.
- **Scheduler and engine endpoints.** These are gated by `CRON_TOKEN` and
  `ENGINE_TRIGGER_TOKEN`, compared with `hmac.compare_digest` and failing
  closed. Reaching them without a token is a serious bug.
- **Team member privilege.** A member's token authenticates *as the owning
  account* while `request.auth` stays the `TeamAccount`. Anything that lets a
  member act outside their granted modules is a serious bug.

**Out of scope** — issues that require an operator to have already misconfigured
the instance in a way the documentation warns against:

- Running with `DJANGO_DEBUG=True` in production. `backend/tracker/settings.py`
  refuses to start with the placeholder secret key when DEBUG is off; running
  with DEBUG on is documented as development-only.
- Using the committed `.env.example` values (including its published MongoDB
  password) outside local development. `docs/DEPLOYMENT.md` and
  `.env.production.example` cover this.
- Exposing MongoDB, the engine (`:8001`) or the Django admin to a network. All
  three bind to loopback by default and the production overlay does not publish
  the database at all.
- Denial of service from a self-hosted instance's own configured provider keys.

## Supported versions

Pre-1.0: only the latest `main` is supported. There are no backported fixes.
If you run a fork, rebase before reporting.

## What this software does not protect you from

Self-hosting means the operator owns the perimeter. SearchMirror does not
provide TLS termination, secret management, backups, log rotation or host
hardening, and `docs/DEPLOYMENT.md` says so explicitly rather than implying
the Compose stack is a finished deployment. An instance published to the
internet without a reverse proxy in front of it is not a vulnerability in this
project.
