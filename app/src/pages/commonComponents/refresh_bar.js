import React, { useEffect, useState } from "react";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';

import ProgressBar from "./progressBar";
import { RefreshIcon } from "./icons";
import { Tsk } from "./parts";

//
export default function RefreshBar({ onRefreshTriggerFunc, onRefreshCheckFunc, kwids, refresh_on, refreshUpdate, pageurl, pjtid }) {

   const [mRPT, setmRPT] = useState(0);
   const [mRCK, setmRCK] = useState(null);
   const [mRTK, setmRTK] = useState(null);

   // Both polls are started imperatively through the refs the parent holds, so
   // no effect owns them. Each one stops itself only once a response comes back
   // showing the path changed -- which is one tick too late: by then the
   // component is unmounted and setmRPT/refreshUpdate run on nothing. Tear the
   // intervals, the in-flight request and the completion timeout down here.
   const rankPollRef = React.useRef(null);
   const volPollRef = React.useRef(null);
   const doneTimerRef = React.useRef(null);
   // A manual refresh is processed by the ranking engine, which a scheduler
   // drives. On an instance where that scheduler is not running the count never
   // moves and the bar span forever. Cap the poll so it reports honestly and
   // stops instead of spinning without end. 36 polls x 5s = 3 minutes, well
   // past a real refresh of a handful of keywords.
   const attemptsRef = React.useRef(0);
   const MAX_REFRESH_POLLS = 36;
   const abortRef = React.useRef(null);
   if (abortRef.current === null) {
      abortRef.current = new AbortController();
   }
   useEffect(() => () => {
      clearInterval(rankPollRef.current);
      clearInterval(volPollRef.current);
      clearTimeout(doneTimerRef.current);
      abortRef.current.abort();
   }, []);

   useEffect (() => {
      onRefreshTriggerFunc.current = onRefreshTrigger
      onRefreshCheckFunc.current = onRefreshCheck
      
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [kwids], pjtid);

   const onRefreshCheck = (userid, grpid, rftype) => {

      setmRPT(0);
      setmRCK(null);
      setmRTK(null);
      if(rftype !== "onv"){
         onRefreshCompleteCheck(userid, grpid)
      }else if(rftype !== "onk"){
         onRefreshVolumeCheck(userid, grpid)
      }
   }

   const onRefreshTrigger = () => { 
       // this.setState({manualRefreshRestrict: "onload", refresh_on: true,})
      setmRPT(0);
      setmRCK(null);
      setmRTK(null);
      // const selted = [this.state.kwid];
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      const grpid = cookies.get('activegrp')
      if (!grpid) { return; }   // no project: nothing to ask about


      var data = {
         'userid': userid,
         'grpid': grpid,
         'ids': kwids,
      };
      axios.post(global.apiurl + '/usercrawl', data, {
         headers: {'Authorization': 'Token '+ usertoken }
      }).then(response => {
         return response.data;
      }).then(res => {  
         if (res.status === "true") {
            refreshUpdate(true);
            onRefreshCompleteCheck(userid, grpid)
         } else {
            toast.error(res.message);
            refreshUpdate(false);
            // this.setState({manualRefreshRestrict: "enable", refresh_on: false,})
         }
      }).catch((error) => {
         // history.push("/")
         toast.error("Please! Try again later.") 
         refreshUpdate(false);
           // this.setState({manualRefreshRestrict: "enable", refresh_on: false,})
      });
   }

   const grpConfirm = (projectid) =>{
      const cookies = new Cookies();
      const grpid = cookies.get('activegrp')
      if (!grpid) { return; }   // no project: nothing to ask about
      // console.log("test in fun ",projectid, grpid)
      return projectid !== grpid 
   }

   const onRefreshCompleteCheck = (userid, projectid) => {
      var ajaxRefreshCall = "ACTIVE" 
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      // const grpid = cookies.get('activegrp')
      attemptsRef.current = 0;

      rankPollRef.current = setInterval(async () => {
         if (ajaxRefreshCall === "ACTIVE") { 
            ajaxRefreshCall = "DEACTIVE" 
            attemptsRef.current += 1;
            if (attemptsRef.current > MAX_REFRESH_POLLS) {
               clearInterval(rankPollRef.current);
               refreshUpdate(false);
               toast.info("Refresh is taking longer than expected. Scheduled processing may not be running on this instance.");
               return;
            }

            var data = {
               'userid': userid,
               'grpid': projectid,
               'cntid': 'onload',
            };
            axios.post(global.apiurl + '/refreshstatus', data, {
               headers: {'Authorization': 'Token '+ usertoken },
               signal: abortRef.current.signal
            }).then(response => {
               return response.data;
            }).then(res => {

               if (res.status === "true") {

                  const mrSuccessKeyword = parseInt(res.LUC) - parseInt(res.runkeyword)
                  const mrRemainPercent = parseInt((mrSuccessKeyword / parseInt(res.LUC)) * 100)
                  setmRTK(parseInt(res.LUC));
                  setmRCK(mrSuccessKeyword);
                  setmRPT(mrRemainPercent);
                  // setmRPT(mrRemainPercent > 1 ? mrRemainPercent : mRPT);

                  if(!window.location.pathname.toString().includes(pageurl) || grpConfirm(projectid)){
                     clearInterval(rankPollRef.current);
                     refreshUpdate(false);
                     // this.setState({ manualRefreshRestrict: "enable", refresh_on: false })
                  }else if(res.Engmd === 0){
                     clearInterval(rankPollRef.current);
                     refreshUpdate(false);
                     // this.setState({ manualRefreshRestrict: "enable", refresh_on: false })
                     toast.error("Manual refresh is currently disabled. You'll have it back soon."); 
                  }else if(res.errc) {
                     /* Any errc is terminal, so this is checked BEFORE the
                        done-and-drained test rather than inside it.

                        Three of the codes are raised while a run is still
                        nominally in flight -- serp/refresh_error.py answers
                        `nokey` and `keyunreadable` from the live key state
                        before it looks at any run record at all, and
                        `engine_disabled` fires precisely when refresh_status is
                        "start" or "wait" with no ENGINE_TRIGGER_TOKEN to drain
                        the queue. None of them can resolve by waiting. Checked
                        only on `runkeyword === 0` they would never fire: the
                        poller would spend all 36 attempts and then report
                        "taking longer than expected", which is a worse answer
                        than "you have not added a DataBlue key". The other
                        three (engine_unreachable, serp_rate_limited,
                        serp_failed) are written when a run drains, so
                        runkeyword is already 0 and stopping is what would have
                        happened anyway.

                        `err` is rendered verbatim: the engine writes it with
                        counts this side cannot reconstruct ("3 of 5 keywords
                        could not be checked"). Contract: fix-backend.md, B-03. */
                     clearInterval(rankPollRef.current);
                     toast.error(res.err || 'The refresh could not be completed.');
                     refreshUpdate(false);
                  }else if(parseInt(res.runkeyword) === 0 && res.rst === "done") {     
                     clearInterval(rankPollRef.current);
                     /* runkeyword reaching 0 means the run STOPPED, not that it
                        worked -- the engine clears the running flag on its
                        error paths too, so "done" with 0 remaining was also
                        what total failure looked like, and this reported "SERP
                        Data loaded successfully" over it. Reaching here with
                        errc empty is the one state that is genuinely success.

                        `fkw` is deliberately not consulted: it is a STANDING
                        count of keywords with no current rank data, not this
                        run's result, so a project that has since recovered
                        would re-announce an old failure on every poll. It
                        belongs on a persistent badge, not in a per-run toast. */
                     toast.success('SERP Data loaded successfully.');
                     // refreshUpdate(false);
                     // this.setState({ manualRefreshRestrict: "enable", refresh_on: false })
                     doneTimerRef.current = setTimeout(() => { 
                        // this.setState({kwdataloading: true, comptrLoading: true, AdsLoading: true})
                        
                        refreshUpdate(false, "success")
                     }, 1000); 
                  } else {
                     ajaxRefreshCall = "ACTIVE" 
                  }
                   
               } else {
                  toast.error(res.message);
                  refreshUpdate(false);
                  // this.setState({ manualRefreshRestrict: "enable", refresh_on: false })
               }                       
            }).catch((error) => {
               // The unmount cleanup already cleared the interval: no failure to
               // report, and nobody left to show a toast to.
               if (axios.isCancel(error)) {
                  return
               }
               clearInterval(rankPollRef.current);
               toast.success('Please! Try after sometime.');
               refreshUpdate(false);
                // this.setState({ manualRefreshRestrict: "enable", refresh_on: false })
            });
         } 
      }, 5000); 
   }

   const onRefreshVolumeCheck = (userid, projectid) => {
      var volRefreshCall = "ACTIVE"
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      // const grpid = cookies.get('activegrp')

      volPollRef.current = setInterval(async () => {
         if (volRefreshCall === "ACTIVE") { 
            volRefreshCall = "DEACTIVE" 

            var data = {
               'userid': userid,
               'grpid': projectid,
               'cntid': 'onvol',
            };
            axios.post(global.apiurl + '/refreshstatus', data, {
               headers: {'Authorization': 'Token '+ usertoken },
               signal: abortRef.current.signal
            }).then(response => {
               return response.data;
            }).then(res => {
               if (res.status === "true") { 
                  if(!window.location.pathname.toString().includes(pageurl) || grpConfirm(projectid)){
                     clearInterval(volPollRef.current);
                     refreshUpdate(false);
                     // this.setState({ manualRefreshRestrict: "enable", refresh_on: false })
                  }else if(parseInt(res.runkeyword) === 0) {    
                     clearInterval(volPollRef.current);
                     refreshUpdate(false, "success");
                     // this.props.parentCallback("success"); 
                  } else {
                     volRefreshCall = "ACTIVE" 
                  }
               } else {
                     clearInterval(volPollRef.current);
                     refreshUpdate(false, "error");
                    // this.props.parentCallback("error"); 
               }                       
            }).catch( err => {
               // The unmount cleanup already cleared the interval and there is
               // nothing left to update.
               if (axios.isCancel(err)) {
                  return
               }
               clearInterval(volPollRef.current);
               refreshUpdate(false, "error");
               // this.props.parentCallback("error"); 
            });
         } 
      }, 10000);  
   }


   return (
       refresh_on ?
         <div className="reFreshing">
            <div className="refreshProgressContent">
               <div className="d-flex justify-content-between w-100">
                  <div className="d-flex align-items-center gap-2 m-b10">
                     <span className="d-flex">{<RefreshIcon />}</span>
                     <p className="mb-0">Refreshing...</p>
                  </div>
                  <p className="fB mb-0 d-flex" style={{ color:"var(--accent)" }}>
                     { (mRCK || mRCK === 0) ? mRCK : <Tsk width={25} />}/{mRTK ? mRTK : <Tsk width={25} />}
                  </p>
               </div>
               <ProgressBar bgcolor={"#1a3cff"} bglightcolor={"#cdd7ff"} completed={mRPT} />
            </div>
         </div>
      : null
   );
}
