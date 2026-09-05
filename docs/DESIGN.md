# Tracker — design system

One source of truth. Every screen, both apps (`app/`, `client-app/`).
If a value is not in this file, it does not belong in a component.

**Direction:** monochrome editorial. One white ground for the whole product,
near-black ink, edges drawn with a hairline rather than a fill. One blue for
links and the focused state, one violet for navigation state. Type does the
work; colour does not decorate. Generous radius, hairline borders, no shadows
except on things that genuinely float (menus, dialogs, toasts).

Reference feel: wide geometric grotesk headlines, bracketed uppercase micro-labels,
fully-rounded pill buttons, large cards separated by hairlines, not by tint.

The values below are transcribed from
`src/assets/styles/modules/_tokens.scss`, which is the source. When they
disagree, the SCSS is right and this table is stale — three rows here (`--paper`,
`--surface-2`, `--line`) were exactly that, and two people re-derived contrast
numbers from them before it was caught. Re-read the SCSS before computing
anything from a value on this page.

---

## Tokens

Defined once in `src/assets/styles/modules/_tokens.scss` as CSS custom properties
on `:root`, and mirrored into the MUI theme in `src/App.js`. **Never hardcode a
hex in a component or a page stylesheet.**

### Colour

| Token | Value | Use |
|---|---|---|
| `--ink` | `#0f0f10` | primary text, primary button fill |
| `--ink-2` | `#3d3f45` | secondary text |
| `--ink-3` | `#6b6e76` | muted text, table headers, captions |
| `--ink-4` | `#9aa0a8` | disabled, placeholder |
| `--paper` | `#ffffff` | page canvas |
| `--surface` | `#ffffff` | cards, tables, menus |
| `--surface-2` | `#f5f5f6` | inset panels, hover fill, chips, skeletons |
| `--line` | `rgba(15,15,16,0.12)` | all borders and dividers |
| `--line-2` | `rgba(15,15,16,0.06)` | table row separators |
| `--accent` | `#1a3cff` | links, focus ring, selected state |
| `--accent-weak` | `#e8ecff` | selected table row |
| `--nav-accent` | `#791fba` | active rail item, active tab label, rail bar, "new" dot |
| `--nav-accent-weak` | `#f1e9fc` | active rail item / active tab fill |
| `--up` | `#12b76a` | rank improved |
| `--down` | `#d92d20` | rank declined |
| `--flat` | `#98a2b3` | no change — neutral, never orange |
| `--warn` | `#dc6803` | approaching a quota cap |

Rules:
- Colour must carry meaning. Never assign a colour to distinguish one card,
  meter, or row from another when a label already does that.
- No gradients. No coloured card tints. No pastel fills.
- Rank direction is the only place green and red appear.
- `--accent` means "act on this or follow this". `--nav-accent` means "you are
  here". They are two jobs, so they are two colours — `--accent` used to do
  both, which made an active rail item read as a call to action.

### `--nav-accent`, derived

OKLCH `0.470 / 0.220 / 305` — a deep violet, generated at fixed lightness and
chroma, then measured rather than eyeballed.

Hue 305 is the widest gap left in the palette: 39.4° from `--accent` (265.7)
and 30.2° from the chart plum (335.2), its two nearest neighbours. Green
(`--up`, 154.9), red (`--down`, 29.5) and amber (`--warn`, 50.2) are reserved
for rank direction and quota pressure and were excluded by rule, not by taste.

Measured on `#ffffff`:

| Use | Pair | Ratio | Needs |
|---|---|---|---|
| active tab / rail label | `#791fba` on `#f1e9fc` | 6.55:1 | 4.5:1 |
| label on the page ground | `#791fba` on `#ffffff` | 7.73:1 | 4.5:1 |
| label on a hovered row | `#791fba` on `#f5f5f6` | 7.09:1 | 4.5:1 |
| rail bar, "new" dot — non-text marks | `#791fba` on `#ffffff` | 7.73:1 | 3:1 |
| white label, if a solid fill is ever used | `#ffffff` on `#791fba` | 7.73:1 | 4.5:1 |

Separation from `--accent` in OKLab (×100): 18.1 normal, 12.1 deuteranopia,
10.8 protanopia, 12.8 tritanopia — it stays a different colour, not a darker
blue, under all three simulations.

`--nav-accent-weak` is `#f1e9fc` — the same hue at `--accent-weak`'s lightness
and chroma (OKLCH `0.946 / 0.026 / 305`). It is **1.18:1 on white**, so like
`--accent-weak` (1.17:1) it cannot carry a state on its own and never appears
as the only difference between two states. The state is carried by the label
(6.55:1 on the fill) and, on the rail, by the solid 3px bar (7.73:1). No tint
of this hue can do both jobs: a fill dark enough to reach 3:1 against white
leaves only 2.58:1 under a `#791fba` label, which is why the pair exists.

