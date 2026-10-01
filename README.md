# SearchMirror — Open-source Google rank tracker

[![CI](https://github.com/databluedev/searchmirror/actions/workflows/ci.yml/badge.svg)](https://github.com/databluedev/searchmirror/actions/workflows/ci.yml)
[![Licence: AGPL v3](https://img.shields.io/badge/licence-AGPL--3.0-blue.svg)](LICENSE)

SearchMirror is an open-source, self-hosted Google rank tracker and AI visibility
monitor powered by the
[datablue.dev](https://www.datablue.dev/?utm_source=github&utm_medium=referral&utm_campaign=searchmirror&utm_content=readme)
SERP API. Track keyword positions by country, language, and device, compare
competitors, and explore brand mentions in AI responses using your own provider
keys.

Built for SEO practitioners, agencies, and developers who want to run their own
rank-tracking dashboard while using DataBlue for Google search results.

[Quick start](#quick-start) · [User guide](docs/USER-GUIDE.md) · [DataBlue integration](docs/DATABLUE-INTEGRATION.md)

## What you can do

- **Track Google keyword rankings:** follow position history for your projects
  with country, language, and desktop/mobile targeting.
- **Compare competitors:** review competitor rankings alongside your tracked
  keywords.
- **Explore AI visibility:** use Geo Citations to check brand mentions in AI
  responses with account-supplied AI keys. This is separate from Google ranking.
- **Plan content:** generate outlines and drafts with Content Planner and your
  chosen AI provider.
- **Keep control of your instance:** self-host the application and manage
  projects, reports, provider keys, and team access.

SearchMirror is AGPL-3.0 software. Live rank checks consume DataBlue credits;
AI features use separately configured provider keys and may incur provider
charges. Self-hosting does not make those API calls free.

> **Status: pre-1.0.** The local Docker stack and supported product paths are
> functional, but the project still carries a legacy Django 3.2 and MongoDB 4.4
> runtime. Treat the included Compose stack as a development environment, not a
> production deployment template.

## Supported scope

The current public surface is intentionally narrow:

- projects and tracked keywords
- rank dashboard and keyword history
- competitor tracking
- Geo Citations using account-supplied AI keys
- Content Planner using account-supplied AI keys
- reports, account settings, and team members with per-module roles

Keyword research, search volume, Content Gap, page audit, billing and the old
commercial vendor integrations are not part of this application and their code
has been removed. Google Search Console and Analytics code is retained but
parked until a proper server-side OAuth flow is provided; it is not advertised
as ready.

## Bring your own keys

**Need a DataBlue API key?** Sign up at
[datablue.dev](https://www.datablue.dev/signup?utm_source=github&utm_medium=referral&utm_campaign=searchmirror&utm_content=readme_api_key),
then save your key in SearchMirror under **Settings -> API Keys**. See the
[integration guide](docs/DATABLUE-INTEGRATION.md) for setup and provider behavior.

Live rank checks require DataBlue. Each account can save its own DataBlue key
under **Settings -> API Keys**. Keys are encrypted at rest with
`SERP_KEY_SECRET` and are not returned in clear text.

An operator may set `DATABLUE_API_KEY` and explicitly enable
`ALLOW_INSTANCE_FALLBACK=true` for a single-operator install. Fallback is off by
default so one account cannot silently spend the instance owner's credits.

Geo Citations and Content Planner optionally use OpenAI, Anthropic, Perplexity,
or Gemini. Accounts configure a provider key and model in Settings; both
features share the same provider router. No Hugging Face or DataForSEO account
is required.

## Quick start

Requirements: Docker with the Compose plugin.

```bash
git clone https://github.com/databluedev/searchmirror.git
cd searchmirror
cp .env.example .env
docker compose up -d --build
```

The backend automatically applies migrations and runs the idempotent local
seed. Sign in at [http://127.0.0.1:3001](http://127.0.0.1:3001) with:

| Field | Local value |
|---|---|
| Email | `admin@local.test` |
| Password | `LocalDev12345` |

These credentials are for the local seed only. Replace the placeholder Django,
engine, encryption, and scheduler secrets before exposing an instance.

| Service | Address | Purpose |
|---|---|---|
| `tracker-app` | http://127.0.0.1:3001 | React application |
| `tracker-backend` | http://127.0.0.1:8000 | Django API |
| `tracker-engine` | http://127.0.0.1:8001 | internal ranking engine |
| `tracker-scheduler` | - | queues the daily 01:00 rank runs |
| `tracker-mongo` | 127.0.0.1:27017 | MongoDB |

> Every port is published on `127.0.0.1` only -- the stack is not reachable
> from the local network, and there is no IPv6 listener to half-answer a
> `localhost` connection. `localhost` and `127.0.0.1` both work; the docs
> use the explicit IPv4 form because that is what the tests and
> `CORS_ALLOWED_ORIGINS` are written against.

The `tracker-*` container names are retained for volume and deployment
compatibility; the public product name is SearchMirror.

### Run real rankings

Saving a DataBlue key only configures the account. The following command
performs live provider requests and spends DataBlue credits:

```bash
docker compose exec engine python rank_local.py
```

The command prints the estimated request count before starting. It is never run
automatically by the test suite.

### Production-bundle smoke build

The main app can also be compiled and served by nginx on port 4001:

```bash
docker compose --profile prod up -d --build app-prod
```

This validates the frontend bundle; it does not turn the development Django
servers or MongoDB image into a hardened production deployment.

### Marketing site

`landing/` is an independent Vite application:

```bash
cd landing
pnpm install
pnpm dev      # http://localhost:5180
pnpm build    # production bundle in landing/dist
```

Its outbound links live in `landing/src/lib/site.ts`. `REPO_URL` points to this
repository; the licence, docs, and issues links are derived from it.

## Configuration

Copy [`.env.example`](.env.example) to `.env`. The example documents every
supported setting and contains only local placeholders.

The important security settings are:

- `DJANGO_SECRET_KEY` and `ENGINE_SECRET_KEY`: signing secrets; production mode
  refuses known placeholders and short values.
- `SERP_KEY_SECRET`: encrypts saved DataBlue keys. Rotating it makes existing
  saved keys unreadable.
- `ALLOW_INSTANCE_FALLBACK`: must be explicitly enabled before the shared
  `DATABLUE_API_KEY` can be used.
- `CRON_TOKEN` and `ENGINE_TRIGGER_TOKEN`: protect scheduler and on-demand
  engine entry points. Blank values leave those entry points disabled.
- `CORS_ALLOWED_ORIGINS`, `DJANGO_ALLOWED_HOSTS`, `APP_SITE_URL`, and
  `APP_API_URL`: set these to the deployment's actual origins.

AI provider environment variables are optional instance fallbacks. A hosted or
multi-user deployment should leave them blank and use per-account keys.

## Tests and builds

With the local stack running:

```bash
python -m pytest tests -q
docker compose exec -T backend python manage.py check
docker compose exec -T engine python manage.py check
docker compose exec -T app npm run build
cd landing && pnpm build
```

The tests cover authentication, provider routing, production configuration,
supported routes, and Docker-backed integration behavior. Browser verification
should avoid clicking Rank, Refresh, or Generate unless spending configured
provider credits is intentional.

## Project layout

| Path | Purpose |
|---|---|
| `app/` | React 18 + Vite product UI |
| `landing/` | React 18 + Vite marketing site |
| `backend/` | Django API, accounts, projects, reports, and orchestration |
| `engine/` | Django ranking engine and DataBlue integration |
| `shared/` | code shared by both Django services |
| `brand/` | the mark: source of truth for every favicon, logo, and wordmark |
| `docker/` | service Dockerfiles and nginx configuration |
| `tests/` | regression and Docker-backed integration tests |

The backend and engine are separate Django applications sharing MongoDB. A
future runtime upgrade should migrate Django/djongo and MongoDB together rather
than changing one layer in isolation.

## Documentation

| Document | What it is for |
|---|---|
| [`docs/USER-GUIDE.md`](docs/USER-GUIDE.md) | Using a running instance: projects, keywords, reading the dashboard, and what costs money |
| [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) | Every environment variable, what it does, and what breaks without it |
| [`SECURITY.md`](SECURITY.md) | Reporting a vulnerability, and what is in scope |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Start here to work on the code: running the stack, where things live, conventions, how to submit a change |
| [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) | What is expected of everyone taking part, and how to report a problem |
| [`CHANGELOG.md`](CHANGELOG.md) | What changed in each release, and the known limitations of the current one |
| [`docs/TESTING.md`](docs/TESTING.md) | The test suite — how it runs, the two kinds of test, what is covered and what is not |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Running an instance for real: the production overlay, TLS, secrets, backups |
| [`docs/DESIGN.md`](docs/DESIGN.md) | The design contract. Governs every pixel; read before any UI change |
| [`docs/PRODUCT-DESIGN.md`](docs/PRODUCT-DESIGN.md) | Navigation and information architecture |
| [`docs/ORCHESTRATION.md`](docs/ORCHESTRATION.md) | How daily ranking is scheduled across projects. Read before changing `engine/project/machine/` |
| [`docs/DATABLUE-INTEGRATION.md`](docs/DATABLUE-INTEGRATION.md) | How the SERP provider is called and what it returns |
| [`docs/DATABLUE-FINDINGS-2026-09-05.md`](docs/DATABLUE-FINDINGS-2026-09-05.md) | Measured provider behaviour, including fields that are always empty |
| [`docs/SHIPPED-SURFACE.md`](docs/SHIPPED-SURFACE.md) | What ships, what is parked and why. Paired with `tests/test_shipped_surface.py` |

## Maintainer

Built and maintained by **Sheik Mohammed Ali M**
([@sheik-md-ali](https://github.com/sheik-md-ali)) —
<mdali.sheik1613@gmail.com>.

Bug reports and feature requests belong in the issue tracker; questions are
welcome by email. Security issues go through [`SECURITY.md`](SECURITY.md), not
a public issue. Contributions are welcome — start with
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

SearchMirror is licensed under the [GNU Affero General Public License v3.0](LICENSE).
If you modify it and provide the modified software as a network service, the
AGPL requires that service's users be offered the corresponding source code.

Copyright (C) 2026 Sheik Mohammed Ali M and SearchMirror contributors.
