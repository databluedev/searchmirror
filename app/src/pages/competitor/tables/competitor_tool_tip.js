import React from "react";
import { isRanked } from "../../../utils/rank_state";
// import { VolTool } from "../../common_fun";   

/// DIFFERENCE TOOL
export function DiffTool({value}) {
   return (
      <div className="wd-pos-block d-flex align-items-center">
         <div className="defaultClr"> Yesterday, it was </div>
         <div className="f-semi primaryClr m-l5 f-14x"> {value} </div>
      </div> 
   );
}; 

/// POSITION TOOL
export function PositionTool({row}) {
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
export function SearchVolumeTool({lvol, lmonth, pvol, pmonth}) {
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
export function ExactURLTool({url, exact}) {
   return (
      <div className="">
         { exact ? 
            <div className="brdBottom p-b5 m-b5 pClr fM text-left">Tracking Exact URL</div>
         : null }
            <a href={url} className="lh20x" target="_blank" rel="noopener noreferrer">{url}</a>
      </div>            
   );
};

/// FLAG TOOL MESSAGE
export function ListFlagToolMessage({row}) {
   return (
      <div className="">
         <div className="wd-flag-block">
            <div className="wd-flag-header f-semi">Tracking</div>
            <div className="wd-flag-content pClr f-semi"> {row.RG} </div>
         </div>
         <div className="brdBottom my-1"></div>
         <div className="wd-flag-block">
            <div className="wd-flag-header f-semi">Country</div>
            <div className="wd-flag-content secondaryClr f-semi"> {row.CY} </div>
         </div>
         <div className="brdBottom my-1"></div>
         <div className="wd-flag-block">
            <div className="wd-flag-header f-semi">Language</div>
            <div className="wd-flag-content secondaryClr f-semi"> {row.lng} </div> 
         </div>
         <div className="brdBottom my-1"></div>
         <div className="wd-flag-block">
            <div className="wd-flag-header f-semi">Search result</div>
            <div className="wd-flag-content secondaryClr f-semi"> {row.srs} </div>
         </div>
      </div>            
   );
}; 

/// FLAG TOOL MESSAGE
export function GridFlagToolMessage({row}) {
   return (
      <div className="">
         <div className="wd-flag-block">
            <div className="wd-flag-header f-semi">Tracking</div>
            <div className="wd-flag-content pClr f-semi"> {row.RG} </div>
         </div>
         <div className="brdBottom my-1"></div>
         <div className="wd-flag-block">
            <div className="wd-flag-header f-semi">Country</div>
            <div className="wd-flag-content secondaryClr f-semi"> {row.CY} </div>
         </div>
         <div className="brdBottom my-1"></div>
         <div className="wd-flag-block">
            <div className="wd-flag-header f-semi">Language</div>
            <div className="wd-flag-content secondaryClr f-semi"> {row.lng} </div> 
         </div>
         <div className="brdBottom my-1"></div>
         <div className="wd-flag-block">
            <div className="wd-flag-header f-semi">Platform</div>
            <div className="wd-flag-content secondaryClr f-semi"> {row.PM === "M" ? "Mobile" : "Desktop"} </div>
         </div>
      </div>            
   );
}; 


/* Works an earlier position back from the current one and a delta.

   The old version had a branch for "no current position and the delta is
   negative", which computed `100 - |delta|` -- a previous rank invented from
   a baseline the keyword was never measured against. Where there is no
   current position there is nothing to work backwards from, and the tooltip
   now says that instead of printing a number. */
export function DayDiffTool({row, day}) {
   var i = 0;
   var tooltipText = "";
   const ranked = isRanked(row);
   const delta = day === "1d" ? row.OD : day === "7d" ? row.SD : row.XD;
   const when = day === "1d" ? "yesterday" : day === "7d" ? "A week ago" : "Two weeks ago";

   if (!ranked) {
      tooltipText = day === "1d"
         ? "It has no current position, so yesterday's cannot be worked out from it."
         : `${when}'s position cannot be worked out without a current one.`;
   } else {
      i = delta > 0 ? delta + row.RW : delta < 0 ? row.RW - Math.abs(delta) : row.RW;
      tooltipText = day === "1d" ? `It was ${i} yesterday` : `${when}, it was ${i}.`;
   }
   return (
      <div className="wd-pos-block d-flex align-items-center">
         <div className="defaultClr">{tooltipText}</div>
         {/* <div className="f-semi primaryClr m-l5 f-14x"> {i} </div> */}
      </div> 
   );
}; 