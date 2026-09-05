import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Para,Title,SmallText,TextLg,Text, Tsk} from "../../commonComponents/parts";
import { Grid, Tooltip, Pagination, Stack, MenuItem } from "@mui/material";
import { GoOverviewPageIcon } from "../../commonComponents/icons";
import { url_to_host } from "../../common_fun";   
import Cookies from 'universal-cookie';
import Zoom from '@mui/material/Zoom';
import CompScoreDial, { CompTrend, CompCount } from "./comp_score_dial";
import { GoLinkIcon } from "../../commonComponents/icons";
import ClickAway from "../../commonComponents/click_away";
import {CompetitorEdit,CompetitorDelete,ModalBox} from "../../commonComponents/Modals";
import SiteMark from "../../commonComponents/site_mark";

function CompetitorProjects(props) {
   const [activeCompName, setActiveCompName] = React.useState(0);
   const [delPrjtMdlVsble, setDelPrjtMdlVsble] = React.useState(false);
   const [editPrjtMdlVsble, setEdtPrjtMdlVsble] = React.useState(false);
   const [activeCompId, setActiveCompId] = React.useState(0);
   const effectupdate = false;

   const [data, setData] = useState({
      page: 1,
      list: props.aiRunStatus.Cp.slice(0, props.compProjectPageLimit),
      tlk : props.aiRunStatus.tlk,
      lm : props.aiRunStatus.lm,
   });
   
   // var {list, topGeneralComp,addingComp,tlk,lm,addedComp,community,social,fnshBtn} = data;
   var {page, list} = data;

  
   useEffect(() => {
      if (Object.keys(props.aiRunStatus.Cp).length > 0){
         setData(olddata => ({...olddata, page:1, list: props.aiRunStatus.Cp.slice(0, props.compProjectPageLimit), tlk : props.aiRunStatus.tlk, lm : props.aiRunStatus.lm }))
      }

   // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [props.aiRunStatus.Cp,effectupdate]);

   const comparisonPage = (domain,grpAge) => {
      const cookies = new Cookies();
      cookies.set('__sp_cgrp__', domain , { path: '/', maxAge: global.cookiesexpire });  
      cookies.set('__sp_cgrp_age__', grpAge , { path: '/', maxAge: global.cookiesexpire });  
   }

   const pageChange = (event, value) => {
      setData(olddata => ({...olddata, page:value, list:props.aiRunStatus.Cp.slice((value * props.compProjectPageLimit)-props.compProjectPageLimit, value * props.compProjectPageLimit) }))
      // setProject(olddata => ({...olddata, 'page':value, 'displaydata': project.filterdata.slice((value * projectPageLimit)-projectPageLimit, value * projectPageLimit) }))
   };

   // const viewProjectMdlOpen = (pinfo) => {
   //    setProjectInfo({...projectInfo,
   //      domainStatus: "-",
   //      register : "-",
   //      domainCreated : "-",
   //      domainUpdate : "-",
   //      domainExpiry : "-",
   //      organization : "-",
   //      state : "-",
   //      country : "-",
   //      domainUrl : "http://www.test.com",
   //      domainName : "Test",
   //  });
   //    setViewPrjtModal(true);
   // }
   // const closeviewProjectMdlOpen = () => {
   //    setViewPrjtModal(false);
   // };
   const editProjectMdlOpen = (cid,cname) => {
      setActiveCompId(cid);
      setActiveCompName(cname);;
      setEdtPrjtMdlVsble(true);
   };

   const editProjectMdlClose = () => {
      setEdtPrjtMdlVsble(false);
   };

   const deleteProjectMdlOpen = (cid) => {
      setDelPrjtMdlVsble(true);
      setActiveCompId(cid); 
   };

   const deleteProjectMdlClose = () => {
      setDelPrjtMdlVsble(false);
   };

   const updateItem = (data) => {
      let index = list.findIndex(x => x.key === data.id);
      if (index !== -1) {
        let temporaryarray = list.slice();
        temporaryarray[index]['pn'] = data.cname;
        setData(olddata => ({...olddata, list: temporaryarray}))

      } else {
        console.log('no match');
      }
   }

   const deleteItem = (data) => {
      let index = list.findIndex(x => x.key === data.id);
      if (index !== -1) { 
         const newArray = list.filter((comp) => comp.key !== data.id);        
         setData(olddata => ({...olddata, list: newArray}))
      } else {
        console.log('no match');
      }
   }

   return (
      <>
         {/* <ProjectInfoModalComponent
            prjData={projectInfo}
            IsModalOpened={viewPrjtModal}
            onCloseModal={closeviewPrfojectMdlOpen}
         /> */}
         {/* delete */}
         <ModalBox title="" onClose={deleteProjectMdlClose} open={delPrjtMdlVsble} >
            <CompetitorDelete cmpid={activeCompId} modalClose={deleteProjectMdlClose} deleteItem={deleteItem} pagetype="competitors"/>
         </ModalBox>
         {/* delete */}
         <ModalBox title="" onClose={editProjectMdlClose} open={editPrjtMdlVsble} >
            <CompetitorEdit cid={activeCompId} cname={activeCompName} modalClose={editProjectMdlClose} updateItem={updateItem}/>
          </ModalBox>
         <div className="compProj">
           <Grid container spacing={2} className="projectSection">
           {list.map((comp, index) => (
               <Grid key={index} item xs={12} md={6} lg={4} xl={4}>
                  <div className="projectCard">
                  <div className="d-flex align-items-center gap-2">
                        <div className="whiteBorderBtn align-self-start p-1">
                           { comp.dn ?
                              <SiteMark domain={comp.dn} className="bdr-4x" width={25} height={25} />
                           : <Tsk height={20} width={20} /> }
                        </div>
                     <div className="w-100 align-self-start overflow-hidden compName">
                        <div className="d-flex">
                           <Link to="/competitors/keywords" onClick={() => comparisonPage(comp.key,comp.gA)} className="text-truncate">
                              <TextLg class="mb-0 fM lineHAuto pClr text-truncate">
                                 {comp.pn ? <span className="hvr-underline">{comp.pn}</span> : <Tsk width={"100%"} />}
                              </TextLg> 
                           </Link>
                           {/*<div style={{width: "17px", flex: "0 0 auto", marginLeft: '5px'}}>
                           <Tooltip title={"Delete Competitor"} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
                              <div className="deleteComp">
                              { comp.Mtk !== null ? <DeleteIcon width="14.2" height="14" /> : null}
                              </div>
                           </Tooltip>
                        </div>*/}
                        </div>
                        <Para class="mb-2 d-flex">{comp.dn ? 
                        <>
                           <a href={comp.dn} target="_blank" rel="noopener noreferrer" className="goLink linknvrColor d-flex align-items-center" >
                           <span className="mW-180 text-truncate d-block linkColor linknvrColor"> 
                           {url_to_host(comp.dn)}
                           </span>
                              <GoLinkIcon height={10} width={10} className={"m-l5 newlightTxtClr"} />
                           </a>
                        </>
                        // url_to_host(comp.dn)
                        : <Tsk width={80} />}</Para>
                        <Para class="mb-1">Matching keyword</Para>
                        { comp.Mtk !== null ? 
                           <TextLg class="mb-0 lineHAuto fB f14x d-flex">
                              <Tooltip title={<>Yesterday, it was { comp.yMtk >= 0 ? comp.yMtk : <span className="newlightTxtClr fM">not available</span> }</>} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
                              <div className="d-flex">
                                 {comp.Mtk} 
                              </div>
                           </Tooltip>
                           /{comp.Tk}</TextLg> 
                        : <Tsk width={60} height={22} />}
                     </div>
                     <div className="flexoAuto text-center mt-1 compScore">
                        <Text class="lineHTen txtClr mb-2">Search Visibility Score</Text>
                        <div>
                        <CompScoreDial score={comp.ss} measured={comp.Mtk !== null} />
                        </div>
                        {/* The score is an average over the shared keywords only,
                            so it has to carry that denominator. Without it an 80
                            computed across 4 of 30 keywords reads as a project-wide
                            80 and outranks a real one. */}
                        <SmallText class="compDial__scope d-block">
                           {comp.Mtk !== null ? <>over {comp.Mtk} keyword{comp.Mtk === "1" || comp.Mtk === 1 ? "" : "s"}</> : <Tsk width={80} height={14} />}
                        </SmallText>
                        <SmallText class="fB d-flex align-items-center justify-content-center">
                        <span className="m-r5 txtClr l18px d-flex align-items-center"> Best <span className="m-l5">{(comp.Mtk !== null && comp.bss >= 0) ? comp.bss : comp.bss < 0 ? <span className="newlightTxtClr">NA</span> : <Tsk width={30} height={18} />} </span></span>
                        </SmallText>
                        {comp.Mtk !== null ?
                           <SmallText class="compTrend d-block">
                              <CompTrend current={comp.ss} previous={comp.yss} measured={comp.gA > 1} />
                           </SmallText>
                        : null}
                     </div>
                     <div className="moreIcon align-self-start">
                        <ClickAway>
                           {/* <MenuItem className="primaryHover" onClick={() => viewProjectMdlOpen(comp)}>Info</MenuItem> */}
                           <MenuItem className="primaryHover" onClick={() => editProjectMdlOpen(comp.key,comp.pn)}>Rename</MenuItem>
                           <MenuItem className="primaryHover" onClick={() => deleteProjectMdlOpen(comp.key)}>Delete</MenuItem>
                        </ClickAway> 
                     </div>
                     </div>
                     <Grid container spacing={0} className="whiteBox">
                        <Grid item xs={4} md={4}>
                           <div className="status bg-transparent p-0">
                              <Text class="mb-2 d-flex align-items-center gap-1 f14x">
                              <span className="lineHTen">Improved</span>
                              </Text>
                              {comp.Mtk !== null ? 
                              <Tooltip title={<>Yesterday, it was { comp.yik >= 0 ? comp.yik : <span className="newlightTxtClr fM">not available</span>}</>} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
                                    <div>
                                    <Title class="my-1 d-flex align-items-center gap-2 f18x">
                                       <CompCount value={comp.ik} measured={comp.gA > 1} />
                                    </Title>
                                    </div>
                              </Tooltip>
                           : <Tsk width={40} />}
                           </div>
                        </Grid>
                        <Grid item xs={4} md={4}>
                           <div className="status bg-transparent p-0">
                              <Text class="mb-2 d-flex align-items-center gap-1 f14x">
                              <span className="lineHTen">Declined</span>
                              </Text>

                              {comp.Mtk !== null ? 
                              <Tooltip title={<>Yesterday, it was { comp.ydk >= 0 ? comp.ydk : <span className="newlightTxtClr fM">not available</span>}</>} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
                              <div>
                              <Title class="my-1 d-flex align-items-center gap-2 f18x">
                                    <CompCount value={comp.dk} measured={comp.gA > 1} />
                              </Title>
                              </div>
                              </Tooltip>
                              : <Tsk width={40} />}
                           </div>
                        </Grid>
                        <Grid item xs={4} md={4}>
                           <div className="status bg-transparent p-0">
                              <Text class="mb-2 d-flex align-items-center gap-1 f14x">
                              <span className="lineHTen">First Position</span>
                              </Text>
                              {comp.Mtk !== null ? 
                              <Tooltip title={<>Yesterday, it was { comp.yfp >= 0 ? comp.yfp : <span className="newlightTxtClr fM">not available</span>}</>} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
                              <div>
                              <Title class="my-1 d-flex align-items-center gap-2 f18x">
                                    <CompCount value={comp.fp} measured={comp.gA > 1} />
                              </Title>
                              </div>
                              </Tooltip>
                              : <Tsk width={40} />}
                           </div>
                        </Grid>
                     </Grid>
                     <div className="d-flex align-items-center justify-content-between">

                        {comp.rT?
                           <Para class="dS_Bsdte m-b0  m-t20 f13x lh20x">Last Updated: {comp.rT} </Para>  
                        :
                           <div className="kr_vt10Button m-t20">    
                              <Tsk height={24} width={100} />
                           </div>
                        }

                        <div className="kr_vt10Button-block-snp m-t0">
                        {comp.key?
                           <Link to="/competitors/keywords" onClick={() => comparisonPage(comp.key,comp.gA)} className="text-truncate">
                              <div className="kr_vt10Button m-t20">
                                 {"View Keywords"} 
                                 <span className="arrow m-l5">
                                    <GoOverviewPageIcon/>
                                 </span>     
                              </div>
                           </Link>
                        :
                           <div className="kr_vt10Button m-t20">    
                              <Tsk height={24} width={160} />
                           </div>
                        }
                        </div>
                     </div>
                  </div>
               </Grid>
            ))}
            </Grid>
         </div>

         { props.aiRunStatus.Cp.length > props.compProjectPageLimit ? 
            <Stack className="d-flex m-t30 align-items-center justify-content-end" spacing={2}>
               <Pagination count={props.aiRunStatus.Cp.length % props.compProjectPageLimit === 0 ? props.aiRunStatus.Cp.length/props.compProjectPageLimit : Math.floor(props.aiRunStatus.Cp.length/props.compProjectPageLimit)+1} variant="outlined" color="primary" page={page} onChange={pageChange} />
            </Stack>
         : null }
      </>
   );
}

export default CompetitorProjects; 
