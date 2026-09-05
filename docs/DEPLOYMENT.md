# Deploying SearchMirror

Last reviewed: 2026-09-02

This is the production checklist. Work through it in order — the steps depend
on each other, and several of them cannot be fixed after the first boot.

If you only want SearchMirror on your laptop, you do not need this file. Follow
the Quick start in the README and stop there.

---

## 0. What the development stack is, and what it is not

`docker-compose.yml` on its own is a development environment. It is honest
about it, but it is worth being explicit, because it is the file you get by
cloning the repository:

| The dev stack does this | Production needs |
|---|---|
| `manage.py runserver` — auto-reloading, single process, explicitly unsupported by Django for production | a real WSGI server (the overlay uses gunicorn) |
| `DJANGO_DEBUG=True` — serves full tracebacks with settings and query values to whoever triggers an error | DEBUG off, and a real `DJANGO_SECRET_KEY` |
| a seeded demo account whose password is published in this repository's README | no seed |
| a MongoDB password published in this repository | a generated one, set before the first boot |
| the Vite dev server, compiling on demand over an open HMR websocket | the prebuilt static bundle behind nginx |
| plain HTTP on your loopback interface | TLS, terminated by a reverse proxy you run |

> A note on that first row, because the usual shorthand is wrong. `runserver`
> **is** threaded — it serves one request per thread, and the running process
> here carries 16 of them. What it is not is multi-process, supervised, or
> willing to hold a connection backlog: past roughly 60 simultaneous
> connections it resets them rather than queueing (measured: 51 of 60 served,
> 9 reset; 84 of 120 served, 36 reset). It also reloads on every source change.
> The problem with `runserver` in production is not that it is serial. It is
> that nothing restarts a dead worker and nothing bounds the queue.

`docker-compose.prod.yml` fixes the process-level rows: the server, the seed,
what is published, and the frontend. `.env.production.example` fixes the
configuration rows: DEBUG, the keys, the database password. **Neither fixes the
last row, and neither fixes your host.** Everything below the overlay section
is still your job.

### The overlay

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
               --profile prod up -d --build