### Type

Self-hosted **Space Grotesk** (variable, 300–700, OFL) —
`src/assets/fonts/SpaceGrotesk-latin.woff2` + `-latin-ext.woff2`.

```
--font: "Space Grotesk", "Be Vietnam Pro", -apple-system, Segoe UI, sans-serif;
```

The existing aliases `Regular` / `SemiBold` / `Bold` stay declared and all now
resolve to Space Grotesk at 400 / 600 / 700. **Do not rename them** — hundreds of
call sites reference them and there is no `Medium` face.

| Role | Size / weight / tracking |
|---|---|
| page title | 26px / 600 / -0.03em |
| card title | 15px / 600 / -0.015em |
| body | 14px / 400 / 0, line-height 1.55 |
| small | 12.5px / 400 |
| micro-label | 11px / 600 / 0.08em / uppercase / `--ink-3` |
| data numeral | 15px / 600, `font-variant-numeric: tabular-nums` |

Every column of numbers uses `tabular-nums`. Body text never below 12.5px.

### Space, radius, motion

```
--sp-1: 4px   --sp-2: 8px   --sp-3: 12px  --sp-4: 16px
--sp-5: 24px  --sp-6: 32px  --sp-7: 48px

--r-sm: 8px    inputs, chips, small controls
--r-md: 14px   cards, tables, menus
--r-lg: 20px   page-level panels
--r-pill: 999px  buttons, tabs, badges

--dur: 160ms   --ease: cubic-bezier(0.2, 0, 0, 1)
```

Transition only `color`, `background-color`, `border-color`, `opacity`,
`transform`. Never `width`/`height`/`top`/`left`.

---

## Components

**Button** — pill (`--r-pill`), height 38px, padding 0 18px, 13.5px/600, no shadow.
- primary: `--ink` fill, white text; hover lightens to `#26262a`
- secondary: `--surface` fill, `--line` border, `--ink` text; hover `--surface-2`
- ghost: transparent, `--ink-2` text; hover `--surface-2`
- destructive: transparent, `--down` text and border
- Minimum hit area 38×38. Icon-only buttons carry an `aria-label`.

**Input** — 38px, `--r-sm`, `--line` border, `--surface` fill. Focus: `--accent`
border plus a 3px `--accent-weak` ring. Label always visible above the field;
placeholder is never the label. Error text sits under the field, in `--down`.

**Card** — `--surface`, `--r-md`, 1px `--line`, padding `--sp-5`, no shadow.
Header row: title left, actions right, `--sp-4` bottom padding, hairline under it.
Cards in one row are equal height and their footers align.

**Table** — `--surface`, `--r-md`, 1px `--line`, header row `--surface-2` with
micro-label type. Rows 52px, separated by `--line-2`, hover `--surface-2`,
selected `--accent-weak`. Numeric columns right-aligned and tabular.
Wide tables scroll inside their own `overflow-x:auto` — the page never scrolls
sideways.

**Nav (left rail)** — `--surface`, right border `--line`. Item 40×40, `--r-sm`.
Active: `--nav-accent-weak` fill, `--nav-accent` icon and label, and a solid
3px `--nav-accent` bar on the leading edge — the bar is what the eye finds
peripherally, because the fill is a pale tint on a white rail. Hover:
`--surface-2`. Every item has an accessible name and a tooltip when collapsed.

**Tabs** — one pattern, every strip. Pills, never an underline, and the strip
carries no bottom rule. 38px strip, 34px pill, `--r-pill`, 13.5px/600,
`--ink-3` at rest, `--surface-2` on hover, `--nav-accent-weak` fill with a
`--nav-accent` label when selected — the same pair the rail uses — and no MUI
indicator. The pill is defined once in
the MUI theme (`App.js` → `MuiTabs` / `MuiTab`); the strip wrapper is
`.tabStrip` in `_controls.scss`, and 24px of air separates it from its panel.
A page stylesheet must never restate `.MuiTab-root`, `.MuiTabs-scroller` or
`.MuiTabPanel-root` — those sheets are global once their page loads, so a
"local" tab override repaints every strip in the app.

**Avatar** — initials on `--ink`, white text, 600, `--r-pill`. No third-party
avatar service, no imported illustration.

**Empty state** — micro-label, one sentence of body, one primary action. No art.

**Loading** — a `--surface-2` skeleton in the shape of the content it replaces.
No spinner over 400ms of work, no coloured dots.

---

## Non-negotiable

