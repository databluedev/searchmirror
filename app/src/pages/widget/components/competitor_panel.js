import React from "react";
import { Link } from "react-router-dom";
import { Panel, PanelEmpty } from "./panel";

/* COMPETITORS -- a table, not a chart.

   It was six horizontal bars reading 3, 3, 2, 2, 2, 2. At that range a bar
   chart earns nothing: the longest bar was 97% of the panel and the shortest
   65%, so a 3 and a 2 looked alike, and the chart occupied half a screen to say
   less than the numbers do. Values need a shape before a chart is worth drawing
   and six values between two and three have none.

   Three facts per row instead of one bar: who they are, how many of this
   project's keywords they rank for, and how well. That is also where the
   coverage gap ended up -- "who holds the keywords you do not" is this table,
   read next to the never-ranked count in the panel beside it.

   No colour at all. The domain names distinguish the rows, and docs/DESIGN.md
   forbids spending colour on a distinction a label has already made. --up and
   --down would be actively wrong here even on a direction: they mean "rank
   improved" and "rank declined", and the subject of every row on this table is
   the competitor, so a rival climbing is their improvement and the reader's
   problem. Green would read as good news. */

/* `keywords` gates `avgPosition`, not the other way round. A domain that ranks
   for nothing arrives with avg_position 0.0, and 0.0 in a column where lower is
   better is the best score on the panel -- it would sort a dead competitor
   straight to the top. */
const position = (row) => {
   if (row.keywords <= 0) return "—";
   if (row.avgPosition === null || row.avgPosition <= 0) return "—";
   return row.avgPosition.toFixed(1);
};

/* `trend` is deliberately not rendered. Three columns is the whole table, and
   on real data every rival is "holding" -- six rows repeating one word add a
   column of noise and no decision. It is also the least trustworthy field here:
   "holding" computed from a single snapshot is the absence of a comparison
   rather than the result of one, which `trend_comparable` exists to say and
   which a one-word column has no room to. The competitors page carries it. */

export default function CompetitorPanel({ competitors }) {
   return (
      <Panel
         label="Competitors"
         action={
            <Link className="dashLink" to="/competitors">
               All competitors
            </Link>
         }
      >
         {competitors.length === 0 ? (
            <PanelEmpty>
               No competitor is being tracked for this project yet, so there is nothing to compare your positions
               against.
            </PanelEmpty>
         ) : (
            <table className="dashTable">
               <thead>
                  <tr>
                     <th scope="col">Domain</th>
                     <th scope="col" className="isNum">
                        Keywords
                     </th>
                     <th scope="col" className="isNum">
                        Avg pos
                     </th>
                  </tr>
               </thead>
               <tbody>
                  {competitors.map((row) => (
                     <tr key={row.domain}>
                        <td>
                           <span className="dashTable__domain">{row.domain}</span>
                        </td>
                        <td className="isNum">{row.keywords > 0 ? row.keywords : "—"}</td>
                        <td className="isNum">{position(row)}</td>
                     </tr>
                  ))}
               </tbody>
            </table>
         )}
      </Panel>
   );
}
