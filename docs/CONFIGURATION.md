# Configuration reference

Every setting SearchMirror reads, what it does, and what breaks without it.

There are two templates and they are not interchangeable:

| File | For | Notes |
|---|---|---|
| `.env.example` | local development | `cp .env.example .env`, then `docker compose up -d`. Contains a published MongoDB password and `DJANGO_DEBUG=True` on purpose — safe only because everything binds to loopback |
| `.env.production.example` | a real instance | Start here for anything else, and read [`DEPLOYMENT.md`](DEPLOYMENT.md) first |

Both are committed and contain no real credentials. **Any new setting must be
added to `.env.example` with a comment saying what breaks without it.**

---

## Database

| Variable | Default | What it does |
|---|---|---|
| `MONGO_URI` | local URI | Full connection string. **When set it wins** over the six values below; keep them in sync or leave this blank |
| `MONGO_USER` / `MONGO_PASSWORD` | `tracker` / `trackerlocal` | Created on the container's first boot. Changing these after the volume exists does nothing — `docker compose down -v` to re-initialise |
| `MONGO_DB` | `tracker` | Database name |
| `MONGO_HOST` / `MONGO_PORT` | `mongo` / `27017` | Compose service name, not `localhost` |
| `MONGO_AUTH_SOURCE` | `admin` | The root user is created in `admin`, so this must point there, not at `MONGO_DB` |
| `MONGO_MAX_POOL_SIZE` | — | Production only. Size against `GUNICORN_WORKERS` × `GUNICORN_THREADS` |
| `DB_CONN_MAX_AGE` | `600` | **Do not set to 0.** Django's default of 0 costs a flat ~500 ms on *every* authenticated request: djongo caches one `MongoClient` per database and closes it at the end of each request, so the next request reopens a dead client and waits out pymongo's 0.5 s topology-rescan floor |

## Django

| Variable | Default | What it does |
|---|---|---|
| `DJANGO_DEBUG` | `True` locally | Serves tracebacks with settings, environment and SQL to whoever asks. Also makes settings re-raise import errors instead of logging them. **Never true on a reachable instance** |
| `DJANGO_SECRET_KEY` | placeholder | Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"`. With `DJANGO_DEBUG=False` the app **refuses to start** while this is still the placeholder — that is intentional |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,backend` | `backend` must stay: the engine calls the API by its compose-network name, and dropping it makes engine-driven competitor analysis return `400 DisallowedHost` |
| `APP_SITE_URL` / `APP_API_URL` | loopback | Public browser and API origins used in links the backend generates. `APP_API_URL` is **compiled into the frontend bundle at image build time** — changing it needs an image rebuild, not a restart |
| `CORS_ALLOWED_ORIGINS` | loopback | Browser origins allowed to call the API |
| `CORS_ALLOW_ALL` | `false` | Leave off outside local work |
| `ENABLE_DJANGO_ADMIN` | `false` | `/serministrator/` gives full cross-tenant model access and nothing in the product links to it. Routed only when `DJANGO_DEBUG=True` or when this is explicitly `true`. An obfuscated URL is not access control |

## SERP provider — bring your own key

| Variable | Default | What it does |
|---|---|---|
| `SERP_KEY_SECRET` | placeholder | Master secret for the authenticated-encryption envelope every stored credential uses (`shared/keycrypto.py`). Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. **Rotating it makes every stored account key unreadable** and every user must re-enter theirs — treat it as permanent |
| `DATABLUE_API_KEY` | blank | Instance-wide key. Only ever spent when the next setting is on |
| `ALLOW_INSTANCE_FALLBACK` | `false` | Whether a rank check with no per-account key may spend `DATABLUE_API_KEY`. `true` for a single-operator self-host; `false` for anything multi-user, where an account with no key gets **no ranking** rather than quietly spending yours. Nothing on screen would look wrong if it did, which is why this is a switch and not a default |

Accounts enter their own DataBlue key in the UI under **Account → SERP key**.
The key is validated against the provider, then encrypted at rest. It is never
returned in clear text.

## AI providers

Optional. Geo Citations and Content Planner use whichever provider an account
configures under **Settings → API Keys**; these instance-level values are
fallbacks governed by the same rules as the SERP key.

