import React from "react";

/* Visibility dial for competitor figures.

   commonComponents/pie.js paints the ring by the direction of the score's
   day-over-day change: up is #1a3cff, down is #CF4343, flat is #43CF62. Three
   hardcoded colours, and on a *competitor* the meaning is inverted -- a rival
   losing ground was drawn in alarm red while a rival standing still was drawn
   in success green. A competitor climbing is their improvement and the
   reader's problem, so none of this belongs on a hue. That file is shared with
   pages outside this feature, so rather than change it underneath them the
   competitor screens use this: one neutral ring, tokens only, direction told
   in words by <CompTrend>.

   `denominator` is not decoration. The score is computed over just the
   keywords the competitor and this project share -- two, in most seeded rows --
   so an 80 means "80 across the 4 keywords you both target", not "80 of your
   30". Printing that denominator under the number is the only thing that stops
   the figure reading as a project-wide result. */

const CIRCUMFERENCE = 2 * Math.PI * 25;

const clamp = (value) => {
   const numeric = Number(value);
   if (!Number.isFinite(numeric) || numeric < 0) return 0;
   return numeric > 100 ? 100 : numeric;
};

export function CompScoreDial({ score, measured = true, size = 65 }) {
   // "Not measured" is not zero. An unmeasured dial draws the track only and
   // says so with an em dash, so it can never be read as the best score on the
   // page or as a genuine floor.
   const pct = clamp(score);
   const offset = ((100 - pct) * CIRCUMFERENCE) / 100;

   return (
      <svg width={size} height={size} viewBox="0 0 65 65" className="compDial" role="img"
         aria-label={measured ? "Search visibility score " + Math.round(pct) + " out of 100" : "Search visibility score not measured yet"}>
         <g transform="rotate(-90 32.5 32.5)">
            <circle r={25} cx={32.5} cy={32.5} fill="transparent" strokeWidth="4px" className="compDial__track" />
            {measured && pct > 0 ?
               <circle
                  r={25} cx={32.5} cy={32.5} fill="transparent" strokeWidth="4px"
                  strokeDasharray={CIRCUMFERENCE} strokeDashoffset={offset}
                  strokeLinecap="round" className="compDial__value"
               />
            : null}
         </g>
         <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle"
            className="compDial__label">
            {measured ? Math.round(pct) : "—"}
         </text>
      </svg>
   );
}

/* Direction in words, in neutral ink. "climbing" on a competitor row is bad
   news for the reader and must not arrive dressed in --up green; --up/--down
   are reserved for the reader's own rank direction. */
export function CompTrend({ current, previous, measured = true, subject = "competitor" }) {
   if (!measured || !Number.isFinite(Number(previous)) || Number(previous) < 0) {
      return <span className="compTrend compTrend--none">not measured yet</span>;
   }
   const delta = Number(current) - Number(previous);
   const word = delta > 0 ? "climbing" : delta < 0 ? "slipping" : "holding";
   return (
      <span className="compTrend">
         {subject === "you" && delta !== 0 ?
            <span className={"compTrend__mark " + (delta > 0 ? "is-up" : "is-down")} aria-hidden="true" />
         : null}
         {word}
      </span>
   );
}

/* A count that could not be measured must not print 0. */
export function CompCount({ value, measured = true }) {
   return <span>{measured && Number.isFinite(Number(value)) ? value : "—"}</span>;
}

export default CompScoreDial;
