/**
 * Chart palette — the single source of truth for ApexCharts series colours.
 *
 * WHY THIS FILE EXISTS
 * docs/DESIGN.md says no hex literal belongs outside _tokens.scss and the MUI
 * theme, but ApexCharts cannot take `var(--token)`: it runs shading maths on the
 * strings it is given (gradients, hover states), which produces garbage from a
 * CSS function. So the chart scale has to exist as concrete values somewhere.
 * It lives here, once, instead of in 33 places.
 *
 * These values now DO live in _tokens.scss as `--chart-band-1..6`, and this is
 * the mirror of that source. Change them there first, then here. The stylesheet
 * side reads the tokens directly (search-volume and difficulty tags); only
 * ApexCharts needs these concrete strings.
 *
 * WHAT REPLACED WHAT
 * `#763de1`, a violet with no place in the design system, was used 33 times.
 * In most of them it was decorative: the *fill* under a line whose *stroke* was
 * already `--accent`, so the violet was never carrying meaning. The competitor
 * chart additionally painted a rival's series in `#CF4343` — the same red
 * DESIGN.md reserves for "rank declined" — so a colour that means "worse" was
 * being spent on "somebody else".
 *
 * RULES THIS ENCODES
 * - Rank direction is `--up` / `--down` / `--flat` and nothing else ever gets
 *   those. They are absent from `series` on purpose: a competitor is not a
 *   direction.
 * - `series` is IDENTITY, assigned in fixed order and never cycled. Slot 0 is
 *   always "yours", which is why it is the accent.
 * - `rankBands` is MAGNITUDE, so it is one hue stepped light -> dark, not a
 *   rainbow. The old array ran red -> green -> amber -> pink -> blue, which
 *   both mixed the reserved rank-direction colours into a non-directional scale
 *   and encoded an ordered quantity as unordered identity.
 *
 * VALIDATION (skill: dataviz, scripts/validate_palette.js, surface #ffffff)
 *   series    -> lightness band PASS, chroma floor PASS, CVD separation PASS
 *                (worst adjacent dE 14.9 deutan, target >= 8), normal-vision
 *                floor PASS (28.8, gate 15), contrast PASS (all >= 3:1)
 *   rankBands -> monotone lightness PASS, adjacent dL PASS (all >= 0.06),
 *                light-end contrast PASS (2.16:1, floor 2:1), single hue PASS
 *                (spread 1 degree)
 * Re-run the validator before changing any value here.
 */

// Identity. Fixed order, never cycled. Slot 0 is always the user's own series.
// 0: --accent          the user
// 1: teal   OKLCH 0.60 / 0.13  / 195   a competitor
// 2: plum   OKLCH 0.46 / 0.16  / 335   a second competitor
const series = ["#1a3cff", "#009798", "#8a2a7a"];

// Magnitude. One hue (the accent's, 265.7 degrees) stepped light -> dark, so a
// stacked bar reads as a ramp: palest = Not Ranked, darkest = First Position.
const rankBands = ["#91b0f4", "#6c94f4", "#4875f3", "#2551f3", "#1738ce", "#0f299c"];

// Non-series marks. Annotation pins are chrome, not data, so they take ink --
// they must not consume an identity slot.
const note = "#9aa0a8";  // --ink-4
const axis = "#6b6e76";  // --ink-3
const label = "#0f0f10"; // --ink

const CHART = { series, rankBands, note, axis, label };

export default CHART;
export { series, rankBands, note, axis, label };
