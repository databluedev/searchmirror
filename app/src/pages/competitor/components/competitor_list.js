import React, { useState,useEffect } from "react";
import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import { useHistory } from "react-router-dom";
import axios from 'axios';
import { DataEmptyIcon,CloseIconlg,DeleteIcon } from "../../commonComponents/icons";
import { Box, Button,Grid } from "@mui/material";
import {Para, Title, AppTooltip, AppButton,TextLg,Tsk} from "../../commonComponents/parts"; 
import {fstLtrCapitalfun} from "../../common_fun";   
import COMPTableSearch from "./compTableSearch";
import { GoLinkIcon } from "../../commonComponents/icons";
import SiteMark from "../../commonComponents/site_mark";
import parser from '../../../utils/domain';


function CompetitorsList(props) {

   const style = {
      position: "absolute",
      width: "100%",
      height: "100%",
      bgcolor: "var(--surface)",
      paddingLeft: '60px',
      outline: "none"
   };
   const Improved = (
      <div>
         <Para>
            List of all top competitors.
         </Para>
      </div>
   );
   // const [added,setAdded] = useState([]);
   const [data, setData] = useState({
      tlk : null,
      lm : 0,
      uCc : 0,
      tcc: props.tcc,
      fullComp: {},
      filterComp: {},
      addingComp:{},
      addedComp: [],
      // addedComp: added.map(data =>  data.dn),
      fnshBtn: false,
      modalOpen:false,
      loading:true
   });
   const history = useHistory();
   var {fullComp,filterComp,addingComp,tlk,lm,uCc,tcc,addedComp,fnshBtn,loading} = data;
   const projectCompetitorLimit = Math.min(Number(lm) || 6, 6);
   // uCc counts competitors across the whole ACCOUNT; the cap enforced here and
   // in the backend is per project. addedComp is built from Cpd, which the API
   // already scopes to this project, so it is what the counter must use --
   // otherwise a project tracking none shows itself as full.
   const projectUsed = addedComp.length;
   const selectedTotal = Object.keys(addingComp).length + projectUsed;
   const isAtCompetitorLimit = selectedTotal >= projectCompetitorLimit;
   const accountExhausted = (Object.keys(addingComp).length + uCc) >= Number(lm);
   useEffect(() => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      const grpid = cookies.get('activegrp');
      if(!usertoken || !userid){
         history.push("/login");        
      }

      var data = {
         'userid': userid,
         'grpid': grpid,
      };
      axios.post(global.apiurl + '/compai/competitorslist', data, {
         headers: {'Authorization': 'Token '+ usertoken }
      }).then(response => {
         return response.data;
      }).then(res => {
         if(res.st !== 1){
            // statusUpdate({'Astatus':"VOID"})
         }else {
            // setAdded(res.Cp)
            setData(olddata => ({...olddata, fullComp: res.Cl, filterComp: res.Cl, addedComp:res.Cpd.map(data => parser(data).domain), tlk: res.tlk, lm:res.lm, uCc:res.uCc, tcc:res.tcc, loading:false }))
         }
      }).catch((error) => {
         // history.push("/")
      });

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, []);
   const handleClose = () => {
      props.close();
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

   const handleAdding = (name) => {
      if(isAtCompetitorLimit){
         toast.error("You can track "+projectCompetitorLimit+" competitors per project. Remove one first.")
      }else if(accountExhausted){
         toast.error("Sorry! You have reached your limit.")
      }else{
         setData({...data,
            addingComp:{...addingComp, [name]:projectName(name) },
         })
      }
   }

   const handleDelete = (name) => {
      const { [name]: removed, ...remainingCompetitors } = addingComp;
      setData({...data, addingComp: remainingCompetitors })
   }

   const compdataUpdate = (data,loader=false) => {
      setData(olddata => ({...olddata, filterComp: data, loading:loader }))
   }

   const addCompetitors = () => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token');
      const userid = cookies.get('session_userid');
      const grpid = cookies.get('activegrp');
      if(Object.keys(addingComp).length === 0){
         toast.error("Please select at least one competitor")
      }else if(selectedTotal > projectCompetitorLimit){
         toast.error("You can't track more than "+projectCompetitorLimit+" competitors on one project")
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
            setData(olddata => ({...olddata, fnshBtn: false, addingComp:{} ,modalOpen:false }))
            props.close()
            if(res.st !== 1){
               toast.error(res.message)
               if(props.pageUpdate){
                  props.pageUpdate();
               }else{
                  history.push("/competitors");
               }
            }else {
               if(props.dataUpdate){
                  props.dataUpdate(res.Cp)
               }else{
                  history.push("/competitors");
               }
            }
         }).catch((error) => {
            setData(olddata => ({...olddata, fnshBtn: false, addingComp:{} ,modalOpen:false  }))
            props.close()
            if(props.pageUpdate){
               props.pageUpdate();
            }else{
               history.push("/competitors");
            }
         });
      }
   }


   return (
      <Box className="wd-modal-box topCompeti  mng-modal-box" sx={style}>
         <header className="wd-history-header">
            <div className="d-flex align-items-center justify-content-between px-2">
               <div> 
                  <Title class="wd-history-title">
                     {"All Competitors"}
                     <div className="toolTipIcon">
                        <AppTooltip dimension="14" parentClassName="z9999" place="bottom-start" title={Improved} /> 
                     </div>
                  </Title>
                  <Para class="mb-3 d-flex align-items-center f14x lh24x">Note: The list displays top competitors from {tcc} results.</Para> 
                  {/*<Para class="wd-history-sub-title mb-0">All competitors</Para>*/}
               </div>
               <div className="d-flex">
                  <div className="compSrch m-r10">
                     <COMPTableSearch pageType="modal" fullComp={fullComp} filterComp={filterComp} compdataUpdate={compdataUpdate} tcc={tcc}/>
                  </div>
                  <div style={{ flex: "0 0 auto" }}>
                     <Button onClick={handleClose} className="wd-CloseButton">
                        <CloseIconlg color="#0a0a0a" />
                     </Button>
                  </div>
               </div>
            </div>
            <div className="newCompSrch p-r20">
               <COMPTableSearch pageType="modal" fullComp={fullComp} filterComp={filterComp} compdataUpdate={compdataUpdate} tcc={tcc}/>
            </div>
         </header>
               
         <div>
            <div className="p20x m-b90">
               <Grid container spacing={2} className="projectSection">

               {loading ?
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
               :
               <>
               {Object.keys(filterComp).length > 0 ?
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
                                    disabled={isAtCompetitorLimit}
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
               </>
               }
               </Grid>
            </div>
            <div className="footer d-flex justify-content-between align-items-center">
            <div className="compFooterNote">
               <span className="fM">Tracking {projectUsed} of {projectCompetitorLimit} for this project</span>
               <span className="newlightTxtClr compFooterNote__hint">
                  {isAtCompetitorLimit && Object.keys(addingComp).length === 0
                     ? " · remove one to swap in another"
                     : " · " + Object.keys(addingComp).length + " selected to add"}
               </span>
            </div>
            <div className="d-flex cfbtns gap-3">
               <div style={{ width: "100px" }}>
                  <AppButton
                     onclick={handleClose}
                     value="Cancel"
                     color="white"
                     class="borderBtn"
                     noIcon="d-none"
                  ></AppButton>
               </div>
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
         </div>
         </div>
      </Box>

   );
}

export default CompetitorsList;
