# What ships, and what only looks unreachable

A module with no callers is not automatically dead. This codebase deliberately
keeps several that nothing routes to, and it reaches others by name rather than
by import. Both look identical to a naive "who imports this?" search, and both
have been wrongly reported as dead here before.

So the distinction is **written down** rather than inferred, and
`tests/test_shipped_surface.py` reads these lists.

---

## Removed: unrouted feature code, deleted rather than published

This project used to keep four "parked" apps — complete enough to keep, not
part of the supported surface, routed by nothing. On **2026-09-05** all four
were deleted, along with one module and one view that existed only to serve
them. Parking made sense while this was a private working copy. It stops making
sense the moment the repository is published: an unrouted app is not dormant,
it is **shipped** — cloned, read, scanned, and reported against.

| Removed | Files | Lines | Why it could go |
|---|---:|---:|---|
| `backend/payment` | 22 | 3,245 | Billing. The product is bring-your-own-key and self-hosted: no plan to sell, no checkout, no storefront. Included a Stripe integration and a code-redemption flow that named a commercial marketplace. |
| `backend/kw_research` | 14 | 3,378 | Keyword research and search volume. Needed a paid volume data source this product does not buy, and still named the commercial predecessor. |
| `backend/pageaudit` | 10 | 1,130 | Page audit. Depended on a crawl path that was never finished. |
| `backend/content_gap` | 9 | 1,072 | Content Gap. Depended on `kw_research`. |
| `backend/serp/searchvolume.py` | 1 | 679 | Existed only to import `payment` and `kw_research` for a metered volume feature. |
| **Total** | **56** | **9,504** | |

None of them was load-bearing, and each had exactly one thread into live code:

- **`payment`** — one Django admin registration in `serp/admin.py`. Three other
  modules imported `UserSubscriptions` in an import line and never used it.
- **`kw_research`** — `serp/views.py` imported its models with a wildcard and
  used one class, inside a `gresultpage` branch selected by a `pageType` its
  single caller has never sent.
- **`content_gap`** — `serp/serializers.py` counted `CGASearch` rows into a
  `cGLT` field no screen reads.
- **`pageaudit`** — nothing at all.

`tests/test_shipped_surface.py` fails if any of them returns, or if one is
listed in `INSTALLED_APPS` without being on disk. `PARKED_PACKAGES` in that
file is now empty on purpose: add an entry only for something deliberately kept
**and** deliberately unrouted, with the reason written down.

---

## Reached by name, not by import

These have no importer and are still live. A reachability check that does not
know about them reports every one as dead — which is exactly what happened the
first time one was written.

| Path | Reached by |
|---|---|
| `backend/serp/management/commands/rank_schedule.py` | `manage.py rank_schedule`, run every 15 minutes by the `scheduler` service in `docker-compose.yml` |
| `backend/tracker/wsgi.py` | gunicorn, via `tracker.wsgi:application` in `docker-compose.prod.yml` |
| `backend/tracker/asgi.py` | Django's ASGI entry point |
| `backend/project/wsgi.py` (engine) | gunicorn, via `project.wsgi:application` |
| `*/tests.py` | Django's own test discovery. Empty stubs; harmless. |
| `*/migrations/*.py` | Django's migration loader, by directory |
| `*/admin.py`, `*/apps.py` | Django's app registry |

---

## Removed 2026-09-05

Nothing imported these and no URL reached them. Each was checked by resolving
imports to the **file** they load, not to a module name, and each deletion was
verified on its own before the next.

| Path | Lines | Evidence |
|---|---:|---|
| `backend/serp/widget_serializers.py` | 265 | A stale subset of the live `serp/custom_serializer/widget_serializers.py` (472 lines). **Five files mention the name and zero of them resolve to this file** — all three real importers (`serp/brand_acq.py`, `serp/e_com_widget.py`, `serp/widget.py`) load the `custom_serializer/` copy. |
| `backend/llmtracker/recompute.py` | 97 | No importer, no route. |
| `backend/llmtracker/claude.py` | 35 | No importer. Superseded by `get_anthropic_client` in `llmtracker/views.py`. Eight files mention "claude" — all of them the provider name in `claude_api_key` / `claude_model`, none of them this module. |

**652 lines.** After each removal: both `manage.py check` clean, the full suite
passing, and the affected endpoints returning byte-identical bodies —
`/eldnah_wdt`, `/dashboard_overview`, `/dashservice` for the first, and all six
Geo Citations endpoints for the last two.

### The trap worth remembering

`serp/widget_serializers.py` is why the check resolves imports to files. Grep
for the leaf name and it looks used by four files; every one of those imports
resolves to a different file with the same name. A name is not a module.

---

## Dependencies kept although nothing in `src/` imports them

`package.json` cannot carry comments, so the reasons live here. Each is a
**peer requirement** of something the application does use: remove it and the
build succeeds while the app fails at runtime, which is the worst way for this
to go wrong.

| Package | Required as a peer by |
|---|---|
| `@emotion/react` | `@mui/material`, `@mui/system`, `@mui/lab`, `@mui/x-date-pickers`, `@emotion/styled` |
| `react-dnd` | `react-tag-input` |
| `react-dnd-html5-backend` | `react-tag-input` |

## Dependencies removed 2026-09-05

Zero references anywhere in `app/src`, and not a peer requirement of anything
kept. 51 declared dependencies to 39.

`@mui/styles`, `@radix-ui/react-slot`, `jwt-decode`, `lodash`, `lottie-react`,
`papaparse`, `react-copy-to-clipboard`, `react-google-login`,
`react-grid-layout`, `react-table`, `react-timer-hook`,
`use-state-with-callback`.

The check that produced this list is in `tests/test_shipped_surface.py`: a
candidate must be unreferenced in the source **and** absent from the peer
requirements of every dependency being kept. The first pass of this analysis
looked only at source references and would have removed `@emotion/react`,
taking MUI down with it.
