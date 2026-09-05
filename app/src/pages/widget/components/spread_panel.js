import React from "react";
import { Panel, PanelEmpty } from "./panel";
import { spreadTotal } from "../dashboard_data";

/* POSITION SPREAD -- where the whole keyword set sits.

   Rank band is SEQUENTIAL, so it is one hue stepped dark to light, best to
   worst, and never five colours: five hues would encode an ordered quantity as
   unordered identity, and a rainbow in a monochrome product is the loudest
   thing on the screen. The hue is ink, which is what makes it belong here --
   an accent-blue ramp is still a wall of blue.

   The worst band is drawn hollow rather than filled. There is no ink step light
   enough to sit under --ink-4 and still be visible, and "outside the top thirty"
   is an absence rather than a quantity of anything -- so it takes the same
   outline the never-ranked mark uses. On a project with twenty-eight of thirty
   in that band the bar reads as almost entirely hollow, which is the honest
   shape of it.

   The bar alone is not the panel. A band holding one keyword out of thirty is a
   three-pixel segment, and the previous version of this shipped exactly that:
   one flat block with slivers nobody could read. Every band therefore also has
   a row with its count, so the bar carries the shape and the rows carry the
   numbers, and no band is unreadable at any distribution. */

const BANDS = [
   { key: "p1", label: "#1", step: "s1" },
   { key: "p2_3", label: "2–3", step: "s2" },
   { key: "p4_10", label: "4–10", step: "s3" },
   { key: "p11_30", label: "11–30", step: "s4" },
   { key: "beyond", label: "31+", step: "s5" },
];

export default function SpreadPanel({ spread }) {
   const total = spreadTotal(spread);

   if (total === 0) {
      return (
         <Panel label="Position spread">
            <PanelEmpty>No keyword has a position to place in a band yet.</PanelEmpty>
         </Panel>
      );
   }

   const summary = BANDS.map((band) => band.label + " " + spread[band.key]).join(", ");
   const ranked = total - spread.beyond;

   return (
      <Panel label="Position spread">
         <div className="dashSpread" role="img" aria-label={"Keywords by position band: " + summary}>
            {BANDS.map((band) =>
               spread[band.key] > 0 ? (
                  <span
                     key={band.key}
                     className={"dashSpread__seg dashSpread__seg--" + band.step}
                     style={{ width: (spread[band.key] / total) * 100 + "%" }}
                  />
               ) : null,
            )}
         </div>

         <ul className="dashBands">
            {BANDS.map((band) => (
               <li key={band.key} className="dashBand">
                  <span className={"dashBand__swatch dashSpread__seg--" + band.step} aria-hidden="true" />
                  <span className="dashBand__label">{band.label}</span>
                  <span className="dashBand__value">{spread[band.key]}</span>
               </li>
            ))}
         </ul>

         <p className="dashPanel__foot">
            {ranked} of {total} in the top 30
         </p>
      </Panel>
   );
}
