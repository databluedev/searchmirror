# Changelog

All notable changes to SearchMirror are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project aims to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
from 1.0.0 onward. **Until then the project is pre-1.0 and breaking changes may
land in any release** — pin a commit if you depend on current behaviour.

## [Unreleased]

Nothing yet.

## [0.1.0] — 2026-09-05

First public release. SearchMirror is an open-source, self-hosted rank tracker
and AI-visibility monitor built on the [DataBlue](https://datablue.dev) SERP
API, adapted from a commercial product and narrowed to what it can honestly
support.

### Added

- **Projects and keywords** — per-project country, language, device and search
  depth, with per-keyword overrides.
- **Rank dashboard and history** — visibility score, movement, and a history
  chart per keyword.
- **Competitors** — track rival domains against the same keywords.
- **Geo Citations** — how often AI assistants mention a brand, and what they
  cite. Uses the account's own provider key.
- **Content Planner** — AI article outlines and drafts, generated in the
  background so a slow provider cannot hold a request open.
- **Reports** — PDF and CSV export.
- **Teams** — members with per-module permissions, signing in with their own
  credentials.
- **Bring-your-own-key** — each account stores its own DataBlue key, encrypted
  at rest. An instance key is spendable only when the operator explicitly sets
  `ALLOW_INSTANCE_FALLBACK`; no code path bills the operator silently.
- **Daily scheduling** — projects are queued in waves across the day rather than
  all at midnight, with atomic claims and a stale-claim sweep so work is not
  lost to a dead worker.
- **Documentation** — deployment, configuration, testing, design, product
  design, orchestration, provider integration, and a user guide.
- **A test suite** — 253 tests covering authentication, cross-account ownership,
  credential encryption, bring-your-own-key routing, the rank-state contract,
  team permissions, the shipped route surface, and query budgets.

### Changed

- **An unranked keyword is no longer reported as position 101.** The API now
  distinguishes four states — ranked, outside the tracked depth, not measured,
  and never checked — and never presents a position the product did not
  observe. Out-of-range results state the depth that produced them.
- **The keyword history chart shows gaps, not invented positions.** A range with
  no positions at all says so instead of drawing an empty grid.
- **Page-load cost is flat in project count.** The shell endpoint went from 22
  queries to 10 and stopped growing with the account.

### Removed

- **Billing** — 3,245 lines. The product is bring-your-own-key and self-hosted:
  there is no plan to sell, no checkout, and no storefront.
- **Keyword research and search volume** — needed a paid data source this
  product does not buy.
- **Page audit** and **Content Gap** — depended on unfinished paths.
- **Favourites** — the dashboard widget was cut first; what remained set a flag
  nothing displayed.

  Together with unreachable modules and views, roughly 10,000 lines that no
  route could reach. `tests/test_shipped_surface.py` fails if any of it returns.

### Security

- Cross-account ownership is enforced in middleware rather than per view, after
  56 views were found trusting an unvalidated account id from the request body.
- Provider credentials are encrypted at rest with an authenticated envelope and
  are never returned in clear text.
- Scheduler and engine endpoints are token-gated with a constant-time compare
  and fail closed: no token configured means no valid callers.

### Known limitations

- **The keywords endpoint does not paginate.** Every keyword in a project is
  returned on each load. Fine at hundreds; roughly 3 MB at 5,000.
- **Google Search Console and Analytics are parked** pending a proper
  server-side OAuth flow, and are shown as unavailable rather than advertised.
- **The runtime is legacy** — Django 3.2 with djongo on MongoDB 4.4. Treat the
  bundled Compose stack as a development environment; see `docs/DEPLOYMENT.md`
  for running it for real.

[Unreleased]: https://github.com/databluedev/searchmirror/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/databluedev/searchmirror/releases/tag/v0.1.0
