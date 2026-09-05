import React, { useMemo } from "react";
import { isRanked, rankLabel, rankSortKey } from "../../../utils/rank_state";
// import { useHistory } from "react-router-dom";

// import Skeleton from '@mui/material/Skeleton';

// import { Tooltip, Box } from "@mui/material";
// import Zoom from '@mui/material/Zoom';

import {PositionTool, ExactURLTool} from "./tool_tip"; 

import DataTable from 'react-data-table-component';

import { FillArrow,ExactDomainIcon, GoLinkIcon, GoOverviewPageIcon, SortingIcon } from "../../commonComponents/icons";
import {convertSiteUrl } from "../../common_fun";
import KWTypoerror from "../components/keyword_typo_error";
import { AppTooltip, Tsk, Csk } from "../../commonComponents/parts";
import { KnowMore } from "../../../utils/external_link";
import { Tooltip, useMediaQuery, Zoom } from "@mui/material";


const NoData = () => { 
   return (
      <div className="gd-table-empty text-center">
         <p className="ls-table-empty-body">No keyword matches this view for the selected period.</p>
      </div>
   );
};
//
// const SkeletonColor = "var(--surface-2)";
// const ToggleSkeletonColor = "var(--surface-2)";

function TrendingTable({ toggleCleared, tag, grdresult, grdfullresult, tableUpdate, tabledataUpdate, handleRowSelected, selectedRowIds, updatefullpage, keywordpageroute, canSelectKeywords }) {

   /* Same defect the list table had, in the other view: 32 + 48 + 300 put RANK
      at x=397 on a 390px screen, so the grid showed a column of keyword names
      and no positions at all until you scrolled the card sideways. The two
      per-row action buttons (open in Google, rank history) drop on a phone --
      both are on the keyword's own page, which the chevron at the end of the
      row reaches -- and KEYWORD gives up the rest. */
   const narrow = useMediaQuery("(max-width:575.98px)");
   // const history = useHistory();


   // const snippetFeatures = (sValue) => {
   //    if(sValue.length > 0){
   //       return(
   //             <>
   //             {sValue.includes('slrs')===true ?
   //                <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a sitelink"} TransitionComponent={Zoom} >
   //                   <span className="cursorNO"> <SFLinkIcon /> </span>
   //                </Tooltip>
   //             : null }
   //             {sValue.includes('twrs')===true ?
   //                <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has twitter pack"} TransitionComponent={Zoom} >
   //                   <span className="cursorNO"> <SFTwitterIcon /> </span>
   //                </Tooltip>
   //             : null }
   //             {sValue.includes('lcrs')===true ? 
   //                <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a local pack"} TransitionComponent={Zoom} >
   //                   <span className="cursorNO " > <SFLocalPackIcon /> </span>
   //                </Tooltip>
   //             : null }
   //             {sValue.includes('imrs')===true ?
   //                <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has an image pack"} TransitionComponent={Zoom} >
   //                   <span className="cursorNO "> <SFImageIcon /> </span>
   //                </Tooltip>
   //             : null }
   //             { sValue.includes('vdrs')===true  ? 
   //                <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a video pack"} TransitionComponent={Zoom} >
   //                   <span className="cursorNO "> <SFVideoPackIcon /> </span>
   //                </Tooltip>
   //             : null }
   //             {sValue.includes('nwrs')===true ?
   //                <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has news pack"} TransitionComponent={Zoom} >
   //                   <span className="cursorNO " > <SFNewsIcon /> </span>
   //                </Tooltip>
   //             : null }
   //             {sValue.includes('rqrs')===true  ? 
   //                <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has related questions"} TransitionComponent={Zoom} >
   //                   <span className="cursorNO " > <SFRelatedQuestionIcon /> </span>
   //                </Tooltip>
   //             : null }
   //             {sValue.includes('mprs')===true ?
   //                <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a map pack"} TransitionComponent={Zoom} >
   //                   <span className="cursorNO" > <SFLocationIcon /> </span>
   //                </Tooltip>
   //             : null }
   //             </>
   //         );
   //       }
   //    else
   //       return(
   //          <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={<div className="lh18x"><div> {"The result has a featured snippet"} </div> <a href={global.featursnipt} target="_blank" rel="noopener noreferrer" className="f12x m-l5 fw600 text-underline fM pClr">know more</a> </div>} TransitionComponent={Zoom} >
   //             <span className=""> <FeatureSnptIcon /> </span>
   //          </Tooltip>
   //       )
   // }

   /// COLUMN DECLARATION
   // One action per row: the chevron into the keyword. Google page, rank
   // history, favourite and the flag are all on the keyword's own page.
   const columns = useMemo(() => [
      {
         id: 'keyword',
         name: 'KEYWORD',   
         style : { display: "grid", overflow: "hidden", padding: "0px" },
         sortable: true,
         selector: row => row.KW,
         minWidth: narrow ? "120px" : "300px",
         maxWidth: narrow ? "210px" : undefined,
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center justify-content-between py-2" style={{ minWidth: 0 }}>
            
               <div className="d-flex align-items-center overflow-hidden" style={{ minWidth: 0 }}>
                  <div className="d-flex align-items-center" style={{ minWidth: 0 }}>
                    { row.KW ?
                      <div className="" style={{ minWidth: 0 }}>
                        <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={row.KW} TransitionComponent={Zoom} >
                           <div style={narrow ? { maxWidth: "100%" } : undefined} className={"text-truncate m-r5 m-b5 cursorP "+ (((row.kwas !== '' && row.kwas !== '-') || row.cnn) ? "maxW240x" : "maxW260x")} onClick={() => keywordpageroute(row)}>
                             {row.KW}
                           </div>
                        </Tooltip>
                        <div className="d-flex" style={{ minWidth: 0 }}>
                        { row.edm ? <div className="d-flex m-r5"><ExactDomainIcon /></div> : null }
                           <div style={narrow ? { maxWidth: "100%" } : undefined} className={"text-truncate f12x lh14x newlightTxtClr "+(((row.kwas !== '' && row.kwas !== '-') || row.cnn) ? "maxW200x" : row.edm ? "maxW220x" : "maxW240x")}> 
                              {convertSiteUrl(row.SR)}
                           </div>
                        <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={<ExactURLTool url={row.SR} exact={row.edm} />} TransitionComponent={Zoom} >
                           <a href={row.SR} className="lh20x d-flex align-items-center" target="_blank" rel="noopener noreferrer">
                           <GoLinkIcon height={10} width={10} className={"m-l5 newlightTxtClr"} />
                           </a>
                        </Tooltip>
                        </div>
                      </div>
                     : 
                      <div className="m-l8">
                        <div className="maxW200x text-truncate m-r5 m-b5">
                          <Tsk width={140} />
                        </div>
                        <div className={"maxW200x text-truncate fsES lh14x "+ (row.edm ? "pClr" : "lightTxtClr")}>
                          <Tsk width={190} />
                        </div>
                      </div>
                    }
                  </div>
               </div>
               <div className="d-flex align-items-center" style={{ flex: "0 0 auto" }}>
                  <div className="d-flex m-r5">
                     <div className="keywordCheckIcon mr-2 redIcon">                                      
                        { ((row.kwas !== '' && row.kwas !== '-') || row.cnn) ?    
                            <AppTooltip className="red md p-2 typoerrortooltip" dimension="14"
                              title={
                                <div className="p-1">
                                { (row.kwas !== '' && row.kwas !== '-') &&
                                    <KWTypoerror row={row} tableUpdate={tableUpdate} updatefullpage={updatefullpage} />
                                }
                                { row.cnn && 
                                    <>
                                       {(row.kwas !== '' && row.kwas !== '-') ? <div className="brdBottom m-t10 m-b5" /> : null}
                                       <div className="text-center lh22x">
                                           <span>{"Fix "}</span>
                                           <span><b className="pClr f-wg600 fM mx-1">{"'"+row.KW+"'"}</b></span>
                                           <span>{" keyword cannibalization issues ! "} </span>
                                           <span className="fM pClr mx-1"> <KnowMore href={global.cannbltnurl} className="f-xsm ml-1 f-wg600 fM text-underline pClr" /></span>
                                       </div>
                                    </>
                                }
                                </div>
                            } 
                            place="top"
                            />
                        : null
                        }
                     </div>
                  </div>
               </div>
            </div>
         )
      },{
         id: "rank",
         name: "RANK",
         right: true,
         sortable: true,
         style : { padding: '0px' },
         minWidth: narrow ? "50px" : "60px",
         maxWidth: narrow ? "58px" : "80px",
         selector: (row) => rankSortKey(row),
         cell: (row, index, column, id) => (
            (row.RK && (row.RK).length > 0) ?
               <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={ <PositionTool row={row}/> } TransitionComponent={Zoom}>
                  <div className="d-flex align-items-center justify-content-end gap-1">
                     { isRanked(row) ?
                        <span className="fM">{row.RW}</span>
                     :
                        <span className="fM lightgray">{rankLabel(row, true)}</span>
                     }
                     <div className={(row.RK[0] < row.RK[1] ? 'arrow green': row.RK[0] > row.RK[1] ? 'arrow red': 'd-none')}>
                        <FillArrow className="d-flex" />
                     </div>
                  </div>
               </Tooltip>
            :
               <Tsk width={30} />
        ),
      },{
         id: "brk",
         name: "BEST",
         right: true,
         minWidth: narrow ? "50px" : "60px",
         maxWidth: narrow ? "58px" : "96px",
         sortable: true,
         style : { padding: '0px' },
         //
         selector: (row) => row.brk,
         cell: (row, index, column, id) => (
            (row.RK && row.RK.length > 0 && row.brk > 0) ?
               <span className="fM">{row.brk}</span>
            : (row.RK && row.RK.length > 0 && row.brk === 0) ?
               <span className="fM lightTxtClr">{'-'}</span>
            : <Tsk width={30} /> 
         ),
      },
      // {
      //    name: "SERP",
      //    minWidth: "40px",
      //    maxWidth: "50px",
      //    style : { padding: "0px" },
      //    cell: (row, index, column, id) => (
      //     <>
      //       { row.RK && row.RK.length > 0 ?
      //           row.rvw || row.fds || row.knw || row.ads || row.snp.length > 0 ? 
      //             <div className="d-flex align-items-center FSnptcolumn" style={{gap: "3px"}}>
      //                {row.rvw ?
      //                   <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={row.trg !== "-" ? <>You have {row.trg} star ratings</> : "Reviews found"} TransitionComponent={Zoom} >
      //                      <span className=""> <SFRatingClrIcon value={row.trg} /> </span> 
      //                   </Tooltip>
      //                : null}
      //                {row.ads !== false && (row.ads==="Ain" || row.ads==="Atb" || row.ads==="At" || row.ads==="Ab") ? 
      //                   <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={row.ads === "Ain" ? "You are in Google Ads" : row.ads === "Atb" ? "Ads found above & below the fold" : row.ads === "At" ? "Ads found above the fold" : row.ads === "Ab" ? "Ads found below the fold" : ""} TransitionComponent={Zoom} >
      //                      <span className=""> {row.ads === "Ain" ? <AdsIcon color="var(--accent)" /> : row.ads === "Atb" ? <AdTopBottomIcon /> : row.ads === "At" ? <AdTopIcon /> : row.ads === "Ab" ? <AdbottomIcon /> : null} </span>
      //                   </Tooltip>
      //                : null }

      //                {row.fds ?  
      //                   <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={<div className="lh18x"><div> {row.fs_s  === "yes" ? "You are in the featured snippets" : "The result has a featured snippet"} </div> <a href={global.featursnipt} target="_blank" rel="noopener noreferrer" className="f12x m-l5 fw600 text-underline fM pClr">know more</a> </div>} TransitionComponent={Zoom} >
      //                      <span className="">  {row.fs_s  === "yes" ? <FeatureSnptIcon color="var(--accent)" /> : <FeatureSnptIcon /> } </span>
      //                   </Tooltip>
      //                : null}

      //                {row.knw ? 
      //                   <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a knowledge panel"} TransitionComponent={Zoom} >
      //                      <span className=""> <SFKnwlgPanelIcon /> </span>
      //                   </Tooltip>
      //                : null}

      //               {(row.snp.length > 0 && row.fsc < 2) &&
      //                   snippetFeatures(row.snp.slice(0,Number(2)-Number(row.fsc)) )
      //               }

      //               {Number(row.fsc)+Number(row.snp.length) > 2 &&
      //                   <div className="moreIcon">
      //                     <ClickAway height={14}>
      //                       <Box
      //                         sx={{
      //                           display: "grid",
      //                           gridTemplateColumn: "1fr 1fr 1fr 1fr 1fr 1fr",
      //                           gap: "7px",
      //                         }}
      //                         className="d-flex flex-wrap align-items-center"
      //                       >
      //                         {row.rvw ?
      //                            <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={row.trg !== "-" ? <>You have {row.trg} star ratings</> : "Reviews found"} TransitionComponent={Zoom} >
      //                               <span className=""> <SFRatingClrIcon value={row.trg} /> </span> 
      //                            </Tooltip>
      //                         : null}
      //                         {row.ads !== false && (row.ads==="Ain" || row.ads==="Atb" || row.ads==="At" || row.ads==="Ab") ? 
      //                            <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={row.ads === "Ain" ? "You are in Google Ads" : row.ads === "Atb" ? "Ads found above & below the fold" : row.ads === "At" ? "Ads found above the fold" : row.ads === "Ab" ? "Ads found below the fold" : ""} TransitionComponent={Zoom} >
      //                               <span className=""> {row.ads === "Ain" ? <AdsIcon color="var(--accent)" /> : row.ads === "Atb" ? <AdTopBottomIcon /> : row.ads === "At" ? <AdTopIcon /> : row.ads === "Ab" ? <AdbottomIcon /> : null} </span>
      //                            </Tooltip>
      //                         : null }

      //                         {row.fds ?  
      //                            <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={<div className="lh18x"><div> {row.fs_s  === "yes" ? "You are in the featured snippets" : "The result has a featured snippet"} </div> <a href={global.featursnipt} target="_blank" rel="noopener noreferrer" className="f12x m-l5 fw600 text-underline fM pClr">know more</a> </div>} TransitionComponent={Zoom} >
      //                               <span className="">  {row.fs_s  === "yes" ? <FeatureSnptIcon color="var(--accent)" /> : <FeatureSnptIcon /> } </span>
      //                            </Tooltip>
      //                         : null}

      //                         {row.knw ? 
      //                            <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a knowledge panel"} TransitionComponent={Zoom} >
      //                               <span className=""> <SFKnwlgPanelIcon /> </span>
      //                            </Tooltip>
      //                         : null}

      //                         {(row.snp.length > 0) &&
      //                             snippetFeatures(row.snp)
      //                         }
      //                       </Box>

      //                     </ClickAway> 
      //                   </div>
      //               }
      //             </div>
      //          :
      //             <span className="d-flex justify-content-center fM lightTxtClr ">{'NA'}</span>
      //       :
      //           <Tsk width={60} />
      //       }
      //     </>
      //   ),
      // }
      {
         id: "lnk",
         name: "",
         minWidth: "35px",
         maxWidth: "35px",
         style : { justifyContent:'start', paddingLeft: "3px",paddingRight:'0px' },
         cell: (row, index, column, id) => (
            <div className="d-flex justify-content-center">
               {row.KW ?
                  <div className="nw_circleArrow cursorP" onClick={() => keywordpageroute(row)}>
                     <GoOverviewPageIcon />
                  </div>
               : <Csk width={24} height={24} className="flag" />}
            </div>
        ),
      },

   // eslint-disable-next-line react-hooks/exhaustive-deps
   ], [grdresult, grdfullresult, narrow]); 
   
   /// COMMENT
   const paginationComponentOptions = {
      rowsPerPageText: 'Per page', 
      rangeSeparatorText: 'of', 
      noRowsPerPage: false,
   }

   // console.log("test escond ", props.tag)

   // const Checkbox = React.forwardRef(({ onClick, ...rest }, ref) =>
   //    {
   //    return(
   //         <>
   //             <div className="form-check pb-5" style={{ backgroundColor: '' }}>
   //                 <input 
   //                     type="checkbox"
   //                     className="form-check-input"
   //                     style={{ height: '20px', width: '20px' }}
   //                     ref={ref}
   //                     onClick={ onClick }
   //                     {...rest}
   //                 />
   //                 <label className="form-check-label" id="booty-check" />
   //             </div>
   //         </>
   //    )
   // })

   // console.log("gridCheckedTag tag name",grdresult)

   
   
   return (
      <>         
         <div className="gd_rdt_CustomTable"> 
               <DataTable
                  columns={columns}
                  data={grdresult}
                  keyField="key"
                  sortIcon={<SortingIcon />} 
                  defaultSortFieldId={"position"}
                  defaultSortAsc={true} 
                  selectableRows={canSelectKeywords}
                  selectableRowDisabled={(row) => !row.KW}
                  // selectableRowsComponent={Checkbox}
                  onSelectedRowsChange={handleRowSelected}
                  clearSelectedRows={toggleCleared}
                  pagination={grdresult.length > 25}
                  paginationPerPage={25}
                  paginationRowsPerPageOptions={[10,25,50,100]}
                  // paginationServer={ grdresult.length === kwCount ? false : true}
                  // paginationTotalRows={totalRows}
                  paginationComponentOptions={paginationComponentOptions}
                  noDataComponent={<NoData />} 
               />
            
         </div>
      </>
   )
}

export default TrendingTable;
