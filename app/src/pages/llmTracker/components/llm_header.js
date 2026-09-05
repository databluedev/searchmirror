import React, { useEffect, useState } from "react";
import { Title, Para, AppTooltip, AppIconButton } from "../../commonComponents/parts";
import ManageWidget from "../../commonComponents/llm/llm_manage_widget"
import { BacklinkIcon } from "../../commonComponents/icons";
import LLMRunAnalysis from "./llm_run_analysis";
import LLMSuggestPrompts from "./llm_suggest_prompts";

function LLMHeader({ children, ...props }) {
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
                     <Title class="wd-title">Geo Citations</Title>
                  </>
                  <Para class="wd-subTitle m-b0 d-flex align-items-center lh14x">Monitor Your Brand Mentions Across AI Platforms</Para>
               </div>
            </div>
            {/* Widths and wrapping live in style.scss under .geoHeaderActions:
                these three controls measure ~470px, which does not fit a 390px
                phone, and the row was clipped with "Add prompts" off-screen. */}
            {props.canManage ? <div className="d-flex align-items-center geoHeaderActions">
               {/* Nothing else in the product triggers processing, so without
                   this a prompt sits at INIT forever. */}
               <LLMRunAnalysis onDone={props.refetchLLMPrompts} />
               <LLMSuggestPrompts refetchLLMPrompts={props.refetchLLMPrompts} />
               <div className="geoHeaderActionAdd">
                  <ManageWidget {...props} />
               </div>
            </div> : null}
         </div>
      </header>
   );
}

export default LLMHeader;
