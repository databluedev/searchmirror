import React, { useState } from "react";
import "../style.scss";

import { Grid, Tooltip, MenuItem, Zoom } from "@mui/material";

import { AdsIcon, AdbottomIcon,AdTopIcon, FilterIcon, TagIcon } from "../../commonComponents/icons";


import { Para, AppTooltip, TextLg, Text, Tsk } from "../../commonComponents/parts";
import ClickAway from "../../commonComponents/click_away";
import SiteMark from "../../commonComponents/site_mark";

export const faviconfun = (url) =>{
    return <SiteMark domain={url} width={18} height={18} />
}

/// Ads tooltip TOOL
export function AdTooltip({ad}) {
   return (
      <a target="_blank" href={ad.lk} rel="noopener noreferrer">
      <div className="d-flex align-items-center cursorP">
         <span className="logobox m-r10 p-1">
            {faviconfun(ad.dm)}
         </span>
          { ad.lk.length > 40 ?
            <span>
              <div className="f12x pClr f-semi lh16x text-left cursorP">{ad.lk.slice(0, ad.lk.length/2)}</div>
              <div className="f12x pClr f-semi lh16x text-left cursorP">{ad.lk.slice(ad.lk.length/2, ad.lk.length)}</div>
            </span>
          :
            <span className="f12x pClr f-semi lh16x text-left cursorP">{ad.lk}</span>
          }
      </div> 
      </a>
   );
};

/// Compititor tooltip TOOL
export function CompTooltip({cmp}) {
   return (
      <a target="_blank" href={cmp.lk} rel="noopener noreferrer">
        <div className="d-flex align-items-center cursorP">
            <span className="logobox m-r10 p-1">
               {faviconfun(cmp.dn)}
            </span>
            { cmp.lk.length > 40 ?
              <span>
                <div className="f12x pClr f-semi lh16x text-left cursorP">{cmp.lk.slice(0, cmp.lk.length/2)}</div>
                <div className="f12x pClr f-semi lh16x text-left cursorP">{cmp.lk.slice(cmp.lk.length/2, cmp.lk.length)}</div>
              </span>
            :
              <span className="f12x pClr f-semi lh16x text-left cursorP">{cmp.lk}</span>
            }
        </div> 
      </a>
   );
};