```

It layers on top of the base file and never replaces it. Concretely it:

- runs both Django services under gunicorn instead of `runserver`
- drops `seed_local.py` from the backend's start command
- publishes the API and the frontend on `127.0.0.1` only, and MongoDB not at all
- moves the Vite dev server behind a `dev` profile so it never starts
- serves the frontend from `app-prod` (nginx + the built bundle)

Requires **Docker Compose 2.24 or newer** — the overlay uses the `!override`
and `!reset` merge tags. `docker compose version` to check.

Set an alias, or you will eventually run `docker compose up -d` by itself on
the server and quietly restart the development stack:

```bash
alias smc='docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile prod'
```

---

## 1. Before you start: two end-of-life runtimes

SearchMirror runs on **Django 3.2** (extended support ended April 2024) and
**MongoDB 4.4** (end of life February 2024). Neither receives security fixes.

This is a known pre-1.0 condition, not an oversight, and it is tracked as a
release blocker. It has two consequences for you now:

1. **Do not "upgrade" MongoDB on your own.** The ORM is `djongo 1.3.6`, which
   does not support MongoDB 5 or later. Moving the database forward requires
   moving off djongo at the same time. Pinning `mongo:4.4` is deliberate.
2. **Keep the database off the network.** An unpatched 4.4 with a public port
   is the single most likely way this deployment is compromised. The compose
   files no longer publish it; do not add the port back.

Decide with open eyes whether an EOL stack is acceptable for your data, then
continue.

---

## 2. Host preparation

- A Linux host with Docker Engine and the Compose plugin.
- A firewall that denies inbound by default. Open **443 only** (and 22 for
  yourself). Nothing else in this stack should be reachable from outside.
- Enough disk for the Mongo volume plus logs, and monitoring on free space.
- A DNS name for the app and one for the API — e.g. `example.com` and
  `api.example.com`. They may be the same host.

Docker publishes ports by punching through `iptables`, *below* most host
firewalls: a `ports:` entry bound to `0.0.0.0` is reachable from the internet
even when `ufw` says the port is closed. This is why every published port in
these files is pinned to `127.0.0.1`. If you edit a `ports:` line, keep the
`127.0.0.1:` prefix.

---

## 3. Configuration

```bash
cp .env.production.example .env
$EDITOR .env
```

Fill in every value marked `REQUIRED`. The generators are in the comments
beside each one. Four of them are worth calling out:

| Variable | Why it matters |
|---|---|
| `MONGO_PASSWORD` / `MONGO_URI` | The root user is created on the volume's **first boot only**. Getting this wrong means re-initialising the database, which means losing it. Set it before you start anything, and keep the two in sync. |
| `DJANGO_SECRET_KEY` | Signs sessions and password-reset links. On the committed placeholder, anyone with the repository can forge both. `settings.py` refuses to start with DEBUG off and a placeholder, so a mistake here is a crash, not a silent hole. |
| `SERP_KEY_SECRET` | Encrypts every account's stored DataBlue key. **Rotating it makes all stored keys permanently unreadable** and every user must re-enter theirs. Treat it as permanent and put it in your backups. |
| `APP_API_URL` | Compiled into the frontend bundle at **image build time**, not read at runtime. Changing it later requires `--build`, not a restart. |

Leave `SEED_LOCAL` and `ENABLE_DJANGO_ADMIN` blank. Both are gated to refuse to
run in production, and both gates exist because the alternative was a
deployment booting an internet-reachable account with a documented password.

### Judge speed on the production build, not the dev server

The development stack is not slow by accident; it is slow by design, and it is
the thing most people have in front of them when they form an opinion about how
fast the product is. Measure both before concluding anything.

Vite in dev serves every module as its own HTTP request, unminified, compiling
SCSS on demand — and on Docker Desktop it reads them across a bind mount. The
production build is 70 pre-built chunks, minified and gzipped, of which a first
paint needs five files.

| | Development (`:3001`) | Production build |
|---|---:|---:|
| Requests for a first paint | **31+** | **5** |
| Transferred | **2.4 MB** | **286 KB** gzipped |
| Per-module latency | 3–7 ms (×31) | one request per chunk |

The dev figure is a **floor, not a total**: it was measured by walking only
three levels of the module graph. A real page load resolves the whole graph —
263 source files plus their dependencies. Cold and warm caches made no
difference to the count, only to per-module latency (7.1 ms cold, 3.2 ms warm).

The production numbers come from `app/build` after `npm run build`: a 732 KB
main chunk (233 KB gzipped) and a 322 KB stylesheet (52 KB gzipped). All 70
chunks together are 1.1 MB gzipped, but only the five above are needed before
the app is usable; the rest are route chunks fetched on navigation.

To see the production bundle locally, bring up the `app-prod` service on
`:4001` (see the overlay section above) rather than reading `:3001` and
extrapolating.

### `DB_CONN_MAX_AGE` — leave it alone unless you are debugging

Seconds a database connection is reused across requests. Default 600.

Django's own default is `0`, which closes the connection after every request.
That is wrong for this stack in a way that is easy to miss. djongo memoises one
`MongoClient` per database name for the life of the process
(`djongo/database.py`), but its `_close()` closes that shared client — so the
next request pulls the same dead client back out of the cache, reopening it
resets the pymongo topology, and server selection cannot rescan sooner than
`MIN_HEARTBEAT_INTERVAL`, which is 0.5s.

The result was a flat ~500ms on **every** authenticated request, whatever it
did. Measured on the dev stack, before and after:

| Endpoint | `DB_CONN_MAX_AGE=0` | `=600` |
|---|---:|---:|
| `/country_list` | 502.4 ms | 14.3 ms |
| `/refreshstatus` | 502.6 ms | 49.0 ms |
| `/dashservice` (142 KB) | 499.7 ms | 68.4 ms |
| `/baseauth` | 513.6 ms | 101.5 ms |

CPU across ten sequential requests went from 13% of wall time to 88% — the
server was blocking, not computing.

Set it to `0` only to rule out a connection-reuse problem. That restores the
old behaviour exactly, with no code change and no rebuild — a restart is
enough. It is a bounded value rather than `None` on purpose: the connection is
still recycled periodically, so any state djongo accumulates cannot live for
the whole life of the worker.

`.env` holds every secret this deployment has. `chmod 600 .env`, keep it out of
your backups' world-readable paths, and note that `docker compose config`
prints its contents in clear text — do not paste that output into an issue.

---

## 4. Reverse proxy and TLS

Nothing in this stack terminates TLS or speaks HTTPS. Session tokens ride in
the `Authorization` header; over plain HTTP they are readable by every hop.
This step is not optional.

Run nginx (or Caddy, or Traefik) on the host, get certificates from Let's
Encrypt, and forward to the two loopback ports. A working nginx skeleton:

```nginx
# Frontend — the built bundle served by app-prod.
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:4001;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# API.
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    # CSV keyword upload.
    client_max_body_size 25m;

    # Report generation and PDF rendering are synchronous and slow; they
    # outlive the 60s default. Matches gunicorn's --timeout 120.
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then, in `.env`:

