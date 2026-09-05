import React, { useEffect, useState } from "react";
import { Para,ParaLg,AppButton,AppTooltip,TextLg,Tsk} from "../../commonComponents/parts";
import { Grid } from "@mui/material";
import { DeleteIcon,DataEmptyIcon,GoLinkIcon } from "../../commonComponents/icons";
import {fstLtrCapitalfun} from "../../common_fun";   
import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import axios from 'axios';
import COMPTableSearch from "./compTableSearch";
import SiteMark from "../../commonComponents/site_mark";
import parser from '../../../utils/domain';

const existingCompetitorDomains = (competitors = []) =>
   (competitors || []).map((competitor) => parser(competitor.dn).domain);

function TopCompetitorsList(props) {
   const [data, setData] = useState({ 
      tcc : props.aiRunStatus.tcc,
      tlk : props.aiRunStatus.tlk,
      lm : props.aiRunStatus.lm,
      uCc : props.aiRunStatus.uCc,
      fullComp: props.aiRunStatus.Cl,
      filterComp: props.aiRunStatus.Cl,
      // filterComp: {"morioh.com": 65, "codecanyon.net": 59, "quora.com": 57, "github.com": 56, "appdupe.com": 54, "dribbble.com": 54 },
      // addingComp:{"morioh.com": 8,"codecanyon.net": 10},
      addingComp:{},
      addedComp: existingCompetitorDomains(props.aiRunStatus.fullCp),
      // addedComp: props.aiRunStatus.fullCp.map(data =>  data.dn),
      // community:{"morioh.com": 65, "codecanyon.net": 59},
      // social: {"morioh.com": 65, "codecanyon.net": 59},
      fnshBtn: false,
      loading: false,
      // searchGeneralComp: props.aiRunStatus.Cl,

   });
   
   var {fullComp,filterComp,addingComp,tlk,lm,uCc,addedComp,fnshBtn,loading,tcc} = data;

   // uCc is CompProject.objects.filter(fk_user_id=userid).count() -- every
   // competitor on the ACCOUNT, across every project. The cap this screen
   // enforces is per project (backend/competitor/views.py add_competitors hard
   // limits usedProjectCompCnt to 6), so counting with uCc made the footer read
   // "Finish (6/6)" on a project that tracks none, directly contradicting
   // /competitors/keywords. addedComp comes from aiRunStatus.fullCp, which the
   // API already scopes to this project, so it is the honest numerator.
   const projectUsed = addedComp.length;
   const projectLimit = Math.min(Number(lm) || 6, 6);
   const selectedTotal = Object.keys(addingComp).length + projectUsed;
   const atProjectLimit = selectedTotal >= projectLimit;
   const accountExhausted = (Object.keys(addingComp).length + uCc) >= Number(lm);

   const Comparison = (
      <div>
         <Para class="m-b0">
            This displays the complete list of  all the top competitors for this project.
            And, you can choose your competitors among those listed here.
         </Para>
      </div>
   );
   useEffect(() => {
      // The component mounts as soon as analysis enters COMP, before the
      // asynchronous status payload necessarily contains the existing cards.
      // Keep the local selection state aligned when that payload arrives;
      // otherwise all six tracked competitors look unselected and neither
      // Skip nor Finish can leave this screen.
      setData(olddata => ({
         ...olddata,
         tcc: props.aiRunStatus.tcc,
         tlk: props.aiRunStatus.tlk,
         lm: props.aiRunStatus.lm,
         uCc: props.aiRunStatus.uCc,
         addedComp: existingCompetitorDomains(props.aiRunStatus.fullCp),
         fullComp: props.aiRunStatus.Cl,
         filterComp: props.aiRunStatus.Cl,
      }));
   }, [props.aiRunStatus]); 

   const handleAdding = (name) => {
      if(atProjectLimit){
         toast.error("You can track "+projectLimit+" competitors per project. Remove one first.")
      }else if(accountExhausted){
         toast.error("Sorry! You have reached your limit.")
      }else{
         setData({...data,
            addingComp:{...addingComp, [name]:projectName(name) },
         })
      }
   }

   const handleDelete = (name) => {
      // setData({...data,
      //    addingComp:[...addingComp, name],
      // })
      // var removedcomp = addingComp.filter((incomp, index) => incomp !== name);
      var removedcomp = addingComp
      delete removedcomp[name]
      setData({...data, addingComp: removedcomp })
   }

   const projectName = (domain) => {
      try{
         var dminfo = parser("http://"+domain)
         // var project_name = dminfo.domain.replace(dminfo.tld, "").slice(0,-1)
         var project_name = dminfo.domain.replace("."+dminfo.tld, "")
         return fstLtrCapitalfun(project_name)
      }catch(e){
         return fstLtrCapitalfun(domain)
      }
   }

   const addCompetitors = () => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token');
      const userid = cookies.get('session_userid');
      const grpid = cookies.get('activegrp');
      if(Object.keys(addingComp).length === 0){
         toast.error("Please select at least one competitor")
      }else if(selectedTotal > projectLimit){
         toast.error("You can't track more than "+projectLimit+" competitors on one project")
      }else if(userid && grpid) {
         setData(olddata => ({...olddata, fnshBtn: true }))
         // setAiRunStatus(olddata => ({...olddata, 'Astatus':"LOAD"}))
         var data = {
            'userid': userid,
            'grpid': grpid,
            'comp': addingComp,
         };
         axios.post(global.apiurl + '/compai/addcompetitors', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if(res.st !== 1){
               setData(olddata => ({...olddata, fnshBtn: false }))
               toast.error(res.message)  
            }else {
               setData(olddata => ({...olddata, fnshBtn: false }))
               props.statusUpdate({'fullCp':res.Cp, 'Cp':res.Cp, 'Astatus':"OVER"})
               // history.push('/topcompetitors');
            }
         }).catch((error) => {
            setData(olddata => ({...olddata, fnshBtn: false }))
            // history.push("/")
         });
      }
   }


   const skipAnalysis = () => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token');
      const userid = cookies.get('session_userid');
      const grpid = cookies.get('activegrp');
      if((Object.keys(addingComp).length + addedComp.length) === 0){
         toast.error("Please select at least one competitor")
      }else if(userid && grpid) {
         props.statusUpdate({'Astatus':"OVER"})
         var data = {
            'userid': userid,
            'grpid': grpid,
            // 'comp': addingComp,
         };
         axios.post(global.apiurl + '/compai/skipanalysis', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if(res.st !== 1){
               // toast.error(res.message)  
            }else {
               // props.statusUpdate({'fullCp':res.Cp, 'Cp':res.Cp, 'Astatus':"OVER"})
               // history.push('/topcompetitors');
            }
         }).catch((error) => {
            // history.push("/")
         });
      }
   }

   const compdataUpdate = (data,loader=false) => {
      setData(olddata => ({...olddata, filterComp: data, loading:loader }))
   }

   return (
      <>
         <div className="topCompeti">
            <div className="m-b70">
               <div className="header d-flex align-items-center justify-content-between mb-5 flex-wrap">
                  <div className="left">
                  <ParaLg class="mb-0 lh24x">
                     <span className="fB">All Competitors</span>
                     <span className="m-l5">
                        <AppTooltip place="bottom-end" class="m-b0" title={Comparison} />
                     </span>
                  </ParaLg>
                  <Para class="mb-3 f14x lh24x">
                     Domains that showed up in your keywords' search results. Add up
                     to {projectLimit} to track their rankings beside yours; social,
                     community and forum sites are filtered out.
                  </Para>
                  </div>
                  <div className="right">
                     <COMPTableSearch tcc={tcc} fullComp={fullComp} filterComp={filterComp} compdataUpdate={compdataUpdate}/>
                  </div>
               </div>
               {/*<span className="m-l5 newlightTxtClr">(Only general sites are available. Social Media, Community and Forms sites removed.)</span>*/}
               {/*<div className="d-flex flex-wrap gap-3 mb-3">
                  <Box
                     className=""
                     sx={{ minWidth: "134px", maxWidth: "150px", flex: "0 0 auto" }}
                  >                     

                     <Button className="whiteBorderBtn">
                        General Sites
                        <span className="m-l8 m-b2">
                           <AppTooltip place="bottom-end" title={Improved} />
                        </span>
                     </Button>
                  </Box>
                  <Box 
                     className=""
                     sx={{ minWidth: "198px", maxWidth: "198px", flex: "0 0 auto" }}
                  >
                     <Button className="primaryButton">
                        Community and Forms
                        <span className="m-l8 m-b2">
                           <AppTooltip place="bottom-end" color="#FFFFFF" title={Improved} />
                        </span>
                     </Button>
                  </Box>
                  <Box 
                     className=""
                     sx={{ minWidth: "132px", maxWidth: "150px", flex: "0 0 auto" }}
                  >
                     <Button className="primaryButton">
                        Social Media
                        <span className="m-l8 m-b2">
                           <AppTooltip place="bottom-end" color="#FFFFFF" title={Improved} />
                        </span>
                     </Button>
                  </Box>
               </div>*/}

               <Grid container spacing={2} className="projectSection">
                  { loading ?
                     [1,2,3,4,5,6,7,8,9].map((compet, index) => (
                        <Grid key={index} item xs={12} md={6} lg={4} xl={4}>
                           <div className={"smallwhiteBox"}>
                              <div className="d-flex align-items-center overflow-hidden">
                                 <div className="whiteBorderBtn align-self-start p-1 m-r10 borderLigClr bdr-5x">
                                    <Tsk height={30} width={30} />
                                 </div>
                                 <div className="w-100 overflow-hidden m-r10">
                                    <TextLg class="mb-0 lineHAuto hvr-text-underline fM pClr text-truncate">
                                       <Tsk width={120} height={18} />
                                    </TextLg>
                                    <Para class="mb-0 m-t8 lh18x text-truncate"><Tsk width={160} height={16} /></Para>
                                   
                                    <Para class="mb-1 m-t10">Matching keyword</Para>
                                    <TextLg class="mb-0 lineHAuto fB"><Tsk className="m-t5" width={60} height={20} /></TextLg>
                                 </div>
                                 <Tsk width={100} height={30} style={{ marginRight: "-10px" }}/>
                              </div>
                           </div>
                        </Grid>
                     ))
                  : Object.keys(filterComp).length > 0 ?
                     Object.keys(filterComp).map((compet, index) => (
                        

                        <Grid key={index} item xs={12} md={6} lg={4} xl={4}>
                           <div className={"smallwhiteBox "+ (addingComp[compet] ? "another"  : addedComp.includes(compet) ? "another":"")}>
                              <div className="d-flex align-items-center overflow-hidden">
                                 <div className="whiteBorderBtn align-self-start p-1 m-r10 borderLigClr bdr-5x">
                                    <SiteMark domain={compet} className="bdr-4x" width={30} height={30} />
                                 </div>
                                 <div className="w-100 overflow-hidden m-r10">
                                    <TextLg class="mb-0 lineHAuto fM pClr text-truncate">
                                       {projectName(compet)}
                                    </TextLg>
                                    <a href={"http://"+compet} target="_blank" rel="noopener noreferrer" className="goLink">
                                       <div className={"maxW290x mb-0 mt-1 text-truncate f14x lh18x linkColor linknvrColor d-flex align-items-center"}>
                                          {compet}
                                          <GoLinkIcon height={10} width={10} className={"m-l5 newlightTxtClr"} />
                                       </div>
                                    </a>
                                    {/*<Para class="mb-2 text-truncate">{compet}</Para>*/}
                                    <Para class="mb-1 m-t10">Matching keywords</Para>
                                    <TextLg class="mb-0 lineHAuto fB">{filterComp[compet]}/{tlk}</TextLg>
                                    <span className="compDial__scope d-block">of the keywords last analysed</span>
                                 </div>
                                 { addedComp.includes(compet) ?
                                    <span className="pClr f14x p-r10">Added</span>
                                 : !props.canAdd ?
                                    <span className="lightTxtClr f14x p-r10">Available</span>
                                 : addingComp[compet] ?
                                    <AppButton
                                       onclick={() => handleDelete(compet)}
                                       class="smallBtn danger"
                                       Icon={ <DeleteIcon color="#fff" style={{ marginRight: "-10px" }}/> }
                                    ></AppButton> 
                                 :
                                    <AppButton
                                       value="Add"
                                       class="smallBtn"
                                       noIcon="d-none"
                                       onclick={()=> handleAdding(compet)}
                                       disabled={atProjectLimit}
                                    ></AppButton>
                                 }
                              </div>
                           </div>
                        </Grid>
                     ))
                  :
                     <div className="d-flex align-items-center justify-content-center w-100 h60vh">
                        <div className="text-center">
                           <DataEmptyIcon className=""/>
                           <div className="ls-table-empty m-t15">
                              No matches found within {tcc} competitors!
                           </div>
                        </div>
                     </div>
                  }
               </Grid>
            </div>
            
            {props.canAdd ? <div className="footer d-flex justify-content-between align-items-center">
               <div className="compFooterNote">
                  {/* The counter states this project's position, not the account's,
                      and names the action instead of leaving "Finish (6/6)" to be
                      guessed at. */}
                  <span className="fM">Tracking {projectUsed} of {projectLimit} for this project</span>
                  <span className="newlightTxtClr compFooterNote__hint">
                     {atProjectLimit && Object.keys(addingComp).length === 0
                        ? " · remove one to swap in another"
                        : " · " + Object.keys(addingComp).length + " selected to add"}
                  </span>
               </div>
               <div className="d-flex gap-3">
                  { projectUsed > 0 ?
                     <div style={{ width: "100px" }}>
                        <AppButton
                           onclick={skipAnalysis}
                           value="Done"
                           color="white"
                           class="borderBtn"
                           noIcon="d-none"
                        ></AppButton>
                     </div>
                  : null }
                     <div style={{ width: "170px" }}>
                        <AppButton
                           onclick={addCompetitors}
                           value={Object.keys(addingComp).length > 0
                              ? "Track " + Object.keys(addingComp).length + " competitor" + (Object.keys(addingComp).length === 1 ? "" : "s")
                              : "Select to track"}
                           color={ Object.keys(addingComp).length > 0 ? "primary" : "white"}
                           class={ Object.keys(addingComp).length > 0 ? "" : "borderBtn"}
                           noIcon="d-none"
                           disabled={Object.keys(addingComp).length === 0}
                           loading={fnshBtn}
                        ></AppButton>
                     </div>
               </div>
            </div> : null}
         </div>

         {/*
            <Grid key={index} item xs={12} md={6} lg={4} xl={4}>
               <div className={"smallwhiteBox "+ (addingComp[compet] ? "another"  : addedComp.includes(compet) ? "another":"")}>
                  <div className="d-flex align-items-center overflow-hidden">
                     <div className="whiteBorderBtn align-self-start p-1 m-r10 borderLigClr bdr-5x">
                        <SiteMark domain={compet} width={30} height={30} />
                     </div>
                     <div className="w-100 overflow-hidden m-r10">
                       
                        <TextLg class="mb-0 lineHAuto fM pClr text-truncate">
                        {projectName(compet)}
                        </TextLg>
                        <a href={"http://"+compet} target="_blank" rel="noopener noreferrer" >
                        <div className={"maxW290x mb-2 mt-1 text-truncate f14x lh14x newlightTxtClr"}>
                        {compet}
                        <GoLinkIcon height={10} width={10} className={"m-l5 newlightTxtClr"} />
                        </div>
                        </a>
                        <Para class="mb-1">Matching keyword</Para>
                        <TextLg class="mb-0 lineHAuto fB">{filterComp[compet]}/{tlk}</TextLg>
                     </div>
                     { addedComp.includes(compet) ?
                        <span className="pClr f14x p-r10">Added</span>
                     : addingComp[compet] ?
                        <AppButton
                        onclick={() => handleDelete(compet)}
                        class="smallBtn danger"
                        Icon={ <DeleteIcon color="#fff" style={{ marginRight: "-10px" }}/> }
                        ></AppButton> 
                     :
                        <AppButton
                           value="Add"
                           class="smallBtn"
                           noIcon="d-none"
                           onclick={()=> handleAdding(compet)}
                        ></AppButton>
                     }
                  </div>
               </div>
            </Grid>
         */}
      </>
   );
}

export default TopCompetitorsList;
