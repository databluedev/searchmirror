import React, { useEffect, useState } from "react";
import { useHistory, useLocation } from "react-router-dom";
import "./style.scss";
import { Para,Title,AppIconButton,Tsk} from "../commonComponents/parts";
import { Tooltip } from "@mui/material";
import {fstLtrCapitalfun} from "../common_fun";
import { DeleteIcon } from "../commonComponents/icons";
import Cookies from 'universal-cookie';
import axios from 'axios';
import CompetitorOverview from "./components/competitor_overview";
import CompetitorTables from "./tables/competitor_tables";
import {ModalBox,CompetitorDelete} from "../commonComponents/Modals";
import Zoom from '@mui/material/Zoom';
import ReanalysisComponent from './components/reanalysis';
import { BacklinkIcon } from "../commonComponents/icons";
import { Link } from "react-router-dom";
import TopAllCompettors from './components/top_all_competiitors';
import CompKeywordRefreshStatus from "./components/comp_keyword_refresh_status";
import { allowsTeamAction } from '../../utils/team_permissions';

var lstresltdata = { "key": 11342, "RK": [], "RW": null, "RS": "never_checked", "SV": "init", "io": "", "PM": "", "kwas": "" }

//delete
const cookies = new Cookies();
const comp_grpid = cookies.get('__sp_cgrp__')
const comp_grp_age = cookies.get('__sp_cgrp_age__')
//delete

