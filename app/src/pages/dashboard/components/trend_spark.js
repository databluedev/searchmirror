import React from "react";
import { Tooltip, Zoom } from "@mui/material";

/* The Trend column: seven days of net keyword movement -- improved minus
   declined -- one mark a day, diverging about a zero line.

   Both series already ride along in the projects payload (serp/serializers.py
   sets ikw / dkw from the group's activity_level) and both arrive newest first,
   so time reads right to left until they are reversed here. Nothing new is
   fetched; the two counters beside this column are the same two arrays, read at
   index 0.

   Why net, and why marks rather than a line. project_status.js records that the
   tiles this replaces drew each counter on its own and rendered "as a 1px dark
   rule: noise shaped like data", because a counter of how many keywords moved
   is usually flat. Net movement crosses zero, so it has shape.

   Three states, and the difference between them is the whole point:

     no history at all  -- activity_level is [], which is a brand-new project.
                           Says so in words. An SVG with nothing in it looks
                           like a rendering failure, which is exactly how the
                           first version of this read on a fresh database.
     a day that is flat -- a visible --flat tick sitting on the zero line. The
                           day happened and nothing moved; that is information,
                           and it has to be drawn or it cannot be told apart
                           from a day that is missing.
     a day that moved   -- a bar above or below the line.

   Direction is carried by which side of the line a mark is on, not by colour. */

const DAYS = 7;
const BAR = 8;
const GAP = 4;
const W = DAYS * BAR + (DAYS - 1) * GAP; /* 80 */
const H = 26;
const MID = H / 2;
const REACH = MID - 1;
const MIN_BAR = 1.5;
const TICK = 2;

const count = (value) => {
   const n = Math.abs(Number(value));
   return Number.isFinite(n) ? n : 0;
};

const TrendSpark = ({ improved, declined }) => {
   const up = Array.isArray(improved) ? improved : [];
   const down = Array.isArray(declined) ? declined : [];
   const len = Math.min(DAYS, Math.max(up.length, down.length));

   /* Oldest first, so the newest day is the rightmost mark. A project with
      fewer than seven days of history keeps its marks on the right, against
      today, rather than starting the series at an arbitrary left edge. */
   const net = [];
   for (let i = len - 1; i >= 0; i--) {
      net.push(count(up[i]) - count(down[i]));
   }

   if (len === 0) {
      return (
         <Tooltip title="No movement history yet" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
            <span className="prjSpark">
               <span className="prjSrOnly">Trend</span>
               <span className="prjSparkEmpty">No history</span>
            </span>
         </Tooltip>
      );
   }

   const peak = net.reduce((max, v) => Math.max(max, Math.abs(v)), 0);
   const total = net.reduce((sum, v) => sum + v, 0);
   const offset = DAYS - len;

   const label =
      "Net movement over " +
      len +
      (len === 1 ? " day: " : " days: ") +
      (total > 0 ? "+" + total : total);

   /* The zero line spans the days that exist, not the whole frame -- a rule
      running under four empty slots claims history the project does not have. */
   const baseX = offset * (BAR + GAP);

   return (
      <Tooltip title={label} placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
         <span className="prjSpark">
            <span className="prjSrOnly">Trend</span>
            <svg width={W} height={H} viewBox={"0 0 " + W + " " + H} role="img" aria-label={label}>
               <rect className="sparkBase" x={baseX} y={MID - 0.5} width={W - baseX} height="1" />
               {net.map((value, i) => {
                  const x = (offset + i) * (BAR + GAP);
                  if (value === 0) {
                     return <rect key={i} className="sparkFlat" x={x} y={MID - TICK / 2} width={BAR} height={TICK} rx="1" />;
                  }
                  /* peak cannot be 0 here: a non-zero value is in the series. */
                  const h = Math.max(MIN_BAR, (Math.abs(value) / peak) * REACH);
                  return (
                     <rect
                        key={i}
                        className={value > 0 ? "sparkUp" : "sparkDown"}
                        x={x}
                        y={value > 0 ? MID - h : MID}
                        width={BAR}
                        height={h}
                        rx="1"
                     />
                  );
               })}
            </svg>
         </span>
      </Tooltip>
   );
};

export default TrendSpark;
