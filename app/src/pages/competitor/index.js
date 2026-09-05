import React, { useEffect, useState, useRef } from "react";
import "./style.scss";
import { useHistory } from "react-router-dom";
import { Title, Para, AppButton } from "../commonComponents/parts";
import { Box, Fade } from "@mui/material";

import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import axios from 'axios';

import { DataEmptyIcon } from "../commonComponents/icons";
import AnalysisStatus from "./components/analysis_status";
import CompetitorHeader from "./components/competitor_header";
import TopCompetitorsList from "./components/top_competitors";
import CompetitorProjects from "./components/competitor_projects";
import CompProjectRefreshStatus from "./components/comp_project_refresh_status";
import { allowsTeamAction } from '../../utils/team_permissions';


// Astatus === "INIT" --> Start Analysis
// Astatus === "VOID" --> Start Analysis
// Astatus === "LOAD" --> Starting Analysis api call button loader
// Astatus === "SCHD" --> Analysis START & SCHD
// Astatus === "WAIT" --> Analysis WAIT 
// Astatus === "COMP" --> Analysis COMP
// Astatus === "OVER" --> Analysis OVER
// Astatus === "FAIL" --> Analysis FAIL

const compProjectPageLimit = 15

function CompetitorAnalysis(props) {

   const canAddCompetitor = allowsTeamAction(props.fullbasedata, "CompAi", "Add Competitor");
   const canReanalyseCompetitors = allowsTeamAction(props.fullbasedata, "CompAi", "Re-analysis Competitor");

   const [aiRunStatus, setAiRunStatus] = useState({ 'Astatus': "INIT", 'Cl': {}, 'fullCp': [], 'Cp': [], 'lm': 1, 'uCc': 0, 'Ac': 0, 'trk': 0, 'tlk': 0, 'trd': 0 });
   const [effectupdate, setEffectupdate] = useState(false);
   const [wait, setWait] = useState(false);

   const onAnalysisTriggerFunc = useRef(null)
   const history = useHistory();
   var intervalRef = useRef(null);

   // The three staged bars below are scheduled with setTimeout and each one
   // closes over the aiRunStatus of the render that scheduled it. Once the
   // status leaves SCHD that captured value is stale, so createProgressbar's
   // own guard still passes while the element it looks up has already been
   // unmounted -- which is the "Cannot set properties of null (setting
   // 'className')" throw. Cancelling them on every status change and on unmount
   // is what actually stops it.
   const progressTimersRef = useRef([]);
   const clearProgressTimers = () => {
      progressTimersRef.current.forEach(clearTimeout);
      progressTimersRef.current = [];
   };

   const createProgressbar = (id, duration, callback) => {
      if (aiRunStatus.Astatus === "SCHD") {
         var progressbar = document.getElementById(id);
         progressbar.className = 'progressbar';
         var progressbarinner = document.createElement('div');
         progressbarinner.className = 'progress-value';
         progressbarinner.style.animationDuration = duration;
         if (typeof (callback) === 'function') {
            progressbarinner.addEventListener('animationend', callback);
         }
         progressbar.appendChild(progressbarinner);
         progressbarinner.style.animationPlayState = 'running';
      } else {
         clearInterval(intervalRef.current);
         intervalRef.current = null;
      }
   }

   const callProgress = () => {
      // The previous batch has long since fired by the time the 40s interval
      // calls back round; dropping it keeps the list from growing.
      clearProgressTimers();
      if (aiRunStatus.Astatus === "SCHD") {

         createProgressbar('progressbar1', '10s');
         progressTimersRef.current.push(setTimeout(function () {
            createProgressbar('progressbar2', '10s')
         }, 10000));
         progressTimersRef.current.push(setTimeout(function () {
            createProgressbar('progressbar3', '10s')
         }, 20000));
         progressTimersRef.current.push(setTimeout(function () {
            createProgressbar('progressbar4', '10s')
         }, 30000));
      } else {
         clearInterval(intervalRef.current);
         intervalRef.current = null;
      }

   }

   useEffect(() => {
      if (aiRunStatus.Astatus === "SCHD") {
         callProgress();
         intervalRef.current = setInterval(function () {
            document.querySelectorAll(".progress-value").forEach(el => el.remove());
            callProgress();
         }, 40000);
      } else {
         clearInterval(intervalRef.current);
         intervalRef.current = null;
      }

      return () => {
         clearInterval(intervalRef.current);
         intervalRef.current = null;
         clearProgressTimers();
      };

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [aiRunStatus.Astatus])

   useEffect(() => {
      // The status request outlives a route change unless it is torn down here.
      //
      // docs/DESIGN.md, "Loading": the top progress line, not a skeleton. This
      // one request decides between five different screens -- top competitors,
      // the tracked-project grid, the analysis-in-progress screen, the empty
      // state and the error -- so there is no shape to draw in advance, and a
      // table skeleton in front of the analysis screen would be a lie. It runs
      // until the request settles rather than on the fixed 1.5s timer it used
      // to, which finished while the page was still blank.
      const controller = new AbortController();
      global.PageTopLoader.current.continuousStart();
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      const grpid = cookies.get('activegrp');
      if (!usertoken || !userid) {
         history.push("/login");
      }

      var data = {
         'userid': userid,
         'grpid': grpid,
      };
      axios.post(global.apiurl + '/compai/analysisstatus', data, {
         headers: { 'Authorization': 'Token ' + usertoken },
         signal: controller.signal
      }).then(response => {
         return response.data;
      }).then(res => {
         if (res.st !== 1) {
            statusUpdate({ 'Astatus': "VOID" })
         } else {
            if (res.As === "VOID" || res.As === "FAIL") {
               statusUpdate({ 'Astatus': "VOID", 'Ac': res.Ac })
            } else if (res.As === "START" || res.As === "SCHD") {
               statusUpdate({ 'Astatus': "SCHD", 'trk': res.Ad['track_keywords'], 'tlk': res.Ad['total_keywords'], 'trd': res.Ad['total_domains'] })
               onAnalysisTriggerFunc.current()
            } else if (res.As === "COMP") {
               statusUpdate({ 'Astatus': "COMP", 'fullCp': res.Cp, 'Cp': res.Cp, 'Cl': res.Cl, 'lm': res.lm, 'uCc': res.uCc, 'trk': res.Ad['track_keywords'], 'tlk': res.tlk, 'trd': res.Ad['total_domains'], 'tcc': res.tcc })
            } else if (res.As === "OVER") {
               statusUpdate({ 'Astatus': "OVER", 'fullCp': res.Cp, 'Cp': res.Cp, 'lm': res.lm, 'uCc': res.uCc, 'tcc': res.tcc })
            }
         }
      }).catch((error) => {
         // history.push("/")
      }).finally(() => {
         // An aborted request is a route change: the bar is unmounted with the
         // page, and completing a ref that is already gone would throw.
         if (global.PageTopLoader.current) global.PageTopLoader.current.complete();
      });

      return () => {
         controller.abort();
      };

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [effectupdate]);

   const viewAnalysis = () => {
      setAiRunStatus(olddata => ({ ...olddata, "Astatus": "COMP" }))
      setWait(false)
   }

   const startAnalysis = () => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token');
      const userid = cookies.get('session_userid');
      const grpid = cookies.get('activegrp');
      if (userid && grpid) {
         setAiRunStatus(olddata => ({ ...olddata, 'Astatus': "LOAD" }))
         var data = {
            'userid': userid,
            'grpid': grpid,
         };
         axios.post(global.apiurl + '/compai/startanalysis', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if (res.st !== 1) {
               setAiRunStatus(olddata => ({ ...olddata, 'Astatus': "VOID" }))
               // setAstatus(false)
               toast.error(res.message)
            } else {
               if (res.Eg !== 1) {
                  setAiRunStatus(olddata => ({ ...olddata, 'Astatus': "VOID" }))
                  toast.warning("Right now we are under maintenance. We will be back soon.")
               } else if (res.Ac > 0) {
                  setAiRunStatus(olddata => ({ ...olddata, 'Astatus': "VOID" }))
                  toast.warning("Another project Competitor Analysis in process.")
               } else {
                  setAiRunStatus(olddata => ({ ...olddata, 'Astatus': "SCHD", 'tlk': res.tlk }))
                  onAnalysisTriggerFunc.current()
               }
               // history.push('/topcompetitors');
            }
         }).catch((error) => {
            // history.push("/")
         });
      }
   }

   const statusUpdate = (data) => {
      setAiRunStatus(olddata => ({ ...olddata, ...data }))
      if (data.Astatus && data.Astatus === "WAIT") {
         clearInterval(intervalRef.current);
         intervalRef.current = null;
         document.querySelectorAll(".progress-value").forEach(el => el.remove());
         setWait(true)

         setTimeout(() => {
            viewAnalysis()
         }, 5000);
      }
   }

   const dataUpdate = (data) => {
      setAiRunStatus(olddata => ({ ...olddata, 'fullCp': data, 'Cp': data }))
   }

   const filterdataUpdate = (data) => {
      setAiRunStatus(olddata => ({ ...olddata, 'Cp': data }))
   }

   const pageUpdate = () => {
      setAiRunStatus(olddata => ({ ...olddata, 'Astatus': "INIT", 'Cl': {}, 'fullCp': [], 'Cp': [], 'lm': 1, 'uCc': 0, 'Ac': 0, 'trk': 0, 'tlk': 0, 'trd': 0 }))
      setEffectupdate(!effectupdate)
   }

   return (
      <>
         {/* INIT is "the status request has not answered yet". The top progress
             line above is the whole loading state for it; a second, centred bar
             on a blank h100vh was the same message in a second idiom. */}
         {aiRunStatus.Astatus === "INIT" ?
            <div className="layout" role="status" aria-live="polite" aria-busy="true">
               <span className="visually-hidden">Loading competitors</span>
            </div>
            :
            <section className="layout">
               <CompetitorHeader aiRunStatus={aiRunStatus} dataUpdate={dataUpdate} pageUpdate={pageUpdate} projectList={props.projectList} fullbasedata={props.fullbasedata} filterdataUpdate={filterdataUpdate} compProjectPageLimit={compProjectPageLimit} canAdd={canAddCompetitor} canReanalyse={canReanalyseCompetitors} />

               {aiRunStatus.Astatus === "COMP" ?
                  <TopCompetitorsList aiRunStatus={aiRunStatus} statusUpdate={statusUpdate} canAdd={canAddCompetitor} />
                  : aiRunStatus.Astatus === "OVER" ?
                     <>
                        {aiRunStatus.Cp.length > 0 ?
                           <>
                              <CompetitorProjects aiRunStatus={aiRunStatus} statusUpdate={statusUpdate} pageUpdate={pageUpdate} compProjectPageLimit={compProjectPageLimit} />
                              <CompProjectRefreshStatus homedata={aiRunStatus.fullCp} homeApi={dataUpdate} pageurl={"competitors"} />
                           </>
                           :
                           <div className="emptyState">
                              <p className="emptyState__label">Competitors</p>
                              <p className="emptyState__body">
                                 No competitor is being tracked against this project yet. Add one with
                                 Top competitors, above.
                              </p>
                           </div>
                        }
                     </>
                     :
                     <div className="cp-robo">
                        <div>
                           <div className="d-flex align-items-center justify-content-center">
                              {aiRunStatus.Astatus === "SCHD" || aiRunStatus.Astatus === "WAIT" ?
                                 <div className="d-none d-md-block">
                                    <Fade in={aiRunStatus.Astatus === "SCHD" || aiRunStatus.Astatus === "WAIT"} {...(aiRunStatus.Astatus === "SCHD" ? { timeout: 750 } : { timeout: 1000 })}>
                                       <Box sx={{ width: "176px", marginBottom: "100px" }}>
                                          <div className="sandalBtn w-100 d-flex align-items-center text-center lh28x p-b5 bdr-5x">Analyzing your keywords</div>
                                          <div className="progressbar" id="progressbar1">
                                             {wait ? <div className="progress-full"></div> : null}
                                          </div>
                                       </Box>
                                    </Fade>
                                    <Fade in={aiRunStatus.Astatus === "SCHD" || aiRunStatus.Astatus === "WAIT"} {...(aiRunStatus.Astatus === "SCHD" ? { timeout: 750 } : { timeout: 1000 })}>
                                       <Box sx={{ width: "176px", marginLeft: { md: "0", xl: "20px" } }} >
                                          <div className="pinkBtn w-100 d-flex align-items-center text-center lh28x p-b5 bdr-5x">Finding the competitors</div>
                                          <div className="progressbar" id="progressbar2">
                                             {wait ? <div className="progress-full"></div> : null}
                                          </div>
                                       </Box>
                                    </Fade>
                                 </div>
                                 : null}
                              <div aria-hidden="true">
                                 <DataEmptyIcon width={160} height={132} />
                              </div>
                              {aiRunStatus.Astatus === "SCHD" || aiRunStatus.Astatus === "WAIT" ?
                                 <div className="d-none d-md-block">
                                    <Fade in={aiRunStatus.Astatus === "SCHD" || aiRunStatus.Astatus === "WAIT"} {...(aiRunStatus.Astatus === "SCHD" ? { timeout: 750 } : { timeout: 1000 })}>
                                       <Box sx={{ width: "176px", marginBottom: "100px", marginTop: "30px" }}>
                                          <div className="lgreenBtn w-100 d-flex align-items-center text-center lh28x p-b5 bdr-5x">Filtering the competitors</div>
                                          <div className="progressbar" id="progressbar3">
                                             {wait ? <div className="progress-full"></div> : null}
                                          </div>
                                       </Box>
                                    </Fade>
                                    <Fade in={aiRunStatus.Astatus === "SCHD" || aiRunStatus.Astatus === "WAIT"} {...(aiRunStatus.Astatus === "SCHD" ? { timeout: 750 } : { timeout: 1000 })}>
                                       <Box sx={{ width: "176px", marginLeft: "-25px" }}>
                                          <div className="lorangeBtn w-100 d-flex align-items-center text-center lh28x p-b5 bdr-5x">Collecting information</div>
                                          <div className="progressbar" id="progressbar4">
                                             {wait ? <div className="progress-full"></div> : null}
                                          </div>
                                       </Box>
                                    </Fade>
                                 </div>
                                 : null}
                           </div>
                           <div className="text-center">
                              <Title>Competitor AI</Title>
                              {aiRunStatus.Astatus === "SCHD" || aiRunStatus.Astatus === "WAIT" ?
                                 <Para class="m-b0">
                                    <span className="pClr fM">{aiRunStatus.trk}</span>/<span className="pClr fM">{aiRunStatus.tlk}</span> keywords match identified and <span className="pClr fM">{aiRunStatus.trd}</span> domains tracked</Para>
                                 :
                                 <Para class="m-b0">Point it at a competitor and it tracks their SEO progress alongside yours.</Para>
                              }
                              {(aiRunStatus.Astatus === "COMP" || aiRunStatus.Astatus === "WAIT" || canReanalyseCompetitors) ? <div className="startAnalysisBtn">
                                 <AppButton
                                    onclick={(aiRunStatus.Astatus === "COMP" || aiRunStatus.Astatus === "WAIT") ? viewAnalysis : startAnalysis}
                                    value={(aiRunStatus.Astatus === "COMP" || aiRunStatus.Astatus === "WAIT") ? "View Analysis" : aiRunStatus.Astatus === "FAIL" ? "Reanalysis" : "Start Analysis"}
                                    noIcon="d-none"
                                    loading={(aiRunStatus.Astatus === "LOAD" || aiRunStatus.Astatus === "SCHD") ? true : false}
                                 />
                              </div> : null}
                           </div>
                        </div>
                     </div>
               }
            </section>
         }
         <AnalysisStatus onAnalysisTriggerFunc={onAnalysisTriggerFunc} aiRunStatus={aiRunStatus} statusUpdate={statusUpdate} pageUpdate={pageUpdate} pageurl={"competitors"} />
      </>
   );
}


export default CompetitorAnalysis;
