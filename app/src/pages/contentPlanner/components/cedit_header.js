import React, { useEffect, useState } from "react";
import { Title, Para, AppTooltip, AppIconButton } from "../../commonComponents/parts";
import ManageWidget from "./cedit_manage_widget"
import { BacklinkIcon } from "../../commonComponents/icons";

function CEditHeader({ children, ...props }) {
   return (
      <header>
         <div className="d-flex justify-content-between flex-wrap gap-3">
            <div className="d-flex flex-wrap gap-3 align-items-center">
               <span>
                  <AppIconButton
                     Icon={<BacklinkIcon />}
                     onclick={() => { window.history.back(); }}
                  />
               </span>
               <div>
                  <>
                     <Title class="wd-title">Content Planner</Title>
                  </>
                  <Para class="wd-subTitle m-b0 d-flex align-items-center lh14x">Create and optimize your content with real-time NLP analysis</Para>
               </div>
            </div>
            {props.canManage ? <div className="d-flex align-items-center twoButton addkeyhdr dashboard flex-[0_0_auto] gap-[0.6rem]">
               <div className="min-w-[174px] max-w-[174px] flex-[0_0_auto]">
                  <ManageWidget {...props} />
               </div>
            </div> : null}
         </div>
      </header>
   );
}

export default CEditHeader;