1. No hex literals outside `_tokens.scss` and the MUI theme.
2. No emoji as icons. SVG only, 1.5px stroke, `currentColor`, 18px in the rail.
3. Focus is always visible — 2px `--accent` outline, 2px offset. Never `outline:none`
   without a replacement.
4. Text contrast ≥ 4.5:1. `--ink-3` on `--surface` is the lightest text permitted.
5. `prefers-reduced-motion: reduce` collapses every transition to ~0.
6. Works at 375 / 768 / 1024 / 1440 with no horizontal page scroll.
7. Nothing ships that references the commercial product this was adapted from,
   or any third-party account (analytics, session recording, affiliate, avatar
   or favicon services). No outbound request leaves a self-hosted instance
   except to the providers the operator configured.
8. The landing page is the same palette, not a sibling of it. See below.

---

## The landing page

`landing/` is Vite + Tailwind + shadcn, so it cannot `@import` the SCSS. It
restates the same values as the bare HSL triples Tailwind needs for
`hsl(var(--x) / <alpha>)`, in `landing/src/index.css`. `_tokens.scss` is the
source; that file is the mirror.

| `_tokens.scss` | value | `landing/src/index.css` |
|---|---|---|
| `--ink` | `#0f0f10` | `240 3.2% 6.1%` |
| `--ink-2` | `#3d3f45` | `225 6.2% 25.5%` |
| `--ink-3` | `#6b6e76` | `223.6 4.9% 44.1%` |
| `--ink-4` | `#9aa0a8` | `214.3 7.4% 63.1%` |
| `--paper` | `#ffffff` | `0 0% 100%` |
| `--surface` | `#ffffff` | `0 0% 100%` |
| `--surface-2` | `#f5f5f6` | `240 5.3% 96.3%` |
| `--line` | `rgba(15,15,16,0.12)` | same rgba, plus `--border`/`--input` `0 0% 88.6%` — that alpha composited on white, because Tailwind's `border-*` needs an opaque triple |
| `--line-2` | `rgba(15,15,16,0.06)` | same rgba |
| `--accent` | `#1a3cff` | `231.1 100% 55.1%` (also `--ring`) |
| `--up` | `#12b76a` | `152 82.1% 39.4%` |
| `--down` | `#d92d20` | `4.2 74.3% 48.8%` (also `--destructive`) |
| `--flat` | `#98a2b3` | `217.8 15.1% 64.9%` |

Landing-only, with a reason: `--line-strong` (`rgba(15,15,16,0.2)`) for the
card hover the app does not have, and the shadcn contract names
(`--background`, `--card`, `--primary`, …), which alias the tokens above
rather than holding values.

App-only, with a reason: `--accent-weak`, `--warn` and the `--nav-accent` pair
are selected rows, quota pressure and navigation state. A marketing page has
none of those, so it does not declare them.

Every triple carries one decimal place. Integer percentages drift up to 3/255
from the app's hex — `--accent-weak` lands on `#e5eaff` instead of `#e8ecff`.
Do not round them.

The landing used to run a warm ground: `--paper: 60 8% 95%` (`#f3f3f0`) with
`--border: 60 3% 86%` (`#dcdcda`). The app has neither, so crossing from the
marketing page into the product changed product. Both are gone.

---

## Motion

Implemented in `src/assets/styles/modules/_motion.scss`. CSS only — no animation
library, nothing to load.

This is an application, not a landing page. Motion explains where something came
from; it never decorates. One distance, one curve, two durations:

| | |
|---|---|
| distance | 8px, always vertical |
| curve | `--ease` — `cubic-bezier(0.2, 0, 0, 1)` |
| entrance | 300–320ms |
| state change | 90–160ms (`--dur`) |
| stagger | 35–40ms per step, capped at 5 steps / 8 items |

Rules:
- Animate `opacity` and `transform` only. Never `width`, `height`, `top`, `left` —
  those force layout every frame.
- A press moves 1px. Hover on a dense table row resolves in ~90ms, because the
  cursor crosses many rows at once and anything slower feels laggy.
- Loading is a skeleton shaped like the content, with a slow shimmer. Never a
  spinner for work under 400ms.
- `prefers-reduced-motion: reduce` collapses durations to ~0 rather than setting
  `animation: none` — entrances animate opacity from 0, so cancelling them
  outright would leave content invisible. Test this; it is easy to get backwards.

---

## Charts

Chart series colour lives in `src/pages/commonComponents/chart_palette.js`, **not**
in `_tokens.scss`. This is a deliberate exception to rule 1: ApexCharts runs
shading maths on the colour strings it is given, so it cannot accept
`var(--token)`. The module is the source; the values below are the record.

### Identity — categorical, fixed order, never cycled

Slot 0 is always "yours". A competitor never lands on slot 0.

