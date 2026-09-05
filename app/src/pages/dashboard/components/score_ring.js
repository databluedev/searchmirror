import React from "react";

/* Search Visibility Score as a ring.

   The score is a percentage -- pages/commonComponents/pie.js has always clamped
   it to 0-100 -- and a bounded index is the one data shape a ring is honestly
   for. It sits in a fixed track in the row (.prjScore), so the arcs line up down
   the list and can be read against each other without reading the digits.

   The ring is ink and the track is a hairline, in both directions. The old Pie
   coloured the whole ring blue / red / green by yesterday's delta, which spent
   the reserved rank colours and the accent on a quantity that has no direction
   of its own; direction is stated separately, by an arrow and a number.

   `known` separates "this project scores zero" from "this project has never
   been scored". serp/serializers.py returns ss = 0 for a group with an empty
   score_meter, so a brand-new project and a genuinely bottomed-out one arrive
   as the same number -- and the row's own tooltip already says "not available"
   for the second case, which a bold 0 in the ring flatly contradicted.

   Geometry is drawn in a 36-unit box at 1:1, so a stroke unit is a pixel.
   Colour is applied through CSS classes, never through fill= or stroke=
   attributes -- var() does not resolve inside an SVG presentation attribute. */

const R = 15;
const CIRC = +(2 * Math.PI * R).toFixed(2);

const ScoreRing = ({ value, known }) => {
   const raw = Number(value);
   const pct = Number.isFinite(raw) ? Math.min(100, Math.max(0, Math.round(raw))) : 0;
   /* --ring-c is what the entrance keyframe animates from: a full circumference
      of offset is an undrawn ring, so the arc sweeps out to its own length. */
   const offset = +(CIRC - (CIRC * pct) / 100).toFixed(2);

   return (
      <span
         className={known ? "ringMeter" : "ringMeter ringMeterEmpty"}
         style={{ "--ring-c": String(CIRC) }}
      >
         <svg viewBox="0 0 36 36" aria-hidden="true" focusable="false">
            <circle className="ringTrack" cx="18" cy="18" r={R} fill="none" strokeWidth="3" />
            {known ?
               <circle
                  className="ringFill"
                  cx="18"
                  cy="18"
                  r={R}
                  fill="none"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeDasharray={CIRC}
                  strokeDashoffset={offset}
                  transform="rotate(-90 18 18)"
               />
               : null}
         </svg>
         <span className="ringValue">{known ? pct : "–"}</span>
      </span>
   );
};

export default ScoreRing;
