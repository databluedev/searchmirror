import React from "react";

/* docs/DESIGN.md, "Loading": a --surface-2 skeleton in the shape of the content
   it replaces. Not a spinner -- the dashboard this replaces held a centred
   spinner that never resolved when the project list was empty, and a spinner
   says nothing about what is coming.

   The header is not skeletonised: which project this is comes from the project
   list the shell already has, so it is real from the first frame and only the
   panels are waiting.

   The four rows below are the real proportions, not an approximation. The
   layout does not depend on the payload, so the skeleton can be the exact shape
   of what is about to replace it. */

function PanelBones({ rows }) {
   return (
      <div className="dashPanel dashSkel__panel">
         <div className="dashSkel__bar" style={{ width: "120px" }} />
         {Array.from({ length: rows }).map((row, i) => (
            <div key={i} className="dashSkel__bar dashSkel__bar--row" style={{ width: i % 2 ? "68%" : "84%" }} />
         ))}
      </div>
   );
}

export default function DashSkeleton() {
   return (
      <div className="dashSkel" aria-busy="true">
         {/* .prjSrOnly is the app's visually-hidden class (_surfaces.scss). */}
         <p className="prjSrOnly">Loading this project&rsquo;s dashboard</p>
         <div className="dashSkel__bar dashSkel__bar--strip" />
         <div className="dashRow dashRow--wide">
            <PanelBones rows={5} />
            <PanelBones rows={5} />
         </div>
         <div className="dashRow dashRow--even">
            <PanelBones rows={4} />
            <PanelBones rows={4} />
         </div>
         <div className="dashSkel__bar dashSkel__bar--strip" />
      </div>
   );
}
