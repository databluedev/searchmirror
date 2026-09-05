# Contributing to SearchMirror

Thanks for looking. This file covers everything you need to get productive:
running the stack, where code lives, the conventions that matter, and the two or
three things that will otherwise waste your afternoon.

Read [`README.md`](README.md) first for what SearchMirror is and the BYOK model.

---

## Before you write code

**Set your line endings to LF.** Do this before your first commit — it is the
single most common way to break this build:

```bash
git config core.autocrlf false
git config core.eol lf
```

The repo ships a [`.gitattributes`](.gitattributes) that pins every text file to
LF, so a fresh clone is correct. The trap is an editor or tool that writes CRLF
into a file that already has LF lines. When that happens to a stylesheet, the
build does not warn — **it fails outright**:

```
resolve-url-loader: found orphan CR, line ...
```

The error names the loader, not your file, so it reads like a dependency problem
and sends people hunting in `node_modules`. It is a line ending. Fix the file:

```bash
# check what a file actually has (CRLF shows as "with CRLF line terminators")
file app/src/assets/styles/modules/_tokens.scss

# strip carriage returns from a single file
sed -i 's/\r$//' path/to/file.scss
```

This applies to every text file, but SCSS is where it actually breaks the build.

---

## Running the stack

Every environment variable is documented in
[`docs/CONFIGURATION.md`](docs/CONFIGURATION.md); a new setting must be added to
`.env.example` with a comment saying what breaks without it.

**Requirements:** Docker and the Compose plugin. Python, Node and MongoDB all
run in containers — you do not need any of them installed.

```bash
cp .env.example .env
docker compose up -d
```

`.env` must exist before the first `up`. The committed defaults are safe local
values; you do not need to edit them to get a running stack.

| Container | URL | What it is |
|---|---|---|
| `tracker-app` | http://127.0.0.1:3001 | main application |
| `tracker-backend` | http://127.0.0.1:8000 | Django API |
| `tracker-engine` | http://127.0.0.1:8001 | ranking engine |
| `tracker-mongo` | 127.0.0.1:27017 | MongoDB 4.4 |

Sign in with `admin@local.test` / `LocalDev12345`.

**Use container names, not service names, with `docker logs`.** The containers
are named `tracker-*` — kept for volume and deployment compatibility — while the
Compose services are `mongo`, `backend`, `engine`, `app` and the prod-profile
`app-prod`. `docker logs tracker-app` works; `docker logs app` matches nothing.
`docker compose logs app` works too — just do not mix the two forms.

### Watching a build

`app/` runs Vite, which uses native file events and serves in ~50ms, so no
polling flag is needed. A rebuild takes a few seconds:

```bash
docker compose logs -f app
```

Wait for Vite's `ready in ...` line, or for the `hmr update` it prints on each
save. An error is printed in full, with the file and line, right where it
happens — there is no `Compiled successfully` banner; that was CRA.

Existing warnings are mostly `no-unused-vars` inherited from the original
codebase. **Do not add new ones**, but you are not expected to fix the backlog
to land a change.

### The seed

The backend runs migrations and `backend/scripts/seed_local.py` on every boot,
so a usable tenant always exists. To run it by hand:

```bash
docker compose exec backend python scripts/seed_local.py
```

It is idempotent — safe to re-run any number of times. It creates the login, an
`Accountusage` row that unlocks the app without Stripe, one project, the
region/language lookups the keyword form needs, and keywords with rank history.

Override what it creates with `SEED_EMAIL`, `SEED_PASSWORD` and `SEED_DOMAIN`
in `.env`.

### Resetting the database

```bash
docker compose down -v && docker compose up -d
```

**Then clear your browser cookies for `localhost`.** Auth is stored in cookies
(`session_token`, `session_userid`), not localStorage. A rebuilt database issues
new tokens but the browser keeps the old cookie, and every request 401s until
you clear it. This looks exactly like a broken login.

### Ranking for real

The only command that spends money. It bills your DataBlue account one request
per keyword, and prints the estimated cost before starting:

```bash
docker compose exec engine python rank_local.py
```

Add your key in the UI under **Settings -> API Keys** first.

---

## Where things live

| Path | What it is |
|---|---|
| `app/` | **Main frontend.** React 18, Vite. Dashboard, keywords, projects, reports, account settings. Most UI work happens here. |
| `landing/` | **Marketing site.** React 18 + Vite + Tailwind. Fully independent — not in the Compose stack. Run it with `cd landing && pnpm install && pnpm dev` on port 5180. |
| `backend/` | **Django API.** Accounts, projects, keywords, competitors, Geo Citations, Content Planner, reports, team management. Everything the frontend calls. Keyword research, search volume, page audit, content gap and billing have been removed entirely. |
| `engine/` | **Ranking worker.** Django + async httpx. Calls DataBlue, parses SERPs, writes rank history. Scheduling and concurrency live in `engine/project/machine/`. |
| `docker/` | Dockerfiles and the nginx config used by the prod-profile builds. |
| `docs/` | Integration notes. The design-system and planning documents are internal and gitignored, so a fresh clone will not have them. |

Inside each frontend, `src/pages/<feature>/` holds a feature, with an `index.js`
entry, a `components/` directory, and a `style.scss`. Routes are registered in
`src/pages/routeComponents/`.

### One frontend

`app/` is the only frontend and serves one audience: the account holder. There
used to be a second build mode and a separate `client-app/` fork for an
agency-facing client portal; both are gone. The portal is preserved on the
`client-portal-archive` branch if a hosted tier ever wants it rebuilt.