function CompetitorsComparison(props) {
   const canAddCompetitor = allowsTeamAction(props.fullbasedata, "CompAi", "Add Competitor");
   const canReanalyseCompetitor = allowsTeamAction(props.fullbasedata, "CompAi", "Re-analysis Competitor");
   const canDeleteCompetitor = allowsTeamAction(props.fullbasedata, "CompAi", "Delete Competitor");
 
   const history = useHistory();
   const location = useLocation();
   //delete
   const [delPrjtMdlVsble, setDelPrjtMdlVsble] = React.useState(false);
   //delete
   const [tableData, setTableData] = useState({ 'lstresult': [] });
   const [effectupdate, setEffectupdate] = useState(false);
   // "" while loading, "none" when the project has no competitors, "error"
   // when the overview call failed for any other reason.
   const [zcompCount, setZCompCount] = useState("");
   const [prjctName, setPrjctName] = useState(null);
   const [backlink, setBacklink] = useState("/competitors");

   const [data, setData] = useState({
      addlimit: 0,
      age: comp_grp_age,
      baseData: {},                       // CHOOSEN PROJECT DATA
      overviewData: {},                   // Overview Full data
      projectList: props.projectList,     // COMPLETE PROJECT LIST
      refreshCnt: 0,
   });
   var {addlimit, age, baseData, overviewData, refreshCnt} = data;

   useEffect(() => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      var grpid = cookies.get('activegrp')
      var comp_grpid = cookies.get('__sp_cgrp__')

      if(!usertoken || !userid){
         history.push("/login");      
      }

      if(location.state && location.state.back !== undefined){
         setBacklink(location.state.back)
      }

      var apidata = {}
      if(props.projectList.length > 0){
        apidata = props.projectList.filter(item => item.GY === parseInt(grpid))[0]
        if (typeof(apidata) !== "object" || apidata.length === 0){
          apidata = props.projectList[0]
        }
        cookies.set('activegrp', apidata.GY, { path: '/', maxAge: global.cookiesexpire });
        grpid = apidata.GY
      }

      var data = {
         'userid': userid,
         'grpid': grpid,
         'cpgrpid': comp_grpid,
      };
      axios.post(global.apiurl + '/compai/ranks', data, {
         headers: {'Authorization': 'Token '+ usertoken }
      }).then(response => {
         return response.data;
      }).then(res => {
         if(res.st !== 1){
            // Fail
         }else {
            // success
            setTableData(olddata => ({...olddata, 'lstresult': res.data }))
            // setData({ ...data, baseData: apidata, overviewData: res.data })
            // overview_details = res.data
         }
      }).catch((error) => {
         // history.push("/")
      });

      axios.post(global.apiurl + '/compai/competitoroverview', data, {
         headers: {'Authorization': 'Token '+ usertoken }
      }).then(response => {
         return response.data;
      }).then(res => {
         if(res.st !== 1){
            // Every non-success ends the load. Resolving the project name used
            // to throw whenever projectList had not arrived yet -- grpid is
            // still the cookie *string* on that first pass, so find() missed
            // and name.NM blew up. The throw landed in the empty .catch below,
            // so setZCompCount never ran and the page sat on its skeletons for
            // ever instead of saying the project has no competitors. Coerce the
            // id, tolerate a miss, and separate "none added" from a real error
            // so the screen never claims the wrong one.
            const project = props.projectList.find(item => Number(item.GY) === Number(grpid));
            setPrjctName(project ? project.NM : "");
            setZCompCount(res.Cc === 0 ? "none" : "error");
         }else {
            // success
            setData({ ...data, baseData: apidata, addlimit:res.al, age:res.gA, overviewData: res.data, refreshCnt: res.mrk })
            // overview_details = res.data
            if (res.gid){
               const cookies = new Cookies();
               cookies.set('__sp_cgrp__', res.gid , { path: '/', maxAge: global.cookiesexpire });  
            }
         }
      }).catch((error) => {
         // history.push("/")
      });

   // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [props.projectList,effectupdate]); 

   //delete
   const deleteProjectMdlOpen = () => {
      setDelPrjtMdlVsble(true);
   }
   const deleteProjectMdlClose = () => {
      setDelPrjtMdlVsble(false);
   };
   //delete

   const pageUpdate = () =>{
      setData({...data, baseData:{}, age:20, overviewData:{} })
      setTableData(olddata => ({...olddata, 'lstresult': Array(5).fill(lstresltdata) }))
      setEffectupdate(!effectupdate)
   }

   return (
      <>
      {zcompCount?
         <section className="layout">
            <header>
               <div className="d-flex justify-content-between flex-wrap gap-3">
                  <div className="d-flex flex-wrap gap-3 align-items-center">
                     <Title class="wd-title">Competitors Analysis
                     {prjctName ?
                        <Para class="wd-subTitle m-b0 d-flex align-items-center lh14x">
                           {fstLtrCapitalfun(prjctName)}
                        </Para>
                     : null}
                     </Title>
                  </div>
               </div>
            </header>
            <div className="emptyState">
               <p className="emptyState__label">{zcompCount === "error" ? "Comparison unavailable" : "Nothing to compare"}</p>
               {zcompCount === "error" ?
                  <p className="emptyState__body">
                     The comparison could not be loaded. Reload the page; if it keeps
                     failing, check that the backend is reachable.
                  </p>
               :
                  <p className="emptyState__body">
                     This page compares your rankings against one competitor you
                     track, and this project tracks none yet. Pick competitors from
                     the analysed list first.
                  </p>
               }
               {/* The old Start Analysis button here was dead: this branch never
                   sets addlimit, so ReanalysisComponent always saw addlm=0 and
                   answered every click with a false "you have reached your limit".
                   Choosing competitors is what actually unblocks this page, and
                   that happens on /competitors, so send the user there. */}
               {zcompCount === "none" ?
                  <Link className="btn btn-primary emptyState__action" to="/competitors">
                     Choose competitors
                  </Link>
               : null}
            </div>
         </section>
      :
         <section className="layout">
            <header>
            <div className="d-flex justify-content-between flex-wrap gap-3">
               <div className="d-flex flex-wrap gap-3 align-items-center">
                  <Link to={backlink}>
                     <AppIconButton
                     Icon={<BacklinkIcon />}
                     />
                  </Link>
                  <div>
                     <Title class="wd-title">Competitors Analysis</Title>
                     {
                        Object.keys(overviewData).length === 0 ? 
                           <Tsk width={180} height={16} className="my-1 d-flex align-items-center gap-2"/>
                        :
                           <Para class="wd-subTitle m-b0 d-flex align-items-center lh14x">
                              {fstLtrCapitalfun(baseData.NM)}
                                 <span className="fB pClr m-l5 m-r5">
                                    vs
                                 </span>
                              {fstLtrCapitalfun(overviewData.gn)} 
                           </Para>
                     }
                  </div>
               </div>
               <div
                  className="d-flex align-items-center twoButton addkeyhdr dashboard flex-none gap-[0.6rem]"
               >
                  {canReanalyseCompetitor ? <div>
                  <ReanalysisComponent addlm={addlimit} />
                  </div> : null}
                  {canDeleteCompetitor ? <div>
                  <Tooltip title="Delete Competitor" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
                     <div>
                     <AppIconButton class="compLottieIcon"
                        onclick={deleteProjectMdlOpen}
                        Icon={ <DeleteIcon  width="16" height="18" 
                     />} />   
                        </div>
                  </Tooltip>  
                  </div> : null}
                  {canAddCompetitor ? <div
                     className="min-w-[174px] max-w-[174px] flex-none"
                  >
                     <TopAllCompettors addlm={addlimit} canAdd={canAddCompetitor} />
                  </div> : null}
               </div>
            </div>
            </header>

            <div>
               {/* delete */}
               {canDeleteCompetitor ? <ModalBox title="" onClose={deleteProjectMdlClose} open={delPrjtMdlVsble} >
                  <CompetitorDelete cmpid={comp_grpid} modalClose={deleteProjectMdlClose}/>
               </ModalBox> : null}
               {/* delete */}

               {/* Both visibility scores average over the keywords the two domains
                   share, never the project's whole keyword set, so the overview
                   needs that count to print alongside them. */}
               <CompetitorOverview data={overviewData} age={age} sharedKeywords={tableData.lstresult.length} />
               
               <CompetitorTables projectName={baseData.NM} cprojectName={overviewData.gn} tableData={tableData} age={age} />

            </div>
         </section>
      }
      
         <CompKeywordRefreshStatus refreshCnt={refreshCnt} homeApi={pageUpdate} pageurl={"competitors/keywords"} />
      </>
   );
}

export default CompetitorsComparison;
