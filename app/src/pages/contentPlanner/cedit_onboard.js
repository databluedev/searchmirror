import React from "react";
import "./style.scss";
import CEditOnboardInfo from "./cedit_onboard_info"

function CEditOnBoard({ projectList, fullbasedata, notice, ...props }) {
   /* `notice` renders INSIDE the layout section. It used to be a sibling in the
      caller's fragment, outside any `.layout` -- and `.layout` is what supplies
      `padding-top: calc(var(--shell-head-h) + var(--sp-5))` to clear the fixed
      app bar. Outside it the notice sat under the bar and was clipped, which is
      how it looked on a real deployment. llmTracker puts its notice inside the
      section for the same reason. */
   return (
      <section className="layout kr_layout">
         {notice}
         <CEditOnboardInfo regionData={props.regionData} kwdSearchDetails={props.kwdSearchDetails} refetchContentPlans={props.refetchContentPlans} />
      </section>
   );
}

export default CEditOnBoard; 
