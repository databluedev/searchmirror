# SearchMirror × DataBlue — integration brief

**Date:** 2026-08-30
**For:** DataBlue engineering
**From:** SearchMirror team

A short, factual brief on what we are building, how we use DataBlue today, and
what we would need from the DataBlue API to move the rest of the product onto
it. No action is requested beyond a feasibility read on the "What we'd need"
section.

---

## 1. What SearchMirror is

SearchMirror is an **open-source, self-hostable SEO rank tracker and AI-visibility
monitor**. Two things it does:

- **Keyword rank tracking** — track a domain's Google position for a set of
  keywords, per country, per device.
- **Geo Citations** — track whether AI models (ChatGPT, Claude, Gemini,
  Perplexity) mention a brand for a set of prompts. (This uses the operator's
  own AI keys, not DataBlue.)

It is **bring-your-own-key (BYOK)**: each account holder pastes their **own
DataBlue API key**, and every SERP call is billed to that key. SearchMirror itself
sells nothing and meters nothing — DataBlue is the SERP provider.

## 2. Where the project lives

| | |
|---|---|
| **Local path** | `D:\Github_repo\opentracker` |
| **Remote** | none yet — private, not pushed |
| **Backend** | Django 3.2 (Python), MongoDB (via djongo/mongoengine) |
| **Ranking engine** | separate Python service (`engine/`), talks to DataBlue |
| **Frontend** | React 17 + Vite + MUI |
| **Run** | `docker compose up` — services: `mongo`, `backend`, `engine`, `app` |

The DataBlue-facing code is in **`engine/project/machine/automation_proxy.py`**
(SERP calls) and **`backend/account/api/views.py`** (key validation + balance).

## 3. How we use DataBlue today

Two endpoints, both authenticated with the account's key as
`Authorization: Bearer <key>`.

### 3a. SERP — keyword rank tracking

```
GET https://api.datablue.dev/v1/data/google/serp
Authorization: Bearer <account key>
```

Query params sent per keyword:

| Param | Value | Notes |
|---|---|---|
| `query` | the keyword (≤256 chars) | |
| `pages` | account's `serp_depth`, default **3** | ~10 organic results per page |
| `advanced` | `false` | lightweight, organic-only |
| `domain` | `google.com` (per-keyword override) | Google TLD |
| `mobile` | `true` / `false` | from the keyword's platform |
| `language` | e.g. `en` | derived per keyword |
| `country` | e.g. `in` | derived per keyword |

We read `position` / `url` from the organic results to compute the domain's
rank. Calls run concurrently (semaphore width 100). This is the **only** thing
SearchMirror bills DataBlue for today, and it works well.

### 3b. Usage — key validation & balance

```
GET https://api.datablue.dev/v1/usage/summary
Authorization: Bearer <account key>
```

Used for two things: (1) validating a pasted key (401/403 ⇒ reject), and (2)
showing the account's credit balance in Settings. We rely on this being
**"not charged"** as documented — please keep that guarantee.

## 4. Feature → data-source map (current state)

| Feature | Data it needs | Source today | On DataBlue? |
|---|---|---|---|
| Keyword rank tracking | Google SERP positions | **DataBlue** `/google/serp` | ✅ yes |
| Credit balance / key check | usage summary | **DataBlue** `/usage/summary` | ✅ yes |
| Competitor AI | SERP results to find who ranks | **DataBlue** `/google/serp` | ✅ yes |
| Geo Citations | AI model responses | operator's AI keys | n/a |
| **Keyword Research** | related keywords **+ search volume** | **DataForSEO** | ⚠️ partial |
| **Content Gap** | **ranked keywords** for a domain | **DataForSEO** | ❌ no |

## 5. What we'd need from DataBlue to drop DataForSEO

We would like to remove the DataForSEO dependency entirely and run the whole
product on a DataBlue key. Three data needs are not covered by the current
DataBlue API (as we read the docs):

1. **Keyword search volume** — absolute monthly search volume (and ideally CPC
   and a difficulty score) for a keyword + country. Today
   `/google/keyword-suggestions` returns related keyword *ideas* with a
   relevance score, but **no volume**. Google Trends interest is relative, not
   absolute, so it does not substitute.

2. **Ranked keywords for a domain** — given `example.com` + country, the list
   of keywords the domain ranks for, with position and volume. This is the core
   of DataForSEO Labs `ranked_keywords/live`, and it powers our Content Gap
   feature. We could not find a DataBlue equivalent.

3. **Related keywords with metrics** — related/expanded keywords for a seed,
   each with search volume, to power Keyword Research (DataForSEO Labs
   `related_keywords/live`).

If DataBlue exposes (or plans) any of these — especially **ranked keywords for
a domain** and **keyword volume** — we would move Keyword Research and Content
Gap onto DataBlue immediately and retire DataForSEO from the product.

## 6. Endpoints we already know DataBlue has (for reference)

From the public docs, useful to us or adjacent:

- `/v1/data/google/serp` — **in use**
- `/v1/usage/summary` — **in use**
- `/google/keyword-suggestions` — ideas only, no volume
- `/google/trends-interest`, `/google/trends-autocomplete` — relative interest
- `/scrape`, `/crawl`, `/search`, `/extract` — web data (not yet used)

---

*Questions to the SearchMirror team: which endpoints and payloads to expect, rate
limits, and whether the three data needs in §5 are on the DataBlue roadmap.*