## The design contract

**The design system governs every pixel.** It is not a suggestion, and UI
changes that ignore it will be sent back. The written contract is in this
repository: [`docs/DESIGN.md`](docs/DESIGN.md) decides how the product looks and
[`docs/PRODUCT-DESIGN.md`](docs/PRODUCT-DESIGN.md) decides how it is organised.
Read both before a UI change. Where a document and the SCSS disagree, the SCSS
is right — fix the document in the same pull request.

The rules below are the ones people trip over most often.

The one that catches everyone:

> **Never hardcode a colour in a component or a page stylesheet.**

All tokens are defined once as CSS custom properties in
`src/assets/styles/modules/_tokens.scss` and mirrored into the MUI theme in
`src/App.js`. Use `var(--ink)`, `var(--paper)` and the rest. If the value you
need is not already a token, it does not belong in the component — raise it as
an issue and get the token added.

Open an issue before proposing navigation or information-architecture changes.
The current structure is inherited and actively being replaced, so a well-meant
tweak may be moving something that is already scheduled for removal.

The mark is the other fixed point: `brand/` is the source of truth for every
favicon, logo and wordmark. Regenerate from there rather than redrawing at the
call site — `brand/README.md` says which file feeds what.

---

## Conventions

**Python.** Tabs in some inherited modules, four spaces in others — match the
file you are editing rather than reformatting it. Do not reformat a file you are
not otherwise changing; it buries the real diff.

**JavaScript.** Match the surrounding file. No global reformatting.

**Commits.** Use a type prefix:

```
fix: keyword table 500s when a keyword has never ranked
feat: bulk keyword import from CSV
docs: document SERP_KEY_SECRET rotation
refactor: extract SERP key validation from the view
chore: remove superseded contentGapOld page tree
```

Keep the subject under about 72 characters and say what changed, not what you
did.

**Secrets.** Never commit `.env`, an API key, or a credential — not in code, not
in a test fixture, not in a comment. `.env.example` is committed and must only
ever contain blanks and safe local defaults. If you need a new setting, add it
to `.env.example` with a comment saying what it does and what breaks without it.

---

## Testing your change

`tests/` holds the suite. It runs over HTTP against a **running** stack,
because djongo on MongoDB cannot create a Django test database — there is no
working `manage.py test`.

```bash
docker compose up -d            # required; the suite is an HTTP client
pip install pytest requests
python -m pytest tests -q
```

**[`docs/TESTING.md`](docs/TESTING.md) is the full guide** — how the fixtures
work, the difference between a live test and a source-assertion test, the
comment-stripping trap that has broken source assertions here before, what is
covered and what is not, and the rules that keep the suite honest.

The three that matter most:

- **Never weaken a test to make it pass.** If the test encoded an assumption
  that is no longer true, say so in the pull request and explain why.
- **Do not spend money in a test.** Ranking a keyword bills a real DataBlue
  request. Nothing in the suite may call Rank, Refresh or Generate.
- **Passing tests are not a working system.** Also run:

  ```bash
  docker compose exec -T backend python manage.py check
  docker compose exec -T engine  python manage.py check
  docker compose exec -T app npm run build
  docker logs --tail=100 tracker-backend 2>&1 | grep -A5 Traceback
  ```

  then click through the screens you touched at <http://127.0.0.1:3001>.
  Do not click Rank, Refresh or Generate unless you mean to spend credits.

Say in your pull request what you actually verified and what you did not.
"Builds, suite passes, I clicked the keywords page but not reports" is a useful
and honest statement. Claiming more than you checked is not.

---

## Submitting a change

1. Branch off `main`.
2. Keep the change focused — one concern per PR.
3. Make sure the stack still builds (above).
4. Open a PR describing **what** changed, **why**, and **what you verified**.
5. Note explicitly if a change affects only one role, and why.

For anything large — restructuring, a new dependency, a schema change,
consolidating the two frontends — open an issue first so the approach can be
agreed before you spend the time.

---

## Good first contributions

- **Rename the obfuscated endpoints.** Inherited from the commercial product:
  `Z2V0YWxscHJvamVjdHM`, `dnert_wdt` and others. They work, they are
  just unreadable. Needs care — each rename touches a URL, a view and every
  frontend call site.
- **Clear the eslint warning backlog**, a directory at a time.
- **Delete dead code.** `tests/test_shipped_surface.py` fails on a module
  nothing reaches, so the check is automated — but prove it before removing:
  search the filename *and* its exported symbols across
  `app/src`, `backend/`, `engine/`, `landing/` and `shared/` — before removing
  it.
- **Documentation.** If something here was wrong or missing when you set up, fix
  it. You are the best-placed person to.

---

## Code of conduct

Taking part means agreeing to the [Code of Conduct](CODE_OF_CONDUCT.md). Report
a problem to the maintainer at <mdali.sheik1613@gmail.com>.

## Continuous integration

Every pull request runs [`.github/workflows/ci.yml`](.github/workflows/ci.yml):
it boots the Docker stack, runs both Django checks and the full suite, and
builds the application and the marketing site. `main` is protected — nothing
lands without a pull request, and CI has to be green.

The scheduler service is deliberately **not** started in CI: it queues due
projects and pokes the engine, and a rank run spends real provider credits.

## Licence

SearchMirror is licensed under the
[GNU Affero General Public License v3.0](LICENSE). If you modify it and provide
the modified software as a network service, the AGPL requires that service's
users be offered the corresponding source code.

By contributing you agree that your contribution is licensed under the same
terms.
