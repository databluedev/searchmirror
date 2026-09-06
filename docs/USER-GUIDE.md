# User guide

How to use a running SearchMirror instance. If you are setting one up, start
with the [README](../README.md) for local use or
[`DEPLOYMENT.md`](DEPLOYMENT.md) for a real one.

> **Ranking costs money.** Every rank check spends one DataBlue request per page
> of results, against *your* key. Nothing in this product ranks anything without
> being asked — but the buttons that ask are easy to click, so they are named
> explicitly in [§10](#10-what-costs-money).

---

## 1. Signing in

Open the application (locally, <http://127.0.0.1:3001>) and sign in. A local
development instance seeds one account:

| Field | Value |
|---|---|
| Email | `admin@local.test` |
| Password | `LocalDev12345` |

**On a real instance there is no seeded login.** That account's password is
published in this repository, so it is created only when the development stack
is running. On a production instance you register the first account through the
signup page — which sends a verification email, so the operator must have
configured SMTP first.

Sessions live in **cookies**, not local storage. If you rebuild the database
while a browser tab is open, the stale cookie makes every request fail with a
401 and it looks like broken login — clear the site's cookies and sign in
again.

## 2. What you will see first

A new account has no projects, so most of the product has nothing to report on
yet. That is expected, and the app says so rather than failing:

- The rail still lists every feature — so you can see what SearchMirror does —
  but the ones that need a project are marked **Set up**.
- Opening one shows what is missing and a single button that fixes it.
- Once a project exists, the marks disappear and those pages fill in.

Three different things can leave a screen waiting, and each says which:

| What it says | What it means |
|---|---|
| **No projects** | The account is empty. Create a project. |
| A key is required | The feature needs a DataBlue or AI key. Add it under Settings. |
| **No rankings yet** | The project exists but nothing has been checked yet. |

The order to work through is: **key → project → keywords → rank**.

## 3. Adding your DataBlue key

SearchMirror is **bring-your-own-key**. Nothing will rank until a key is stored.

**Account → SERP key.** Paste your key from
[datablue.dev](https://datablue.dev) and save. The key is validated against the
provider before it is accepted, then encrypted at rest. It is never shown again
in full and never returned in clear text by the API.

An operator *may* configure an instance-wide key, but it is only spendable when
they explicitly enabled `ALLOW_INSTANCE_FALLBACK`. If you have no key and
fallback is off, rank checks do nothing rather than quietly spending someone
else's credits.

## 4. Creating a project

A project is one domain tracked in one place.

1. **Add project**, then enter the domain.
2. Choose **country**, **language** and **device**. These are part of the query
   sent to Google — the same keyword in two countries is two different
   measurements, so track them as two projects (or set per-keyword overrides).
3. Choose the **search depth** in pages. This is the single most important
   setting on the screen, because it decides both what you can see and what you
   pay:

   | Pages | Results searched | Cost per keyword per check |
   |---:|---:|---:|
   | 1 | top 10 | 1 request |
   | 2 | top 20 | 2 requests |
   | 3 | top 30 | 3 requests |

   A keyword outside the depth you chose is reported as *not in the first N* —
   truthfully, and without guessing a position. Increasing depth later is
   allowed; it costs proportionally more on every future check.

## 5. Adding keywords

**Add keywords** takes one keyword per line. Keep them literal: a keyword is
the exact string sent to Google, and it is stored and displayed exactly as
typed, with no re-casing.

Individual keywords can override the project's country, language, device or
depth from the keyword's own **Configuration** panel — useful for the handful
of terms you want tracked deeper than the rest without paying for the whole
list.

## 6. Reading the dashboard

The dashboard summarises one project.

- **Visibility** is a single weighted score across your tracked keywords. It is
  computed in one place (`shared/scoring.py`) so the dashboard, the reports and
  the engine cannot disagree about it.
- **Movement** shows what rose and fell since the previous check.
- **Alerts** are composed by the server, not the browser, so what you see is
  what the API actually determined. An alert that offers a re-check tells you
  what it will cost before you confirm.

## 7. Reading the keywords table

The position column never invents a number. It shows one of four states:

| What you see | What it means |
|---|---|
| A number | The domain was found at that position |
| **Not in the first 30** (or your depth) | Checked, and the domain was not in the pages searched. A real measurement |
| **Not checked yet** | The keyword has never been checked |
| **Could not be checked** | A check ran and failed — a provider error, not a ranking |

The distinction matters: the first two are data, the last two are the absence
of data. Sorting and filtering keep unranked keywords below every real
position rather than treating them as position 101.

Click any keyword to open its detail page.

## 8. The keyword detail page

**Overview** — current position, best position, the depth that produced the
result, and the keyword's configuration.

**Rank history** — every recorded position over the selected range. A rise on
the chart is a move *towards* position 1. A break in the line is a day the
domain was not in the pages searched; if that is true of every day in the
range, the chart says so rather than drawing an empty grid.

**SERP features** — what else was on the results page: AI Overview, featured
snippet, knowledge panel, reviews, ads and so on. Rows expand to show the
underlying content. Where an AI Overview is present you can read the full
answer text and the sources it cited, and see whether your domain was among
them.

**Notes** — dated annotations. Use them to record what you changed, so a
movement six weeks later has an explanation attached.

## 9. The other modules

**Competitors** — track rival domains against the same keywords and compare
positions side by side.

**Geo Citations** — how often AI assistants mention your brand when asked
questions in your space, and which sources they cite. Uses your own AI provider
key.

**Content Planner** — generates article outlines and drafts from a keyword and
a brief. Also uses your own AI provider key. Generation runs in the background:
you can leave the page, and if the server restarts mid-run the job is reported
as interrupted rather than left claiming to be running.

**Reports** — export what you are tracking as PDF or CSV.

**Team** — invite members and grant them per-module permissions. A member signs
in with their own credentials and acts within the owning account, so their
access can be narrowed without sharing the owner's login.

## 10. What costs money

Only these spend provider credits:

| Action | Spends |
|---|---|
| **Rank** / **Refresh** on a keyword or project | DataBlue: one request per page of depth, per keyword |
| The daily scheduled run (01:00) | The same, for every keyword due |
| **Generate** in Content Planner | Your AI provider |
| Running Geo Citations | Your AI provider |

Browsing, sorting, filtering, exporting and reading history cost nothing — they
read what has already been measured.

## 11. When something looks wrong

**Every keyword says "Not checked yet".** No key is stored, or a check has not
run yet. Add your DataBlue key under Account → SERP key, then rank once.

**Everything 401s and login looks broken.** A stale session cookie against a
rebuilt database. Clear cookies for the site and sign in again.

**A keyword says "Could not be checked".** The provider returned an error for
that keyword. Re-check it; if it persists, the keyword or its region setting is
usually the cause.

**Positions have not moved in days.** Confirm the scheduler service is running.
Without it, nothing is checked automatically and every position is as old as
your last manual refresh.

**A rank looks wrong.** Compare against the live results page — the keyword
detail page links out to the exact query, country and device that produced the
measurement.