| Variable | Provider |
|---|---|
| `OPENAI_API_KEY` / `OPENAI_MODEL` | OpenAI |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` | Anthropic |
| `PERPLEXITY_API_KEY` / `PERPLEXITY_MODEL` | Perplexity |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Google Gemini |

All four go through one path (`backend/account/completions.py` and
`backend/account/aikeys.py`). Do not call a provider SDK directly from a view.

## Scheduling and the engine trigger

| Variable | What it does |
|---|---|
| `CRON_TOKEN` | Gates the scheduler endpoints. Compared with `hmac.compare_digest` and **fails closed**: no token set means no valid callers, which is the safe direction |
| `ENGINE_TRIGGER_TOKEN` | The same mechanism for the backend-to-engine trigger |
| `ENGINE_STALE_CLAIM_MINUTES` | How long a claimed keyword may sit before another worker sweeps it back. Guards against work lost to a dead worker |
| `ENGINE_TENANT_WAIT_CAP` | Upper bound on how long one tenant's turn may block others |
| `ENGINE_KEYWORD_ATTEMPT_CAP` | Attempts before a keyword is recorded as failed rather than retried forever |
| `ENGINE_KEYWORD_BACKOFF_MINUTES` | Wait between attempts |

See [`ORCHESTRATION.md`](ORCHESTRATION.md) for what these actually control.

## Engine service

| Variable | What it does |
|---|---|
| `ENGINE_SECRET_KEY` | The engine's own Django secret; independent of the backend's |
| `ENGINE_DEBUG` | As `DJANGO_DEBUG`, for the engine |
| `ENGINE_ALLOWED_HOSTS` / `ENGINE_ALLOWED_IPS` | The engine binds to loopback on purpose and is not meant to be reachable from outside the compose network |
| `ENGINE_THREADS` / `ENGINE_WORKERS` | Production only. Concurrency for the ranking worker |

## Web server concurrency (production only)

| Variable | What it does |
|---|---|
| `GUNICORN_WORKERS` | Processes. The work is CPU-bound — djongo builds SQL through Django and then parses it back with `sqlparse`, roughly 44% self-time against 8% socket I/O — so scale workers with cores, not with expected traffic |
| `GUNICORN_THREADS` | Threads per worker. Raising this does not help CPU-bound work; it mainly costs memory and pool connections |

## Email

| Variable | What it does |
|---|---|
| `EMAIL_HOST` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP. Blank disables outbound mail entirely |
| `HOST_MAIL` / `ADMIN_MAIL` | From and administrative addresses |
| `EMERGENCY_MAIL` | Engine watchdog alerts. Blank disables the alert — empty entries are filtered out and no mail is attempted |

## Local seed

Development only; the production overlay does not run the seed.

| Variable | Default | What it does |
|---|---|---|
| `SEED_LOCAL` | `true` | Whether to run the idempotent local seed on boot |
| `SEED_EMAIL` / `SEED_PASSWORD` | `admin@local.test` / `LocalDev12345` | The seeded sign-in |
| `SEED_DOMAIN` | — | Domain for the seeded project |

## Google Search Console (parked)

| Variable | Status |
|---|---|
| `VITE_GSC_CLIENT_ID` / `VITE_GSC_SECRET` | **Parked.** The code is retained but there is no server-side OAuth flow yet, so the feature is shown as unavailable rather than advertised as ready |
| `REACT_APP_GSC_CLIENT_ID` / `REACT_APP_GSC_SECRET` | Pre-Vite names, kept for compatibility |

---

## Things that bite

- **`APP_API_URL` is baked into the frontend bundle.** Changing it requires
  rebuilding the `app-prod` image; a restart will not pick it up.
- **`SERP_KEY_SECRET` is permanent.** Rotating it strands every stored key.
- **`DB_CONN_MAX_AGE=0` costs about 500 ms per request.** It is not a safe
  value here even though it is Django's default.
- **The production overlay refuses to start without `APP_API_URL`.** That is a
  deliberate guard, not a bug: the bundle would otherwise be built pointing at
  nothing.
- **`ALLOW_INSTANCE_FALLBACK=true` on a multi-user instance spends your money.**
  There is no per-account ceiling behind it.
