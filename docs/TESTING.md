# Testing SearchMirror

The suite lives in `tests/` and is run with pytest. It is the thing that decides
whether a change is finished, so this document explains not just how to run it
but what kind of test to write, because the suite has two very different kinds
in it and picking the wrong one wastes your time.

```bash
docker compose up -d                        # the suite needs a RUNNING stack
pip install -r tests/requirements.txt
python -m pytest tests -q
```

`tests/requirements.txt` is what the suite needs **on your machine**, which is
not the same as what the containers need. Most tests are HTTP clients and want
only `pytest` and `requests`; a few import backend modules directly to test pure
functions, and those pull in dependencies that otherwise live only inside the
backend image. If a new test imports something from `backend/`, add it there —
CI installs that file and will fail with `ModuleNotFoundError` otherwise.

At the time of writing that is **249 tests in about 35 seconds**.

---

## 1. Why the tests talk HTTP instead of using Django's test client

Django normally creates a throwaway database for each test run. It cannot here:
this project reaches MongoDB through **djongo**, and djongo cannot build a test
database. There is no `manage.py test` path that works.

So the suite drives a running stack over HTTP, as a client. That has three
consequences you need to hold in your head:

- **The stack must be up.** A failure that says "connection refused" means you
  forgot `docker compose up -d`, not that you broke something.
- **Tests share one database.** They run against the seeded account, and a test
  that creates data must clean it up. See §5.
- **Tests cannot see inside the server process.** No `connection.queries`, no
  monkeypatching, no fixtures injected into a view. That is why the second kind
  of test exists.

Point the suite somewhere else with environment variables:

```bash
TRACKER_API=http://127.0.0.1:8000 \
TRACKER_EMAIL=admin@local.test \
TRACKER_PASSWORD=LocalDev12345 \
python -m pytest tests -q
```

---

## 2. The two kinds of test

### Live tests — the default, and what you should reach for first

They log in, call an endpoint, and assert on the response. `tests/conftest.py`
gives you three fixtures:

| Fixture | What it is |
|---|---|
| `api` | the base URL, from `TRACKER_API` |
| `auth` | `(user_id, token)` for the seeded account |
| `headers` | ready-made `Authorization: Token …` headers |

```python
def test_a_project_list_needs_a_token(api):
    response = requests.post(api + "/baseauth", json={"userid": "1"}, timeout=60)
    assert response.status_code in (401, 403)
```

If the seeded account is missing, the fixture **skips** rather than fails —
a skip means "the environment is not set up", a failure means "the code is
wrong". Keep that distinction.

### Source-assertion tests — for properties an HTTP response cannot show

Some invariants are not visible from outside the process. Query counts are the
clearest example: the shell endpoint must not issue more queries as the account
grows, and nothing in an HTTP response reveals how many queries produced it. So
`tests/test_shell_query_budget.py` asserts on the *shape of the source* that
produces the property — that the serializer reads a bulk index rather than
querying per row.

The same technique guards the product surface: `tests/test_product_surface.py`
fails if an unrouted feature comes back, if a paywall reappears, or if a design
rule is violated in a file.

**These tests have one trap, and it has caught this project more than once.**
A check written as `assert "old_value" not in source` fails against *correctly
fixed* code the moment a comment explains what the old value was. Assert on what
runs, not on what the file says. `tests/test_rank_state.py` carries a `_code()`
helper that strips comments before asserting; use it, or assert on a positive
fact ("the new function is called") rather than the absence of a string.

---

## 3. What is covered, and what is not

Covered: authentication and token resolution, ownership enforcement, cron and
engine-trigger gating, registration and first-run, credential encryption and
masking, bring-your-own-key routing, the rank-state contract, team permissions,
the shipped route surface, dead code and unused dependencies, query budgets,
and the keyword-detail payload.

**Not covered, and the biggest gap:** the ranking pipeline itself, the SERP
parsers, and report generation. Contributions there are especially welcome.
The parsers and `shared/` are pure functions that need no database and no
network — they are the easiest place to start and the most valuable.

---

## 4. Writing a test for a bug

Write the test **before** the fix, and watch it fail for the reason you think.
A test that passes before your fix is testing something else.

The tests in this repo carry a docstring explaining *what went wrong and why the
check exists*, not a restatement of the assertion. Compare:

```python
# Not useful: says what the code says.
def test_half_publishes_sf():
    """Asserts sf is in the half branch."""

# Useful: says why anyone should care.
def test_the_half_branch_publishes_the_serp_feature_record():
    """The regression itself: without this the panel renders a chip and a
    source list with no answer and no feature rows."""
```

The second one tells the next person whether a failure matters. Write that.

---

## 5. Rules that keep the suite honest

- **Never weaken a test to make it pass.** If a test fails after your change,
  either the change is wrong or the test encoded an assumption that is no longer
  true — and if it is the second, say so in the pull request and explain why.
- **Clean up what you create.** The suite shares one database. A test that adds
  a project must remove it. (`tests/test_registration.py` currently leaks one
  real account per run; that is a known bug, not a pattern to copy.)
- **Do not spend money in a test.** Ranking a keyword bills a real DataBlue
  request. No test may call Rank, Refresh, or Generate against a live key.
- **A skip is not a pass.** If your new test skips on every machine, it is
  testing nothing.

---

## 6. Verification beyond the suite

Passing tests are not a working system. Before you say a change is done:

```bash
docker compose exec -T backend python manage.py check
docker compose exec -T engine  python manage.py check
docker compose exec -T app npm run build          # the real check for the frontend
cd landing && pnpm build
docker logs --tail=100 tracker-backend 2>&1 | grep -A5 Traceback
```

Then click through the screens your change touches at
<http://127.0.0.1:3001>. **Do not click Rank, Refresh or Generate** unless you
mean to spend real provider credits.

Say in your pull request what you actually verified and what you did not.
"Builds, suite passes, I clicked through the keywords page but not reports" is a
useful and honest statement. Claiming more than you checked is not.