//
export default function KWCompetitors({ adlist, adsLoading, comp, comptrLoading, allcompsget }) {

   const [comptype, setComptype] = useState('tp');

   const Improved = (
      <div>
        <Para>
        Get to know your competitors ranking for this keyword.
        </Para>
      </div>
    );
 
   const ComGoogle = (
      <div>
      <Para>
      Find out all your competitors who run ads for the same keyword.
      </Para>
   </div>
   );
   
   const AdsImg = (ads) => { 
      if(ads === "11")
         return <AdsIcon color="#0a0a0a" />
      else if(ads === "10")
         return <AdTopIcon color="#0a0a0a" />
      else if(ads === "01")
         return <AdbottomIcon color="#0a0a0a" />
      else
         return <span> </span>
   } 

   const comptype_chng = (type) => {
      if(type !== comptype){
         setComptype(type);
         if (!comp[type]){
            allcompsget(type);
         }
      }
   }

   return (
      <>
         <div className="m-t30">
           <div className="box m-b20 compbox">
            <div className="d-flex align-items-center justify-content-between">
             <TextLg class="fB lineHAuto m-b15 m-t5 d-flex align-items-center gap-1">
               Competitors
               <div className="d-flex">
                  <AppTooltip place="bottom-end" title={Improved} />
               </div>
             </TextLg>
             <div>
               <ClickAway 
                  childclassName="CompList" 
                  // parent={ <AppIconButton class={"messageIcon kwselect"} Icon={<FilterIcon />} /> }
                  parent={ <div className="compfilterIcon"> <FilterIcon /> </div> }
               >
                  <MenuItem className={comptype === "tp" ? "primaryActive" : "primaryHover"} onClick={() => comptype_chng('tp')} >
                     <div className="d-flex justify-content-between align-items-center">
                        <TagIcon />
                        <div className="m-r20 m-l10"> Top 10 </div>
                     </div>
                  </MenuItem>
                  <MenuItem className={comptype === "bf" ? "primaryActive" : "primaryHover"} onClick={() => comptype_chng('bf')} >
                     <div className="d-flex justify-content-between align-items-center">
                        <TagIcon />
                        <div className="m-r20 m-l10"> Before you </div>
                     </div>
                  </MenuItem>
                  <MenuItem className={comptype === "ar" ? "primaryActive" : "primaryHover"} onClick={() => comptype_chng('ar')} >
                     <div className="d-flex justify-content-between align-items-center">
                        <TagIcon />
                        <div className="m-r5 m-l10"> After you </div>
                     </div>
                  </MenuItem>
               </ClickAway> 
             </div>
            </div>

            {(comptrLoading === false && comp[comptype] && comp[comptype].length > 0) ?
               <Grid container spacing={3} className="m-b15 m-t0 p-l10 compdata">
                  {comp[comptype].map((cmp, i) => 
                     <Grid item xs={12} lg={6} md={6} sm={6} key={i.toString()} className="px-3 p-t10 p-b10">
                        <Text class="mb-0 d-flex align-items-center">
                           <span className="fB w15x text-right">{cmp.rn}</span>{" "}
                           <a target="_blank" href={"https://www."+cmp.dn+"/"} rel="noopener noreferrer">
                              <span className="logobox m-l10 m-r10 p-1">
                                 {faviconfun(cmp.dn)}
                              </span>
                           </a>
                           <a target="_blank" href={cmp.lk} rel="noopener noreferrer">
                           <Tooltip classes={{ tooltip: "Tltpsmall text-center d-flex align-items-center" }} TransitionComponent={Zoom} placement="top" title={ <CompTooltip cmp={cmp} /> } > 
                              <div>
                                 {cmp.dn}
                              </div>
                           </Tooltip>
                           </a>
                        </Text>
                     </Grid>
                  )}
               </Grid>
            : (comptrLoading === false && comp[comptype] && comp[comptype].length === 0) ?
               /* Both empty lines here were .PentanaryClr, which is $pentanaryClr
                  -- #ececef, the hairline colour -- used as body text. That is
                  1.16:1 on white against the 4.5:1 floor in docs/DESIGN.md, so
                  the sentence explaining why the panel was blank was itself
                  invisible. They also stated only the absence; which slice of
                  the SERP is being asked for is the filter above, and that is
                  what the reader needs to know to make sense of "none". */
               <div className="kwEmptyPanel">
                  <p className="kwEmptyPanel__body">
                     {comptype === "bf" ? "Nothing ranked above you on the last check of this keyword."
                        : comptype === "ar" ? "Nothing ranked below you on the last check of this keyword."
                        : "No other domains were recorded in the top 10 on the last check of this keyword."}
                  </p>
               </div>
            :
               <Grid container spacing={3} className="m-b15 m-t0 p-l10 compdata">
                  {[1,2,3,4,5,6,7,8,9,10].map((data, i) => 
                     <Grid item xs={12} lg={6} md={6} sm={6} key={i.toString()} className="px-3 p-t10 p-b10">
                       <Text class="mb-0 d-flex align-items-center">
                           <span className="fB w15x  "><Tsk width={18} /></span>{" "}
                           <Tsk width={24} height={24} className="m-l10 m-r10 d-flex" />
                           <Tsk width={160} className="" />
                       </Text>
                     </Grid>
                  )}
               </Grid>
            } 
           </div>

           <div className="box adsbox">
             <TextLg class="fB lineHAuto m-b15 m-t5 d-flex align-items-center gap-1">
               Competitors in Google Ads
               <div className="d-flex">
                 <AppTooltip place="bottom-end" title={ComGoogle} />
               </div>
             </TextLg>

            { (adsLoading === false && adlist.length > 0) ? 
               <Grid container spacing={3} className="m-t0 p-l10 adsdata">
                  {adlist.map((ad, i) => 
                     <Grid item xs={12} lg={4} md={6} sm={6} key={i.toString()} className="px-3 p-t10 p-b10">
                       <Text class="mb-0 d-flex align-items-center">
                        <span className="m-r10"> {AdsImg(ad.ps)} </span>
                        <a target="_blank" href={ad.lk} rel="noopener noreferrer">
                           <Tooltip classes={{ tooltip: "Tltpsmall text-center d-flex align-items-center" }} TransitionComponent={Zoom} placement="top" title={ <AdTooltip ad={ad} /> } > 
                           <div>
                              <span>{ad.dm}</span> 
                              {ad.rc ? <span className="newlable m-l10 f-semi">New</span> : null}
                              {/*data === 2 ? <span className="status m-l5" /> : null*/}
                           </div>
                           </Tooltip>
                        </a>
                       </Text>
                     </Grid>
                  )}
               </Grid>
            : (adsLoading === false && adlist.length === 0) ?
               <div className="kwEmptyPanel">
                  <p className="kwEmptyPanel__body">
                     No paid results were shown for this keyword on the last check.
                  </p>
               </div>
            :
               <Grid container spacing={3} className="m-t0 p-l10 adsdata">
                  {[1,2,3,4,5].map((data, i) => 
                     <Grid item  xs={12} lg={4} md={6} sm={6}  key={i.toString()} className="px-3 p-t10 p-b10">
                        <Text class="mb-0 d-flex align-items-center">
                            <Tsk width={18} height={18} className="m-r10 d-flex" />
                            <Tsk width={160} className="" />
                        </Text>
                     </Grid>
                  )}
               </Grid>
            } 
           </div>
         </div>
      </>
   );
}
