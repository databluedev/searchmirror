import React, { useEffect, useState } from "react";
import { Para, Title, AppTooltip, SmallText, TextLg, Text, Tsk } from "../../commonComponents/parts";
import { Grid, Tooltip } from "@mui/material";

import Zoom from '@mui/material/Zoom';
import CompScoreDial, { CompTrend, CompCount } from "./comp_score_dial";
import SiteMark from "../../commonComponents/site_mark";

const Yours = (
   <div>
      <Para class="m-b0">
         Number of keywords marked on featured snippets, Ads and the number of keywords with review ratings.
      </Para>
   </div>
);
const Tracker = (
   <div>
      <Para class="m-b0">
         Search Visibility Score for each competitor, over the keywords you both
         track. Each tracked keyword contributes according to its current Google
         position. First position has the most weight; an unranked keyword
         contributes zero. The result is normalized to a score out of 100.
      </Para>
   </div>
);
const Activity = (
   <div>
      <Para class="m-b0">
         Here's  the data of the same keywords your competitors are ranking for. You can observe the number of improved and declined competitors' keywords, and also the number of your competitors' keywords ranking on 1st position in Google's SERP.
      </Para>
   </div>
);

function CompetitorOverview(props) {
   const [data, setData] = useState({
      allData: {},
      age: null,                // COMPLETE LIST
   });
   var { allData, age } = data;

   useEffect(() => {
      setData({ ...data, allData: props.data, age: props.age })

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [props.data]);


   return (
      <>
         <section className="projectCard noHover m-b30">
            <Grid container spacing={2}>
               <Grid item xs={12} md={12} lg={5} xl={5}>
                  <div className="d-flex align-items-center gap-3 mobColumn">
                     <div className="whiteBorderBtn p-2 border-0">
                        {Object.keys(allData).length === 0 ?
                           <Tsk height={35} width={35} />
                           :
                           <SiteMark domain={allData.mdn} className="bdr-4x" width={35} height={35} />
                        }
                     </div>
                     <div className="whiteCard w-100">
                        <div className="d-flex justify-content-between align-items-center brdBottom m-b15 p-b10 ">
                           <TextLg class="fB mb-0 lineHAuto">
                              Activity
                              <span className="m-l5">
                                 <AppTooltip place="bottom-end" title={Activity} />
                              </span>
                           </TextLg>
                        </div>
                        <Grid container spacing={1} style={{ marginTop: '26px', marginBottom: '26px' }}>
                           <Grid item xs={4} md={4}>
                              <div className="status bg-transparent p-0">
                                 <Text class="mb-2 d-flex align-items-center gap-1">
                                    <span className="lineHTen">Improved</span>
                                 </Text>
                                 {/* age === 0 means the competitor has no score history yet -- that is
                                     "not measured", which CompCount renders as an em dash. It
                                     used to fall into the skeleton branch and spin for ever. */}
                                 {Object.keys(allData).length === 0 ?
                                    <Tsk width={30} height={26} className="my-1 d-flex align-items-center gap-2" />
                                    :
                                    <Tooltip
                                       title={<>Yesterday, it was {allData.myik >= 0 ? allData.myik : <span className="newlightTxtClr fM">not available</span>}</>}
                                       TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
                                       <div>
                                          <Title class="my-1 d-flex align-items-center gap-2">
                                             {/* The delta here was the COMPETITOR's improved
                                                 count minus YOUR yesterday, drawn beside your
                                                 own figure: allData.ik - allData.myik, where
                                                 every other panel on the page pairs m* with
                                                 my*. Nothing on screen said the arrow belonged
                                                 to a different domain than the number. */}
                                             <CompCount value={allData.mik} measured={age > 0} />
                                          </Title>
                                       </div>
                                    </Tooltip>
                                 }
                              </div>
                           </Grid>
                           <Grid item xs={4} md={4}>
                              <div className="status bg-transparent p-0">
                                 <Text class="mb-2 d-flex align-items-center gap-1">
                                    <span className="lineHTen">Declined</span>
                                 </Text>

                                 {/* age === 0 means the competitor has no score history yet -- that is
                                     "not measured", which CompCount renders as an em dash. It
                                     used to fall into the skeleton branch and spin for ever. */}
                                 {Object.keys(allData).length === 0 ?
                                    <Tsk width={30} height={26} className="my-1 d-flex align-items-center gap-2" />
                                    :
                                    <Tooltip
                                       title={<>Yesterday, it was {allData.mydk >= 0 ? allData.mydk : <span className="newlightTxtClr fM">not available</span>}</>}
                                       TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
                                       <div>
                                          <Title class="my-1 d-flex align-items-center gap-2">
                                             <CompCount value={allData.mdk} measured={age > 0} />
                                          </Title>
                                       </div>
                                    </Tooltip>
                                 }
                              </div>
                           </Grid>
                           <Grid item xs={4} md={4}>
                              <div className="status bg-transparent p-0">
                                 <Text class="mb-2 d-flex align-items-center gap-1">
                                    <span className="lineHTen lineH13">First Position</span>
                                 </Text>
                                 {/* age === 0 means the competitor has no score history yet -- that is
                                     "not measured", which CompCount renders as an em dash. It
                                     used to fall into the skeleton branch and spin for ever. */}
                                 {Object.keys(allData).length === 0 ?
                                    <Tsk width={30} height={26} className="my-1 d-flex align-items-center gap-2" />
                                    :
                                    <Tooltip
                                       title={<>Yesterday, it was {allData.myfp >= 0 ? allData.myfp : <span className="newlightTxtClr fM">not available</span>}</>}
                                       // title={"Yesterday it was 10"} 
                                       TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>

                                       {/* // <Tooltip title={"Yesterday it was "+allData.myfp} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}> */}
                                       <div>
                                          <Title class="my-1 d-flex align-items-center gap-2">
                                             <CompCount value={allData.mfp} measured={age > 0} />
                                          </Title>
                                       </div>
                                    </Tooltip>
                                 }
                              </div>
                           </Grid>
                        </Grid>
                     </div>
                  </div>
               </Grid>
               <Grid item xs={12} md={12} lg={3} xl={3}>
                  <div className="whiteCard">
                     <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
                        <TextLg class="fB mb-0 lineHAuto">
                           Search Visibility Score
                           <span className="m-l5">
                              <AppTooltip place="bottom-end" title={Tracker} />
                           </span>
                        </TextLg>
                     </div>
                     <div
                        className="d-flex justify-content-between align-items-center position-relative"
                        style={{ minHeight: "58px", margin: '20px 0' }}
                     >
                        <div>
                           {Object.keys(allData).length === 0 ?
                              <Tsk height={20} width={70} />
                              :
                              <Tooltip
                                 title={<>Yesterday, it was {allData.myss >= 0 ? allData.myss : <span className="newlightTxtClr fM">not available</span>}</>}
                                 placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
                                 <div>
                                    <CompTrend current={allData.mss} previous={allData.myss} measured={age > 1} subject="you" />
                                 </div>
                              </Tooltip>
                           }
                        </div>
                        <div className="compBest">
                           {Object.keys(allData).length === 0 ?
                              <Tsk height={20} width={50} />
                              :
                              <SmallText class="fB d-flex align-items-center">
                                 <span className="m-r5 mb-0 txtClr"> Best: {(age > 0 && allData.mbss >= 0) ? Math.round(allData.mbss) : <span className="newlightTxtClr">&mdash;</span>}</span>
                              </SmallText>
                           }
                        </div>
                        <div className="compPie text-center">
                           <CompScoreDial score={allData.mss} measured={Object.keys(allData).length > 0 && age > 0} />
                           {props.sharedKeywords > 0 ?
                              <SmallText class="compDial__scope d-block">
                                 over {props.sharedKeywords} shared keyword{props.sharedKeywords === 1 ? "" : "s"}
                              </SmallText>
                           : null}
                        </div>
                     </div>
                  </div>
               </Grid>
               <Grid item xs={12} md={12} lg={4} xl={4}>
                  <div className="whiteCard">
                     <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
                        <TextLg class="fB mb-0 lineHAuto">
                           Yours
                           <span className="m-l5">
                              <AppTooltip place="bottom-end" title={Yours} />
                           </span>
                        </TextLg>
                     </div>

                     <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
                        <div className="d-flex align-items-center w55pg gap-1"> Feature Snippet </div>
                        <div className="fB d-flex align-items-center w25pg justify-content-end m-r15">
                           {Object.keys(allData).length === 0 ? <Tsk width={30} /> : allData.msn}
                        </div>
                     </div>

                     <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
                        <div className="d-flex align-items-center w55pg gap-1"> Ads </div>
                        <div className="fB d-flex align-items-center w25pg justify-content-end m-r15">
                           {Object.keys(allData).length === 0 ? <Tsk width={30} /> : allData.mad}
                        </div>
                     </div>

                     <div className="d-flex justify-content-between align-items-center p-b5">
                        <div className="d-flex align-items-center w55pg gap-1"> Review </div>
                        <div className="fB d-flex align-items-center w25pg justify-content-end m-r15">
                           {Object.keys(allData).length === 0 ? <Tsk width={30} /> : allData.mrv}
                        </div>
                     </div>
                  </div>
               </Grid>
            </Grid>

            <Para class="vs">VS</Para>

            <Grid container spacing={2}>
               <Grid item xs={12} md={12} lg={5} xl={5}>
                  <div className="d-flex align-items-center gap-3 mobColumn">
                     <div className="whiteBorderBtn p-2 border-0">
                        {Object.keys(allData).length === 0 ?
                           <Tsk height={35} width={35} />
                           :
                           <SiteMark domain={allData.dn} className="bdr-4x" width={35} height={35} />
                        }
                     </div>
                     <div className="whiteCard w-100">
                        <div className="d-flex justify-content-between align-items-center brdBottom m-b15 p-b10 ">
                           <TextLg class="fB mb-0 lineHAuto">
                              Activity
                              <span className="m-l5">
                                 <AppTooltip place="bottom-end" title={Activity} />
                              </span>
                           </TextLg>
                        </div>
                        <Grid container spacing={1} style={{ marginTop: '26px', marginBottom: '26px' }}>
                           <Grid item xs={4} md={4}>
                              <div className="status bg-transparent p-0">
                                 <Text class="mb-2 d-flex align-items-center gap-1">
                                    <span className="lineHTen">Improved</span>
                                 </Text>
                                 {/* age === 0 means the competitor has no score history yet -- that is
                                     "not measured", which CompCount renders as an em dash. It
                                     used to fall into the skeleton branch and spin for ever. */}
                                 {Object.keys(allData).length === 0 ?
                                    <Tsk width={30} height={26} className="my-1 d-flex align-items-center gap-2" />
                                    :
                                    <Tooltip
                                       title={<>Yesterday, it was {allData.yik >= 0 ? allData.yik : <span className="newlightTxtClr fM">not available</span>}</>}
                                       // title={"Yesterday it was 10"} 
                                       TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
                                       <div>
                                          <Title class="my-1 d-flex align-items-center gap-2">
                                             <CompCount value={allData.ik} measured={age > 0} />
                                          </Title>
                                       </div>
                                    </Tooltip>
                                 }
                              </div>
                           </Grid>
                           <Grid item xs={4} md={4}>
                              <div className="status bg-transparent p-0">
                                 <Text class="mb-2 d-flex align-items-center gap-1">
                                    <span className="lineHTen">Declined</span>
                                 </Text>
                                 {/* age === 0 means the competitor has no score history yet -- that is
                                     "not measured", which CompCount renders as an em dash. It
                                     used to fall into the skeleton branch and spin for ever. */}
                                 {Object.keys(allData).length === 0 ?
                                    <Tsk width={30} height={26} className="my-1 d-flex align-items-center gap-2" />
                                    :
                                    <Tooltip
                                       title={<>Yesterday, it was {allData.ydk >= 0 ? allData.ydk : <span className="newlightTxtClr fM">not available</span>}</>}
                                       // title={"Yesterday it was 10"} 
                                       TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
                                       <div>
                                          <Title class="my-1 d-flex align-items-center gap-2">
                                             <CompCount value={allData.dk} measured={age > 0} />
                                          </Title>
                                       </div>
                                    </Tooltip>
                                 }
                              </div>
                           </Grid>
                           <Grid item xs={4} md={4}>
                              <div className="status bg-transparent p-0">
                                 <Text class="mb-2 d-flex align-items-center gap-1">
                                    <span className="lineHTen lineH13">First Position</span>
                                 </Text>
                                 {/* age === 0 means the competitor has no score history yet -- that is
                                     "not measured", which CompCount renders as an em dash. It
                                     used to fall into the skeleton branch and spin for ever. */}
                                 {Object.keys(allData).length === 0 ?
                                    <Tsk width={30} height={26} className="my-1 d-flex align-items-center gap-2" />
                                    :
                                    <Tooltip
                                       title={<>Yesterday, it was {allData.yfp >= 0 ? allData.yfp : <span className="newlightTxtClr fM">not available</span>}</>}
                                       TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
                                       <div>
                                          <Title class="my-1 d-flex align-items-center gap-2">
                                             <CompCount value={allData.fp} measured={age > 0} />
                                          </Title>
                                       </div>
                                    </Tooltip>
                                 }
                              </div>
                           </Grid>
                        </Grid>
                     </div>
                  </div>
               </Grid>
               <Grid item xs={12} md={12} lg={3} xl={3}>
                  <div className="whiteCard">
                     <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
                        <TextLg class="fB mb-0 lineHAuto">
                           Search Visibility Score
                           <span className="m-l5">
                              <AppTooltip place="bottom-end" title={Tracker} />
                           </span>
                        </TextLg>
                     </div>
                     <div
                        className="d-flex justify-content-between align-items-center position-relative"
                        style={{ minHeight: "58px", margin: '20px 0' }}
                     >
                        <div>
                           {Object.keys(allData).length === 0 ?
                              <Tsk height={20} width={70} />
                              :
                              <Tooltip
                                 title={<>Yesterday, it was {allData.yss >= 0 ? allData.yss : <span className="newlightTxtClr fM">not available</span>}</>}
                                 placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
                                 <div>
                                    <CompTrend current={allData.ss} previous={allData.yss} measured={age > 1} subject="competitor" />
                                 </div>
                              </Tooltip>
                           }
                        </div>
                        <div className="compBest">
                           {Object.keys(allData).length === 0 ?
                              <Tsk height={20} width={50} />
                              :
                              <SmallText class="fB d-flex align-items-center">
                                 <span className="m-r5 mb-0 txtClr"> Best: {(age > 0 && allData.bss >= 0) ? Math.round(allData.bss) : <span className="newlightTxtClr">&mdash;</span>}</span>
                              </SmallText>
                           }
                        </div>
                        <div className="compPie text-center">
                           <CompScoreDial score={allData.ss} measured={Object.keys(allData).length > 0 && age > 0} />
                           {props.sharedKeywords > 0 ?
                              <SmallText class="compDial__scope d-block">
                                 over {props.sharedKeywords} shared keyword{props.sharedKeywords === 1 ? "" : "s"}
                              </SmallText>
                           : null}
                        </div>
                     </div>
                  </div>
               </Grid>
               <Grid item xs={12} md={12} lg={4} xl={4}>
                  <div className="whiteCard">
                     <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
                        <TextLg class="fB mb-0 lineHAuto">
                           Competitor
                           <span className="m-l5">
                              <AppTooltip place="bottom-end" title={Yours} />
                           </span>
                        </TextLg>
                     </div>

                     <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
                        <div className="d-flex align-items-center w55pg gap-1"> Feature Snippet </div>
                        <div className="fB d-flex align-items-center w25pg justify-content-end m-r15">
                           {Object.keys(allData).length === 0 ? <Tsk width={30} /> : allData.sn}
                        </div>
                     </div>

                     <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
                        <div className="d-flex align-items-center w55pg gap-1"> Ads </div>
                        <div className="fB d-flex align-items-center w25pg justify-content-end m-r15">
                           {Object.keys(allData).length === 0 ? <Tsk width={30} /> : allData.ad}
                        </div>
                     </div>

                     <div className="d-flex justify-content-between align-items-center p-b5">
                        <div className="d-flex align-items-center w55pg gap-1"> Review </div>
                        <div className="fB d-flex align-items-center w25pg justify-content-end m-r15">
                           {Object.keys(allData).length === 0 ? <Tsk width={30} /> : allData.rv}
                        </div>
                     </div>
                  </div>
               </Grid>
            </Grid>
         </section>
      </>
   );
}

export default CompetitorOverview; 
