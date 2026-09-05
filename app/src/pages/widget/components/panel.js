import React from "react";

/* One panel shell for the whole screen.

   The heading is the bracketed micro-label from docs/DESIGN.md rather than a
   15px card title: these are sections of one page, not eight independent cards,
   and the label is what makes them read as a single document. `action` is the
   one link a section is allowed -- the place to go to act on what it shows.

   <h3>, not <h2>: every panel now sits inside a measurement-system section
   whose band carries the <h2> (components/section_band.js). The nesting is the
   point of that band, so it has to be audible to a screen reader walking the
   headings and not only visible on the page. */

export function Panel({ label, action, className, children }) {
   return (
      <section className={"dashPanel" + (className ? " " + className : "")}>
         <div className="dashPanel__head">
            <h3 className="dashPanel__label">{label}</h3>
            {action ? <div className="dashPanel__action">{action}</div> : null}
         </div>
         {children}
      </section>
   );
}

/* docs/DESIGN.md, "Empty state": one sentence, no art. Inside a panel there is
   no room for a second primary action, so the panel's own head link is the way
   out and this is only the sentence. */
export function PanelEmpty({ children }) {
   return <p className="dashPanel__empty">{children}</p>;
}

export default Panel;