| Slot | Value | |
|---|---|---|
| 0 | `#1a3cff` | the user's own series — same as `--accent` |
| 1 | `#009798` | teal, OKLCH 0.60 / 0.13 / 195 |
| 2 | `#8a2a7a` | plum, OKLCH 0.46 / 0.16 / 335 |

Generated in OKLCH at fixed lightness and chroma, then validated: lightness band,
chroma floor, contrast ≥ 3:1, and colour-vision separation (worst adjacent ΔE 14.9
under deuteranopia against a target of 8).

An all-neutral palette was tried first and fails — accent plus `--ink-2` plus
`--ink-4` gives a chroma of 0.011–0.014 against a 0.10 floor, so the series become
indistinguishable. That is why two new hues exist.

### Magnitude — rank bands, one hue stepped

`#91b0f4` `#6c94f4` `#4875f3` `#2551f3` `#1738ce` `#0f299c`

Ordinal data gets one hue, light to dark. Monotone lightness, adjacent ΔL ≥ 0.06,
light-end contrast 2.16:1.

This replaced `["#CF4343","#81e7a0","#f3b52e","#e4566e","#349afb","#1a3cff"]` — a
rainbow encoding an ordinal scale, which additionally spent the reserved `--up`
green and `--down` red on something that has no direction. A competitor is not a
direction.

### Non-series marks

Annotation pins `--ink-4` — they are chrome, not data, and must not consume an
identity slot. Axes `--ink-3`, labels `--ink`.

---

## Sanctioned exceptions

Colour outside the token set is allowed in exactly these places, and nowhere else:

1. **Google's SERP colours** — `#1a0dab`, `#202124`, `#4d5156`, `#5f6368`,
   `#70757a` — where the app renders a realistic search-result preview. Tokenising
   them would make the preview stop looking like a SERP.
2. **Third-party brand marks** — the four-colour Google "G" and similar. Never
   convert these to `currentColor`; flattening a brand mark makes it wrong.
3. **`SFRatingClrIcon`'s rating scale** — green / amber / red by rating value.
   Colour carries real information there; flattening it would lose meaning.
4. **Chart series**, per the section above.

Everything else resolves to a token.

## Known deviations, accepted for now

- `.pro-sidebar` uses `transition: all` to animate its hover-expand from 60px to
  250px. This animates `width`, against the motion rule. Overriding it makes the
  rail snap open instead of expanding, so it stands.
- Black-alpha shadow values remain in the tree; they go when the shadows do.
- `#ececef` (~417 occurrences) is used as border, background, colour and fill
  interchangeably. One mapping cannot serve all four, so it needs per-site
  judgement rather than a sweep.

---

## Elevation — correction to the original flat rule

The first pass banned shadows outright and relied on hairlines alone. Measured
against the in-house standard (`llm-monitor`, which uses `shadow-elegant` +
`bg-card/80` on cards), flat-with-hairlines reads as timid rather than restrained.

Two levels, both defined in `_tokens.scss`:

| Token | Use |
|---|---|
| `--elev-1` | cards, panels, the project list — things that sit on the page |
| `--elev-2` | things that float over it, if the MUI theme's own shadow is not used |

Low alpha on the ink hue, so it reads as depth rather than a grey halo. The rest
of the rule stands: no shadow on inputs, table rows, chips or nav items, and
never a shadow used to fake a border.

**Do not reference an elevation token that is not defined here.** `--elev-1` was
referenced from six places in two trees before it existed; `var()` on an
undefined property silently resolves to nothing, so every one of those rendered
no shadow and no error. A missing token fails silently — check it resolves.

---

## Contrast — measured, not assumed

Every colour used as text must clear **4.5:1** on `--surface` (WCAG 2.2, 1.4.3),
and every non-text mark **3:1** (1.4.11). Rank direction is *text* — a "+4"
delta, a "Dropping" label — so it is bound by 4.5:1, not 3:1.

The original status palette failed badly and shipped that way:

| Token | Was | Ratio | Now | Ratio |
|---|---|---|---|---|
| `--up` | `#12b76a` | **2.62:1** | `#0d864e` | 4.63:1 |
| `--flat` | `#98a2b3` | **2.58:1** | `#69778e` | 4.54:1 |
| `--warn` | `#dc6803` | **3.49:1** | `#be5a03` | 4.51:1 |
| `--down` | `#d92d20` | 4.83:1 | unchanged | — |

`--up` and `--flat` also failed the 3:1 non-text floor, so they were unreadable
in the one table users scan most. Each was darkened at its original hue until it
cleared the threshold — computed, not eyeballed.

**Before adding or changing any colour token, compute its ratio.** Two colours
that look fine side by side on a designer's screen routinely fail this, and the
failure is invisible until someone cannot read the number.
