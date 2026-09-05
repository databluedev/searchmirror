import React from "react";
import { isRanked } from "../../../utils/rank_state";
// import { VolTool } from "../../common_fun";   

/// DIFFERENCE TOOL
export function DiffTool({ value }) {
   return (
      <div className="wd-pos-block d-flex align-items-center">
         <div className="defaultClr"> Yesterday, it was </div>
         <div className="f-semi primaryClr m-l5 f-14x"> {value} </div>
      </div>
   );
};

/// POSITION TOOL
export function PositionTool({ row }) {
   return (
      <div className="wd-pos-block d-flex align-items-center">
         <div className="defaultClr"> Yesterday, the position was </div>
         <div className="fM pClr m-l5">
            {row.RK.length < 1 ?
               "Not Available"
               :
               row.RK[1] === 0 ?
                  "Not Ranked"
                  :
                  row.RK[1]
            }
         </div>
      </div>
   );
};

/// SEARCH VOLUME TOOL   
export function SearchVolumeTool({ lvol, lmonth, pvol, pmonth }) {
   return (
      <div className="">
         <div className="lh18x f12x d-flex align-items-center">
            <div className="defaultClr"> Search Volume on {pmonth}: <span className="pClr f-semi">{pvol.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span> </div>
            {/*pmonth !== "" ?
               <div className="f-semi pClr m-l5"> ({pmonth})</div>
            : null */}
         </div>
         <div className="lh18x f12x d-flex align-items-center m-t5">
            <div className="defaultClr"> Search Volume on {lmonth}: <span className="pClr f-semi">{lvol.toLocaleString(undefined, { maximumFractionDigits: 2 })}</span> </div>
            {/*lmonth !== "" ?
               <div className="f-semi pClr m-l5"> ({lmonth}) </div>
            : null */}
         </div>
      </div>
   );
};

/// EXACT URL TRACKING 
export function ExactURLTool({ url, exact }) {
   return (
      <div className="">
         {exact ?
            <div className="brdBottom p-b5 m-b5 pClr fM text-left">Tracking Exact URL</div>
            : null}
         <a href={url} className="lh20x" target="_blank" rel="noopener noreferrer">{url}</a>
      </div>
   );
};

/* Reconstructs an earlier position from the current one and a delta.
   That arithmetic is only meaningful when there IS a current position: it
   used to be guarded on the out-of-range sentinel, which asked "is this
   that magic number" rather than "did this keyword rank", and answered
   wrongly for a keyword
   whose check failed. Guarded on the state now, and when there is no current
   position the tooltip says so instead of printing |delta| as though it were
   a rank. */
export function DayDiffTool({ row, day }) {
   var i = 0;
   var tooltipText = "";
   const ranked = isRanked(row);
   const delta = day === "1d" ? row.OD : day === "7d" ? row.SD : row.XD;
   const when = day === "1d" ? "yesterday" : day === "7d" ? "A week ago" : "Two weeks ago";

   if (!ranked) {
      tooltipText = day === "1d"
         ? "It has no current position, so yesterday's cannot be worked out from it."
         : `${when}'s position cannot be worked out without a current one.`;
   } else if (delta > 0) {
      i = delta + row.RW;
      tooltipText = day === "1d" ? `It was ${i} yesterday` : `${when}, it was ${i}.`;
   } else if (delta < 0) {
      i = row.RW - Math.abs(delta);
      tooltipText = day === "1d" ? `It was ${i} yesterday` : `${when}, it was ${i}.`;
   } else {
      i = row.RW;
      tooltipText = day === "1d" ? `It was ${i} yesterday` : `${when}, it was ${i}.`;
   }
   return (
      <div className="wd-pos-block d-flex align-items-center">
         <div className="defaultClr">{tooltipText}</div>
         {/* <div className="f-semi primaryClr m-l5 f-14x"> {i} </div> */}
      </div>
   );
};

export function GSCToolTip({ row, type }) {
   var tooltipText = "";
   if (row.lw_clks && type === "clks") {
      tooltipText = row.lw_clks + " clicks "
   }
   else if (row.lw_imps && type === "imps") {
      tooltipText = row.lw_imps +  " impressions "
   }
   else {
      tooltipText = ""
   }
   return (
      tooltipText !== "" && 
      <div className="wd-pos-block d-flex align-items-center">
         <span className="pClr f-semi p-1">{tooltipText}</span>
         <div className="defaultClr">{row.gsc_dr}</div>
      </div>
   );
}; 