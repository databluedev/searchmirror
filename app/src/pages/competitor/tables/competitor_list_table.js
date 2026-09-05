import React, { useEffect, useState, useMemo } from "react";
import { isRanked, rankLabel, rankSortKey } from "../../../utils/rank_state";
import DataTable from "react-data-table-component";
import moment from 'moment';
import { Box, Tooltip, Zoom } from "@mui/material";
import { Tsk, Csk } from "../../commonComponents/parts";
import ClickAway from "../../commonComponents/click_away";
import { DataEmptyIcon, FillArrow, MobileSmallIcon, DesktopSmallIcon, RefreshIcon, ExactDomainIcon, KWgraphIcon, GoLinkIcon, SFLinkIcon, SFTwitterIcon, SFLocalPackIcon, SFImageIcon, SFNewsIcon, SFLocationIcon, SFRelatedQuestionIcon, SFVideoPackIcon, FeatureSnptIcon, AdsIcon, AdbottomIcon, AdTopBottomIcon, AdTopIcon, SFKnwlgPanelIcon, SortingIcon } from "../../commonComponents/icons";
import {getfulldate, convertSiteUrl, VolTool, SFRatingClrIcon} from "../../common_fun";   
import Cookies from 'universal-cookie';
import { SearchVolumeTool, DayDiffTool, ExactURLTool} from "./competitor_tool_tip"; 
import KWGooglePage from "./competitor_kw_google_page";
import KWGraphModal from "./competitor_kw_graph_modal";
import CountryFlag from "../../commonComponents/country_flag";
import { KnowMore } from "../../../utils/external_link";

