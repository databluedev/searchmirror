# SearchMirror brand assets

The source of truth for the mark. Anything that renders the logo — favicons,
the marketing header, transactional email, PDF reports, the chart watermark —
derives from these files. Change the mark here and regenerate downstream;
do not redraw it at the call site.

| File | What it is | Where it goes |
|---|---|---|
| `logo-mark.svg` | The bare mark, `currentColor`, no ground | Anywhere the mark sits on a surface that already has a colour. Not below ~20px. |
| `logo-tile.svg` | The mark in `--ink` on a `--paper` tile, 22% corner radius | Favicons, app icons, anything under ~20px |
| `wordmark.svg` | Mark + logotype lockup, `currentColor`, text converted to outlines | Marketing header and footer, email, report covers |
| `preview.png` | Contact sheet of all three at working sizes | Reference only; the one file here that is deliberately unlinked |

## The mark

Two chevrons facing away from each other around a shared lens. It is a mirror
before it is an S: the same shape twice, reflected through the centre.

The vector was traced from the master raster
`app/src/assets/images/logo-dark.png`, which stays in the repo as the reference
the app's own `LogoMark` component loads. The trace measures **IoU 0.9897**
against it — visually identical, and the difference is a sub-pixel hairline on
the outer edges.

## Rules

- **The mark is monochrome, including the tile.** `logo-mark.svg` and
  `wordmark.svg` inherit `currentColor` so one file serves a light ground and an
  inverted footer. `logo-tile.svg` cannot — an SVG cannot read a CSS custom
  property — so it writes out `--ink` (`#0f0f10`) and `--paper` (`#ffffff`).
  Those are the only hardcoded colours in the kit and they track
  `app/src/assets/styles/modules/_tokens.scss`.

- **No accent blue in the mark.** An earlier revision put a white mark on an
  `--accent` tile. Two reasons it is not that:
  `_tokens.scss` files `--accent` under "meaning -- the only colours allowed to
  appear", and a permanent logo ground turns the one action colour into
  furniture; and it measures worse in the case it was supposed to help.
  Contrast against the two grounds a browser tab strip actually uses:

  | | light strip `#dee1e6` | dark strip `#202124` |
  |---|---|---|
  | `--ink` mark on its own white tile | **19.16:1** | **19.16:1** |
  | white tile edge against the strip | 1.31:1 | 16.10:1 |
  | white mark on an `--accent` tile | 5.11:1 | **2.40:1** |

  On a white active tab the tile edge vanishes and the mark floats — that is
  fine and intended, it still holds 19.16:1. The accent tile is the one that
  fails, at 2.40:1 on a dark strip, under even the 3:1 non-text floor.

  `tests/test_product_surface.py::test_favicon_uses_black_mark_on_white_background_without_blue_fallback`
  holds this. Change the test first if the decision ever changes.

- **The one case that would need a filled ground** is a *maskable* launcher icon
  or a social preview image, where the platform crops to its own shape and a
  white ground disappears into a white page. Neither exists today. Add a
  separate accent-ground file for it rather than recolouring these.
- **The logotype is Space Grotesk 600**, set as outlines so no file here
  depends on a webfont. "Search" sits at 55% opacity and "Mirror" at full —
  the same two-tone treatment the app shell and the marketing header use.
- **Below about 20px, use the tile.** The counters between the chevrons and
  the lens close up, and the mark stops reading. The 16px favicon frame drops
  the lens entirely and grows the mark to 62% of the tile, because at that size
  the lens is 1.3px across and reads as a smudge.

## Rasters generated from these files

`app/public/favicon.{ico,svg}`, `app/public/logo{192,512}.png` and
`landing/public/favicon.{ico,svg}` are the tile.

Every one of them is reachable, which is the rule: **no orphan rasters in
`public/`.** `app/index.html` links `/favicon.svg?v=3`; `manifest.json` lists
`favicon.svg`, `logo192.png` and `logo512.png`; `favicon.ico` is reached by the
browser's implicit `/favicon.ico` request. A 64px `favicon.png` used to sit here
with nothing pointing at it and has been deleted — `public/` is copied verbatim
into the build and served, so an unreferenced file there is published without
anyone looking at it. That is exactly how a 396x124 wordmark belonging to the
commercial product this was adapted from survived as an extensionless
`app/public/logo192`, shipping someone else's mark inside the build. If you add
a raster here, reference it or do not add it.

**None of the manifest icons is declared `maskable`.** A maskable icon is
cropped to the platform's own shape, so this white ground would read as a blank
tile on a light launcher. The fix is a separate file with a filled ground, not
recolouring these — see the rule above. `backend/static/uploads/Logo_color.png`
(email and PDF) and `app/src/assets/logo/tracker_light_logo.png` (chart
watermark) are the lockup.

Two of those have a **fixed** pixel size that is load-bearing, so check before
you resize them:

- `tracker_light_logo.png` must stay **396x124**. Four page stylesheets place it
  as a centred `background-image` with no `background-size`, so its intrinsic
  size is its rendered size.
- `Logo_color.png` is **792x248**, twice the 396x124 box the mail templates lay
  out, so it stays sharp on a high-DPI client. The two templates that place it
  without a width carry an explicit one.

## Regenerating the rasters

The PNGs and the `.ico` were produced from the two SVGs here — the tile drawn at
each icon size natively rather than downscaled from one big render, and the
logotype set in Space Grotesk 600 from `app/public/fonts/SpaceGrotesk-latin.woff2`
and converted to outlines. Reproducing them needs `pillow`, `numpy` and
`fonttools[woff]`; none of that is a runtime dependency of the project, so no
build step here is wired into CI. If the mark changes, regenerate every file in
the table above together — a half-updated set is worse than an old one.