- `DJANGO_ALLOWED_HOSTS` must list `api.example.com` — and must keep `backend`,
  because the engine container calls the API by its compose-network name.
- `CORS_ALLOWED_ORIGINS` must be `https://example.com`, with the scheme. Never
  set `CORS_ALLOW_ALL`.
- `APP_SITE_URL` and `APP_API_URL` must be the `https://` URLs.

Redirect port 80 to 443, and consider HSTS once you are confident in the
certificate renewal.

### Static files

gunicorn does not serve static files, and no WSGI static middleware is
installed. This only matters if you set `ENABLE_DJANGO_ADMIN=true`: run
`docker compose exec backend python manage.py collectstatic --noinput` and map
`/static/` in the proxy, or the admin arrives unstyled. The product itself
serves no Django static assets — the frontend is a separate nginx container.

---

## 5. First boot

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
               --profile prod up -d --build
```

Then verify — and verify the thing itself, not a proxy for it:

```bash
# All four services up, and mongo/backend/app-prod reporting healthy.
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile prod ps

# The API answers through your proxy, over TLS, with a real response body.
curl -i https://api.example.com/

# Django's own audit of the deployment. It should report no issues; anything
# it flags here is a real finding.
docker compose exec backend python manage.py check --deploy

# DEBUG is genuinely off.
docker compose exec backend python -c \
  "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','tracker.settings'); django.setup(); from django.conf import settings; print('DEBUG =', settings.DEBUG)"
```

A container being `Up` is not the same as the application working. Sign in with
a real account and load the dashboard before you call the deployment done.

---

## 6. Backups

The Mongo volume is the entire product: projects, keywords, every rank
observation, and the encrypted per-account SERP keys.

```bash
# Dump to a file on the host.
docker compose exec -T mongo mongodump \
    --username "$MONGO_USER" --password "$MONGO_PASSWORD" \
    --authenticationDatabase admin --archive --gzip \
  > "backup-$(date +%F).archive.gz"
