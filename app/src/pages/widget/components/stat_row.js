import React from "react";
import { keywordTotal } from "../dashboard_data";

/* The stat row -- five numbers, one strip, always the same five.

   One bordered strip divided by hairlines rather than five cards. Five cards
   with five borders and five shadows for five numbers is more furniture than
   content, and docs/DESIGN.md separates by hairline rather than by box for
   exactly this case.

   Nothing here is a chart. This row exists to be read in one pass, before the
   eye reaches anything that needs interpreting, so a tile is a label, a number,
   and -- on the one number that has a direction -- a signed delta.

   Every tile keeps its slot on every project. A project with nothing ranking
   still has a RANKED tile; it reads 0/30, which is a finding. */

/* `visibility.delta` and `attention[].delta` share a name and have different
   units -- one is a score difference, the other a difference of positions --
   but BOTH follow "positive is good", deliberately, which is why the same
   up/down test renders both. The attention one was flipped earlier today after
   it was caught painting rank declines green. Do not "correct" either of them
   to match the other's arithmetic: they already agree on the only thing that
   matters here, and making the arithmetic match would invert one of them. */
function Delta({ value }) {
   if (value === null || value === 0) return null;
   return (
      <span className={"dashStat__delta " + (value > 0 ? "isUp" : "isDown")}>
         {value > 0 ? "+" : "−"}
         {Math.abs(value)}
      </span>
   );
}

/* A signed change that is NOT a rank direction, and therefore NOT --up/--down.

   This renders the change in how many keywords are tracked. Adding keywords is
   not an improvement: the visibility score divides by every tracked keyword, so
   adding ten unranked ones DROPS the score without a single ranking having
   moved. A green "+10" sitting beside a falling score would read as "things
   improved" at the exact moment the score fell because of it -- it would not
   merely be decorative, it would assert the opposite of what happened.

   So it takes --ink-3, and it is a separate component from <Delta> rather than
   a flag on it. Sharing the component is how it would later acquire the
   colours: someone tidying "for consistency" changes one branch and this
   inherits it silently. Two components cannot be unified by accident.

   docs/DESIGN.md: --up and --down are rank direction and nothing else, ever.
   The same rule keeps the competitor trend in ink. */
function Shift({ value }) {
   if (value === null || value === undefined || value === 0) return null;
   return (
      <span className="dashStat__shift">
         {value > 0 ? "+" : "−"}
         {Math.abs(value)}
      </span>
   );
}

/* `note` is a qualifier on the figure, not a second figure: muted, smaller, and
   on the same baseline, so the row stays one tile-height. It exists for the one
   number on this row whose denominator changes what it means. */
function Stat({ label, value, note, delta, shift }) {
   return (
      <div className="dashStat">
         <span className="dashStat__label">{label}</span>
         <span className="dashStat__line">
            <span className="dashStat__value">{value}</span>
            {delta === undefined ? null : <Delta value={delta} />}
            {shift === undefined ? null : <Shift value={shift} />}
            {note ? <span className="dashStat__note">{note}</span> : null}
         </span>
      </div>
   );
}

/* One decimal, and an em dash rather than a number when nothing was measured.

   Gated on the DENOMINATOR, not on the value. A project with no ranked keyword
   has no average position and the API sends 0.0 for it, and 0.0 in a column
   where lower is better reads as the best score on the page -- the same trap
   `competitors[].keywords` exists to close on the other side of the screen.

   The denominator is then PRINTED, which is the whole fix. Unranked keywords are
   excluded from this mean rather than counted as 100 or 101 the way most of the
   industry does it, so on project 4 it reads 3.0 while the project ranks for two
   keywords out of thirty -- flattering, until you can see the "over 2". The
   score tile already carries the conventional "you are nowhere" reading (it
   divides by every keyword, so project 4 scores 4); this tile answers the
   complementary question, where the site places when it places at all. The two
   only contradict each other while the denominator is hidden. */
const position = (ranked, value) => {
   if (ranked !== null && ranked <= 0) return "—";
   if (value === null || value <= 0) return "—";
   return value.toFixed(1);
};

/* How many keywords currently hold a position.

   `visibility.ranked` is the field for this and is used whenever it is there.
   The fallback sums the four ranked buckets, and it deliberately does NOT
   subtract `visibility.unranked` from the total, which is what this tile did
   first: `unranked` counts keywords that have NEVER ranked, so a keyword that
   ranked last week and has since dropped out is in neither set and the
   subtraction over-reports what ranks today. The two agree on all three seeded
   projects by coincidence -- none of them has a dropped-out keyword -- so the
   error would have surfaced first in production, the first time a customer lost
   a ranking. The bucket sum is right by construction. */
const rankedCount = (data) => {
   const v = data.visibility;
   if (v.ranked !== null) return v.ranked;
   const s = data.spread;
   return s.p1 + s.p2_3 + s.p4_10 + s.p11_30;
};

export default function StatRow({ data }) {
   const v = data.visibility;
   const m = data.movement;
   /* The five buckets always sum to the keyword count, so this one is safe. */
   const total = keywordTotal(data);
   const ranked = rankedCount(data);
   /* Strictly true. `comparable` is three-valued and null means the API did not
      say -- which is not permission to state a change over a window we cannot
      confirm exists. */
   const comparable = m.comparable === true;

   return (
      <div className="dashStats">
         <Stat label="Visibility" value={v.score === null ? "—" : v.score} delta={v.delta} />
         {/* The change is scoped to the movement window and to nothing else.
             A count change measured over a different period, sitting beside a
             7-day score delta two tiles to its left, would answer a question
             nobody asked and imply a causation between two figures that do not
             share a denominator. When there is no window -- one snapshot, so
             `comparable` is false -- the API sends no delta and the tile is the
             bare count, which is the honest reading rather than a zero. */}
         <Stat label="Keywords" value={total} shift={comparable ? m.keywordsDelta : null} />
         <Stat label="Ranked" value={ranked + "/" + total} />
         <Stat label="Top 10" value={v.top10} />
         <Stat
            label="Avg pos"
            value={position(v.ranked, v.avgPosition)}
            note={v.avgPosition !== null && v.avgPosition > 0 && ranked > 0 ? "over " + ranked : ""}
         />
      </div>
   );
}