export default function CompetitorLstTable({ lstresult, lstfltrresult, tableUpdate, tabledataUpdate, projectbase }) {

   const [perPage, setPerPage] = useState(50);

   useEffect(() => {

      const cookies = new Cookies();
      const lstblPgSize = (cookies.get('__sp_pg_lmt__') === "50" || cookies.get('__sp_pg_lmt__') === "100") ? cookies.get('__sp_pg_lmt__') : 50
      setPerPage(parseInt(lstblPgSize))

   // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [lstresult.length]);

    
   const snippetFeatures = (sValue, rating=0) => {
      if(sValue.length > 0){
         return(
               <>
               {sValue.includes('rv') === true ?
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={rating !== "-" ? <>Competitor has {rating} star ratings</> : "Reviews found"} TransitionComponent={Zoom} >
                     <span className="cursorNO"> <SFRatingClrIcon value={rating} /> </span> 
                  </Tooltip>
               : null}
               {(sValue.includes('Ain') === true || sValue.includes('Atb') === true || sValue.includes('At') === true || sValue.includes('Ab') === true) ? 
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={sValue.includes('Ain') === true ? "Competitor found in the ad" : sValue.includes('Atb') === true ? "Ads found above & below the fold" : sValue.includes('At') === true ? "Ads found above the fold" : sValue.includes('Ab') === true ? "Ads found below the fold" : ""} TransitionComponent={Zoom} >
                     <span className="cursorNO"> {sValue.includes('Ain') === true ? <AdsIcon color="#1a3cff" /> : sValue.includes('Atb') === true ? <AdTopBottomIcon /> : sValue.includes('At') === true ? <AdTopIcon /> : sValue.includes('Ab') === true ? <AdbottomIcon /> : null} </span>
                  </Tooltip>
               : null }

               {(sValue.includes('fs0') === true || sValue.includes('fs1') === true) ?  
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={<div className="lh18x"><div> {sValue.includes('fs1') === true ? "Competitor found in the feature snippet" : "The result has a featured snippet"} </div> <KnowMore href={global.featursnipt} className="f12x m-l5 fw600 text-underline fM pClr" /> </div>} TransitionComponent={Zoom} >
                     <span className="cursorNO">  {sValue.includes('fs1') === true ? <FeatureSnptIcon color="#1a3cff" /> : <FeatureSnptIcon /> } </span>
                  </Tooltip>
               : null}

               {sValue.includes('knw') === true ? 
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a knowledge panel"} TransitionComponent={Zoom} >
                     <span className="cursorNO"> <SFKnwlgPanelIcon /> </span>
                  </Tooltip>
               : null}

               {sValue.includes('slrs')===true ?
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a sitelink"} TransitionComponent={Zoom} >
                     <span className="cursorNO"> <SFLinkIcon /> </span>
                  </Tooltip>
               : null }
               {sValue.includes('twrs')===true ?
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has twitter pack"} TransitionComponent={Zoom} >
                     <span className="cursorNO"> <SFTwitterIcon /> </span>
                  </Tooltip>
               : null }
               {sValue.includes('lcrs')===true ? 
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a local pack"} TransitionComponent={Zoom} >
                     <span className="cursorNO " > <SFLocalPackIcon /> </span>
                  </Tooltip>
               : null }
               {sValue.includes('imrs')===true ?
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has an image pack"} TransitionComponent={Zoom} >
                     <span className="cursorNO "> <SFImageIcon /> </span>
                  </Tooltip>
               : null }
               { sValue.includes('vdrs')===true  ? 
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a video pack"} TransitionComponent={Zoom} >
                     <span className="cursorNO "> <SFVideoPackIcon /> </span>
                  </Tooltip>
               : null }
               {sValue.includes('nwrs')===true ?
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has news pack"} TransitionComponent={Zoom} >
                     <span className="cursorNO " > <SFNewsIcon /> </span>
                  </Tooltip>
               : null }
               {sValue.includes('rqrs')===true  ? 
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has related questions"} TransitionComponent={Zoom} >
                     <span className="cursorNO " > <SFRelatedQuestionIcon /> </span>
                  </Tooltip>
               : null }
               {sValue.includes('mprs')===true ?
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a map pack"} TransitionComponent={Zoom} >
                     <span className="cursorNO" > <SFLocationIcon /> </span>
                  </Tooltip>
               : null }
               </>
           );
         }
      else
         return(
            <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={<div className="lh18x"><div> {"The result has a featured snippet"} </div> <KnowMore href={global.featursnipt} className="f12x m-l5 fw600 text-underline fM pClr" /> </div>} TransitionComponent={Zoom} >
               <span className=""> <FeatureSnptIcon /> </span>
            </Tooltip>
         )
   }

//
    const columns = useMemo(() => [
      {
         id: "actn",
         name: <div className="d-flex justify-content-center w-100"> ACTIONS </div>,
         center: true,
         reorder: false,
         minWidth: "65px",
         maxWidth: "65px",
         width: "65px",
         // style : { justifyContent: "flex-start" },
         // sortable: true,
         // selector: (row) => row.fv,
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center justify-content-center">
               <div className="m-r15 d-flex">
                 { row.KW ?
                 <KWGooglePage row={row} lstresult={lstresult} tabledataUpdate={tabledataUpdate} />
                 : <Tsk width={15} className="mt-1" /> }
               </div>
               <div className="d-flex">
                 { (row.RK).length > 0 ?
                     <KWGraphModal kwdata={row} projectbase={projectbase} >
                        <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} title="Rank History" placement="top"> 
                        <div className="cursorP d-flex">
                           <KWgraphIcon />
                        </div>
                        </Tooltip>
                     </KWGraphModal >
                 : <Tsk width={15} className="mt-1" /> }
               </div>
            </div>
         ),
      },
      {
         id: "kw",
         name: <div className="p-l10"> KEYWORD </div>,
         //
         minWidth : "420px",
         style : { display: "grid" },
         reorder: false,
         sortable: true,
         selector: (row) => row.KW,
         cell: (row, index, column, id) => (
            <div
              className="d-flex align-items-center justify-content-between p-l5 p-r5 py-2"
              // style={{ width: "210px" }}
            >             
              <div className="d-flex align-items-center overflow-hidden">
                <div className="d-flex align-items-center">
                  { row.io ?
                     <div className="nflag">
                        <CountryFlag
                          style={{ borderRadius: "20px" }}
                          loading="lazy"
                          className="md m-r5"
                          width="23"
                          height="23"
                          code={row.io}
                        />
                     </div>
                  : <Csk width={25} height={25} className="flag md m-r5" />}
                  { row.KW ?
                    <div>
                      <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={row.KW} TransitionComponent={Zoom}>
                        <div className="d-flex align-items-center m-b5">
                          <div className="maxW350x text-truncate m-r5 cursorP">
                            {row.KW}
                          </div>
                          { moment().format("MM-DD-YYYY") === moment(row.cd).format("MM-DD-YYYY") ? <div className="complable m-l5 h14x d-flex">New</div> : null} 
                        </div> 
                      </Tooltip>
                      <div className="d-flex">
                     { row.edm ? <div className="d-flex m-r5"><ExactDomainIcon /></div> : null }
                        <div className={"maxW310x text-truncate f12x lh14x newlightTxtClr"}>
                          {convertSiteUrl(row.SR)}
                        </div>
                     <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={<ExactURLTool url={row.SR} exact={row.edm} />} TransitionComponent={Zoom}>
                        <a href={row.SR} className="lh20x d-flex align-items-center" target="_blank" rel="noopener noreferrer">
                        <GoLinkIcon height={10} width={10} className={"m-l5 newlightTxtClr"} />
                        </a>
                      </Tooltip>
                      </div>
                    </div>
                  : 
                    <div className="">
                      <div className="maxW240x text-truncate m-r5 m-b5">
                        <Tsk width={180} />
                      </div>
                      <div className={"maxW240x text-truncate fsES lh14x "+ (row.edm ? "pClr" : "lightTxtClr")}>
                        <Tsk width={280} />
                      </div>
                    </div>
                  }
                </div>
              </div>
              <div
                className="d-flex align-items-center"
                style={{ flex: "0 0 auto" }}
              >
                <div className="d-flex m-r5">
                  <div className="keywordCheckIcon mr-2 redIcon">                                      
                      {/* ((row.kwas !== '' && row.kwas !== '-') || row.cnn) ?    
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
                                       <KnowMore href={global.cannbltnurl} className="f-xsm mx-1 f-wg600 fM text-underline pClr" />
                                    </div>
                                 </>
                              }
                              </div>
                          } 
                          place="top"
                          />
                      : null
                      */}
                  </div>
                </div>
                { row.PM === "M" ?
                  <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title="Mobile" TransitionComponent={Zoom}>
                    <div className="m-r5">
                    <MobileSmallIcon color="currentColor" /> 
                    </div>
                  </Tooltip>
                : row.PM === "D" ?
                  <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title="Desktop" TransitionComponent={Zoom}>  
                    <div className="m-r5">
                    <DesktopSmallIcon color="currentColor" /> 
                    </div>
                  </Tooltip>
                : <Tsk width={20} className="m-r5"/> } 
              </div>
            </div>  
         ),
      },
      {
         // id: "rnk",
         id: "rank",
         name: "MY RANK",
         center: true,
         sortable: true,
         class: "bgGrey",
         style : { backgroundColor: "var(--surface)" },
         minWidth: "80px",
         maxWidth: "90px",
         reorder: false,
         selector: (row) => rankSortKey({ RW: row.MRW, RS: row.MRS, RC: row.MRC, RSK: row.MRSK }),
         cell: (row, index, column, id) => (
            isRanked({ RW: row.MRW, RS: row.MRS }) ?
               <span className="fM">{row.MRW}</span>
            : (row.MRK && row.MRK.length > 0) || row.MRS ?
               <span className="fM lightgray">{rankLabel({ RW: row.MRW, RS: row.MRS, RC: row.MRC }, true)}</span>
            :
               <Tsk width={30} />
        ),
      },
      {
         // id: "rnk",
         id: "comp_rank",
         name: <div>
               <Tooltip title="Competitor's Rank" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
                  <div>
                  COMPETITOR RANK
                  </div>
               </Tooltip>
               </div>,
         center: true,
         sortable: true,
         // class: "bgGrey",
         style : { backgroundColor: "#F5F5F5" },
         reorder: false,
         minWidth: "140px",
         maxWidth: "140px",
         selector: (row) => rankSortKey(row),
         cell: (row, index, column, id) => (
            isRanked(row) ?
               <span className="fM">{row.RW}</span>
            : (row.RK && row.RK.length > 0) || row.RS ?
               <span className="fM lightgray ">{rankLabel(row, true)}</span>
            :
               <Tsk width={30} />
        ),
      },
      {
         id: "brk",
         name: <div>
            <Tooltip title="Competitor's Best Rank" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
               <div>
               BEST
               </div>
            </Tooltip>
            </div>,
         center: true,
         minWidth: "50px",
         maxWidth: "60px",
         sortable: true,
         style : { backgroundColor: "#F5F5F5" },
         reorder: false,
         // omit: (lsttblhdlst.includes('brk')) ? false : true,
         // omit: (projectbase.lth['brk']) ? false : true,
         selector: (row) => row.brnk,
         cell: (row, index, column, id) => (
            (row.RK && row.RK.length > 0 && row.brnk > 0) ?
               <span className="d-flex justify-content-center">{row.brnk}</span>
            : (row.RK && row.RK.length > 0 && row.brnk === 0) ?
               <span className="fM lightTxtClr">{'-'}</span>
            : <Tsk width={30} /> 
         ),
      },
      {
         id: "1d",
         name: <div>
               <Tooltip title="Competitor's yesterday rank difference" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
                  <div>
                  1D
                  </div>
               </Tooltip>
               </div>,
         center: true,
         minWidth: "60px",
         maxWidth: "80px",
         sortable: true,
         style : { backgroundColor: "#F5F5F5" },
         reorder: false,
         // omit: (projectage > 1 && lsttblhdlst.includes('1d')) ? false : true,
         omit: (projectbase.age > 1) ? false : true,
         selector: (row) => row.OD,
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center justify-content-center">
               { row.KW && row.OD === 0 ?
                  <span className="fM lightTxtClr">{'-'}</span>
               : row.KW ?            
                     <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={<DayDiffTool row={row} day="1d"/>} TransitionComponent={Zoom}>
                        <div className="d-flex align-items-center">
                           <span className="ml-2 fM" >{Math.abs(row.OD)}</span>   
                           <span className={(row.OD > 0 ? 'arrow green m-l5 d-flex': row.OD < 0 ? 'arrow red m-l5 d-flex': 'd-none')}>
                           <FillArrow />
                           </span>
                        </div>
                     </Tooltip>
               : <Tsk width={30} /> }
            </div>
         ),
      },
      {
         id: "7d",
         name: <div>
            <Tooltip title="Competitor's 7th day rank difference" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
               <div>
               7D
               </div>
            </Tooltip>
            </div>,
         center: true,
         minWidth: "60px",
         maxWidth: "80px",
         // maxWidth: "68px",
         style : { backgroundColor: "#F5F5F5" },
         sortable: true,
         reorder: false,
         // omit: (projectage > 7 && lsttblhdlst.includes('7d')) ? false : true,
         omit: (projectbase.age > 7) ? false : true,
         selector: (row) => row.SD,
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center justify-content-center">
              {row.KW && row.SD === 0 ?
                <span className="fM lightTxtClr">{'-'}</span>
              : row.KW ?            
                <>
                  <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={<DayDiffTool row={row} day="7d"/>} TransitionComponent={Zoom}>
                     <div className="d-flex align-items-center">
                        <span className="ml-2 fM" >{Math.abs(row.SD)}</span>   
                        <span className={(row.SD > 0 ? 'arrow green m-l5 d-flex': row.SD < 0 ? 'arrow red m-l5 d-flex': 'd-none')}>
                        <FillArrow />
                        </span>
                     </div>
                  </Tooltip>
                </>
              : <Tsk width={30} /> }
            </div>
         ),
      },
      {
         id: "15d",
         name: <div>
            <Tooltip title="Competitor's 14th day rank difference" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
               <div>
               15D
               </div>
            </Tooltip>
            </div>,
         center: true,
         minWidth: "60px",
         maxWidth: "80px",
         // maxWidth: "65px",
         style : { backgroundColor: "#F5F5F5" },
         sortable: true,
         reorder: false,
         // omit: (projectage > 15 && lsttblhdlst.includes('15d')) ? false : true,
         omit: (projectbase.age > 15) ? false : true,
         selector: (row) => row.XD,
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center justify-content-center">
              {row.KW && row.XD === 0 ?
                <span className="fM lightTxtClr">{'-'}</span>
              : row.KW ?              
                <>
                  <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={<DayDiffTool row={row} day="15d"/>} TransitionComponent={Zoom}>
                     <div className="d-flex align-items-center">
                     <span className="ml-2 fM" >{Math.abs(row.XD)}</span>   
                     <span className={(row.XD > 0 ? 'arrow green m-l5 d-flex': row.XD < 0 ? 'arrow red m-l5 d-flex': 'd-none')}>
                     <FillArrow />
                     </span>
                     </div>
                  </Tooltip>
                </>
              : <Tsk width={30} /> }
            </div>
         ),
      },
      {
         id: "fts",
         name:  <div>
            <Tooltip title="Competitor's SERP Snippets" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
               <div>
               SERP
               </div>
            </Tooltip>
            </div>,
         minWidth: "60px",
         maxWidth: "60px",
         style : { paddingLeft: "10px",backgroundColor: "#F5F5F5" },
         // omit: (projectbase.lth['fts']) ? false : true,
         // selector: (row) => row.fs_s,
         reorder: false,
         cell: (row, index, column, id) => (
            <>
               { ((row.RK).length > 0 && row.sp.length > 0) ?
                     <>
                        <Box
                           sx={{
                              display: "grid",
                              gridTemplateColumn: "1fr 1fr 1fr 1fr 1fr 1fr",
                              gap: "7px",
                           }}
                           className="d-flex p-l10 align-items-center"
                        >
                           {snippetFeatures(row.sp.slice(0,Number(2)), row.trg)}
                           {row.sp.length > 2 ?
                              <div className="moreIcon">
                                 <ClickAway height={14}>
                                    <Box
                                       sx={{
                                          display: "grid",
                                          gridTemplateColumn: "1fr 1fr 1fr 1fr 1fr 1fr",
                                          gap: "3px",
                                       }}
                                       className="d-flex flex-wrap align-items-center"
                                    >
                                      {snippetFeatures(row.sp, row.trg)}
                                    </Box>
                                 </ClickAway> 
                              </div>
                           : null }
                        </Box>
                     </>
                  : (row.RK).length > 0 ?
                     <span className="d-flex justify-content-center fM lightTxtClr m-l10">{'NA'}</span>
                  :
                     <Tsk width={70} className="m-l10" />
               }
            </>
         ),
      },
      {
         id: "sv",
         name:  <div>
            <Tooltip title="Search Volume" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
               <div>
               VOLUME
               </div>
            </Tooltip>
            </div>,
         center: true,
         minWidth: "70px",
         maxWidth: "70px",
         sortable: true,
         style : { backgroundColor: "#F5F5F5" },
         reorder: false,
         // omit: (projectbase.lth['sv']) ? false : true,
         selector: (row) => row.SV,
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center justify-content-center">
            {(row.SV !== "-" && row.SV !== "-1" && row.SV !== "init" && row.SV !== " ") ?
               <>
                  <Tooltip classes={{ tooltip: "volumeTooltip" }} placement="top" title={ <SearchVolumeTool lvol={row.SV} lmonth={row.SVM} pvol={row.PSV} pmonth={row.PSVM} /> } TransitionComponent={Zoom}> 
                     <div className="d-flex align-items-center">
                        <span className={row.PSV === row.SV ? "ml-3 pl-1" : "ml-2"}> <VolTool value={row.SV} /></span>
                        <span className={(row.PSV < row.SV ? 'arrow green m-l5 d-flex': row.PSV > row.SV ? 'arrow red m-l5 d-flex': 'd-none')}>
                           <FillArrow />
                        </span>
                     </div>
                  </Tooltip>
               </>
            :               
               <span className={ row.SV !== "init" ? "fM lightTxtClr ml-3 pl-1" : "fM lightTxtClr px-1"}>{row.SV !== "init" ? "NA" : <Tsk  width={60} /> }</span>                           
            }
            </div>
         ),
      },
      {
         id: "dt",
         name: <div className="p-l10"> DATE </div>,
         style : { backgroundColor: "#F5F5F5" },
         // selector: (row) => row.cd,
         reorder: false,
         minWidth: "106px",
         maxWidth: "120px",
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center flex-wrap p-l10">
               <span className="w-100 m-b5"> {row.KW ? getfulldate(row.cd) : <Tsk width={86} />}</span>
               <div className="d-flex m-r5 align-items-center">
                  {row.KW ? <RefreshIcon className="refrshIcon newlightTxtClr" height="10" width="10" color="#C9C8C8" /> : <Csk width={12} height={12} />}
                  <span className="text-truncate m-l5 f12x newlightTxtClr">{row.KW ? row.lrupt : <Tsk width={68} />}</span>
               </div>
            </div>
         ),
      },
   
      // eslint-disable-next-line react-hooks/exhaustive-deps 
   ], [lstresult, projectbase.age]);


   return (
    <>
      <div id="listtable" className="table-responsive CPKW-Listtable">
         { lstfltrresult.length > 0 ? 
            <DataTable
               // columns={[...columns.slice(0,3), ...orderChange(columns.slice(3,11), projectbase.lth), columns[11] ]}
               columns={columns}
               data={lstfltrresult}
               defaultSortFieldId={"rank"}
               defaultSortAsc= {true}
               sortIcon={<div className="d-flex"><SortingIcon /></div>}
               pagination={ lstfltrresult.length > 50 ? true : false }
               paginationPerPage={perPage}
               paginationRowsPerPageOptions={[50,100]}
               // paginationServer={ lstresult.length === kwCount ? false : true}
               paginationTotalRows={lstfltrresult.length}
               // onChangeRowsPerPage={handlePerRowsChange}
               // selectableRows
               // Clicked
               // onColumnOrderChange={testrender}
               // onSelectedRowsChange={handleRowSelected}
               // clearSelectedRows={toggleCleared}
               // selectableRowsHighlight={true}
               // conditionalRowStyles={conditionalRowStyles}
            />
         :
            <div className="empty_list_table text-center justify-content-center">
               <div>
                  <DataEmptyIcon />
                  <div className="ls-table-empty">
                     No Keywords Found
                  </div>
               </div>
            </div>
         }
      </div>
    </>
  );
}