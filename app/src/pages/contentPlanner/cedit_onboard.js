import React from "react";
import "./style.scss";
import CEditOnboardInfo from "./cedit_onboard_info"

function CEditOnBoard({ projectList, fullbasedata, ...props }) {
   return (
      <>
         <section className="layout kr_layout">
            <CEditOnboardInfo regionData={props.regionData} kwdSearchDetails={props.kwdSearchDetails} refetchContentPlans={props.refetchContentPlans} />
         </section>
      </>
   );
}

export default CEditOnBoard; 