```

Run it from cron, ship the output off the host, and **restore one into a
throwaway instance before you trust the schedule.** An untested backup is a
guess.

Back up `.env` alongside it, separately and encrypted. Without
`SERP_KEY_SECRET` a restored database still cannot decrypt a single stored
provider key.

---

## 7. Daily ranking schedule

> **PLACEHOLDER — being built now, do not improvise around it.**
>
> As shipped, nothing triggers the daily rank check on a schedule. Ranking runs
> when someone clicks Refresh (via `ENGINE_TRIGGER_TOKEN`) or when an operator
> runs `docker compose exec engine python rank_local.py` by hand. A scheduler
> is in active development and will land with its own operator instructions;
> this section will be replaced with them.
>
> Until then: do not invent a cron entry against the engine's automation
> endpoints. They spend provider credits per call, and getting the frequency or
> the concurrency wrong bills you for it.

The Geo Citations scheduler is separate and already documented: it is an HTTP
endpoint gated on `CRON_TOKEN`, sent as an `X-Cron-Token` header, and it
refuses everyone with 503 while that variable is blank.

---

## 8. Logs

Two independent streams, with different problems.

**Container stdout/stderr** is captured by Docker's `json-file` driver, which
by default keeps every line ever written until the disk fills. Both compose
files now cap it at 10 MB × 3 files per service. Nothing further to do.

**Application log files** are a different matter. The backend and engine append
to `backend/logs/` and `engine/logs/` on the host — bind-mounted, hand-written
with plain appends, and never rotated or deleted. Payment, report, watchdog and
per-group ranking logs all land there. Add host-side rotation:

```
# /etc/logrotate.d/searchmirror
/opt/searchmirror/backend/logs/*.log
/opt/searchmirror/backend/logs/**/*.log
/opt/searchmirror/engine/logs/**/*.log {
    weekly
    rotate 8
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

`copytruncate` is required: the application holds each file open and appends,
so a plain rename leaves it writing to a deleted inode.

---

## 9. Container users

The application processes run as an unprivileged user (uid 1000), not root.
This matters because the host source tree is bind-mounted into every one of
them, so root in the container was root on your files.

The switch happens in the compose command rather than as a `USER` line in the
Dockerfile, because it has to. `logs/`, `files/` and `project/files/` are
inside the bind mount, so they do not exist at build time — and on any stack
that has run before, they are already owned by root. Each container therefore
starts as root, creates and `chown`s exactly those directories (never `/app`
itself), then `exec setpriv --reuid=app` hands the container over. No root
process survives that line. Check it:

```bash
docker compose exec backend ps -o user,pid,args
```

`docker compose exec` itself still lands you as root — that is the image's
default user, and it is convenient for admin tasks. Add `-u app` for a shell
as the application sees the world.

**Use `-u app` for anything that writes.** A manual ranking run as root leaves
root-owned files under `engine/project/files/`, and the server, running as
`app`, then cannot rewrite them:

```bash
docker compose exec -u app engine python rank_local.py
```

**If the account owning the checkout on the host is not uid 1000**, that chown
will take your own `logs/` and `files/` away from you. Build with your ids:

```bash
docker compose build \
  --build-arg APP_UID=$(id -u) --build-arg APP_GID=$(id -g) backend engine
```

---

## 10. Known gaps

Be aware of these before you expose this to anyone but yourself.

- **Django 3.2 and MongoDB 4.4 are end of life** (section 1). No security fixes.
- **The images have no application code in them.** Both Dockerfiles install
  dependencies only; the source arrives through a bind mount, in production
  too. That means a deployment is a git checkout on the server, `git pull` is
  the update mechanism, and the containers need write access to part of that
  tree. It is not a self-contained artifact you can push to a registry.
- **No readiness endpoint.** The healthchecks confirm that something is
  accepting TCP connections on the port, which is enough to order startup but
  not enough to tell you the application is serving correctly. A proper
  endpoint is specified and pending.
- **No rate limiting** on login or on the API generally. Put it in the reverse
  proxy if this is internet-facing.
- **Google Search Console / Analytics OAuth is parked.** The client secret
  would be public in browser code; the exchange belongs on the server. Do not
  treat it as a supported integration.

  Both screens that reference it — Add Project and Project Settings → Connected
  Apps — show it as **Coming soon**, visible and inert. They deliberately do
  *not* tell the user how to enable it: registering an OAuth client and setting
  build-time variables is your job, not theirs, and the instructions used to sit
  in an end user's settings page naming environment variables at somebody with
  no shell.

  If you do want to try it on your own instance: register a Google OAuth client,
  set `VITE_GSC_CLIENT_ID` and `VITE_GSC_SECRET` in `.env`, and rebuild the
  frontend image — these are inlined at build time, so a restart is not enough.
  With no client id set, the Google controls render as Coming soon and nothing
  mounts that could throw. Note the caveat above still applies: the flow puts
  the secret in browser code, so this is for local experimentation, not for a
  deployment serving other people.

  With no project connected, the keyword list omits the Search Console columns
  entirely rather than sending zeros — see `_gsc_connected` in
  `backend/serp/views.py`. `gsc_last_track` defaults to `utcnow` on the model,
  so it is truthy on a project that never connected anything; the property and
  the track status are what actually answer the question.
- **Report and PDF generation is synchronous.** A large report occupies a
  gunicorn *thread* for its whole duration, and WeasyPrint rendering is
  CPU-bound, so it takes a real share of a core with it. It no longer blocks a
  whole process — that is what the threaded worker class buys — but size
  `GUNICORN_WORKERS` toward `2 × cores + 1` if your users generate reports
  often. Measured: six concurrent exports in flight left an ordinary API call
  at 1.22× its idle latency.

---

## 11. Updating

```bash
git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
               --profile prod up -d --build
```

Take a backup first (section 6). Migrations run automatically on backend start
and are not reversed automatically, so the backup is your rollback.
