# SearchMirror — what a rank tracker should be in 2026

SearchMirror's UI began as a restyled version of the commercial product it was
adapted from, because at first only the surface changed. That product's
**information architecture** dates from around 2015 and was carried over
intact. This document decides what replaces it; `DESIGN.md` decides how it
looks.

---

## 1. What actually changed in search since this layout was designed

| Then (the layout we inherited) | Now |
|---|---|
| Ten blue links | AI Overviews and AI Mode occupy the answer slot above them |
| Google is the surface | ChatGPT, Perplexity, Gemini and Copilot are parallel discovery surfaces |
| "What position am I?" | "Am I in the answer at all, and cited how?" |
| One site, one owner | Agencies run 40 clients and must prove value monthly |

A tracker that only answers "what position am I on Google today" is answering a
2015 question. **Rank is now one signal among several**, and a 2026 tracker is
credible only if it also reports presence in AI answers.

The parent product (`llm-monitor`) already does exactly this — it tracks SEO
*and* GEO. That is the bar, and it is our own bar, not a competitor's.

## 2. What the inherited layout gets wrong

**"Widgets."** A dashboard of configurable widgets is a 2015 idea. It pushes the
job of designing the page onto the user, who does not want it, and the default
state is `/dashboard` rendering "No widget found" — an empty page as a first
impression.

**The overview grid answers no question.** Comparison, Device, Today's
Performance, Tracker score, SERP Features, Google Search Ads — six boxes of
unrelated numbers, equal visual weight, no hierarchy. Nothing on that screen
tells you *what changed* or *what to do*. It is a stat dump.

**It leads with state, not change.** "You have 6 keywords, 5 in the top 100" is
inert. The question is always "what moved since last time, and why".

**The keyword table — the actual product — is below the fold**, under an
overview nobody reads twice.

**Colour carried no meaning** (fixed), and **numbers were not comparable**
(fixed) — but those were symptoms. The architecture is the cause.

## 3. What this product should be

### The one-line job

> Tell me whether my visibility is rising or falling, on every surface that
> matters, and what specifically to look at today.

Three commitments follow from that:

1. **Lead with change, never with state.**
2. **Rank is one surface. AI answers are another.** Track both or be a 2015 tool.
3. **One page answers one question.** No dashboards of everything.

### Screens

**Projects** — one row per project, dense, scannable at 40 clients. Metrics as a
rail, not as tiles. *(Done.)*

**Project overview** — replaces `/dashboard` and the widget concept entirely.
A single narrative page, top to bottom:

1. **The headline.** One sentence of real English: *"14 keywords moved this week.
   9 up, 5 down. Visibility is up 3 points."* Generated from the data, not a
   stat grid.
2. **Trend.** Visibility score over time, one line, with annotations where
   something happened. Range switcher: 7d / 30d / 90d.
3. **Movers.** Two short lists side by side — biggest gains, biggest losses. Five
   each. Each row links to the keyword. This is the page's most useful element
   and it does not exist today.
4. **Surfaces.** Where the visibility actually is: organic positions, AI Overview
   presence, featured snippets, People Also Ask, local pack. A single horizontal
   breakdown, not six cards.
5. **Segments.** Performance by tag, so an agency can answer "how is the money
   category doing" without filtering by hand.

**Keywords** — the table is the product. Overview collapses by default so the
table is above the fold. Segment lens (by tag) as a first-class filter, not a
buried dropdown. Bulk actions. *(Table styling done; hierarchy not.)*

**Keyword detail** — history chart first, SERP snapshot second, metadata last and
quiet. Currently the reverse.

**AI visibility (new)** — the differentiator, and what makes this a 2026 product:
for each tracked keyword, is the domain present in the AI answer, and cited how.
The parent product already solves this; the architecture here must leave room for
it rather than pretending search is still ten links.

### What to delete

- The **widget system**. It is configuration in place of design.
- `/dashboard` as a widget host. The route becomes the project overview above.
- The **six-card overview grid**, replaced by the narrative page.
- **Tracker score as a hero number.** A composite nobody can act on. Keep it as a
  trend line; stop putting it in a ring at the top of every card.

## 4. Visual direction — corrected

The first pass was too austere. Measured against `llm-monitor`, which is the
in-house standard:

| | llm-monitor (target) | tracker (first pass) |
|---|---|---|
| Page title | `text-4xl` (36px) bold, tight tracking | 26px |
| Page padding / section rhythm | `p-8 space-y-8` (32px) | 16–24px |
| Cards | `border` + `shadow-elegant` + `bg-card/80`, backdrop blur | flat, border only, **no shadow at all** |
| Section headers | `bg-muted/20` strip with a bottom border | plain |

The correction: **keep the monochrome discipline, add back confidence.** Bigger
titles, more air, and one soft elevation on cards so they read as objects rather
than as fenced-off regions. Flat-with-hairlines is a legitimate style but it
reads as timid next to the parent product, and this has to look like something an
agency would pay for.

Not negotiable, unchanged: colour carries meaning only, tabular numerals, one
accent, visible focus, reduced-motion honoured.

## 5. Order of work

1. Project overview replaces the widget dashboard — the biggest single change.
2. Keyword table hierarchy: overview collapsed, table first, segment lens.
3. Keyword detail re-ordered: chart, SERP, metadata.
4. Visual correction: type scale up, spacing up, one elevation level.
5. Leave room in the IA for AI-answer visibility.

Steps 1–3 are architecture and are what stops this reading as a copy. Step 4 is
an hour. Step 5 is the roadmap.
