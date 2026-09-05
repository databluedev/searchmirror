import React, { useEffect } from "react";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';

export default function AnalysisStatus({ onAnalysisTriggerFunc, aiRunStatus, statusUpdate, pageUpdate, pageurl }) {

   const [statusCheck, setStatusCheck] = React.useState(false);

   // The poll is started by the parent through onAnalysisTriggerFunc, so no
   // single effect owns it. Without this teardown the interval, its in-flight
   // request and the completion timeout all survive the route change and then
   // call setStatusCheck/statusUpdate on a component that is gone.
   const pollRef = React.useRef(null);
   const doneTimerRef = React.useRef(null);
   const abortRef = React.useRef(null);
   if (abortRef.current === null) {
      abortRef.current = new AbortController();
   }

   useEffect (() => {
      onAnalysisTriggerFunc.current = onAnalysisStatusUpdate
      // console.log("test Competitor")

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, []);

   useEffect(() => () => {
      clearInterval(pollRef.current);
      clearTimeout(doneTimerRef.current);
      abortRef.current.abort();
   }, []);

   const grpConfirm = (projectid=0) =>{
      const cookies = new Cookies();
      const grpid = cookies.get('activegrp')
      // console.log("test in fun ",projectid, grpid)
      return projectid !== grpid 
   }

   const onAnalysisStatusUpdate = () => {
      // console.log("test Competitor")
      if(statusCheck !== true){
         setStatusCheck(true)
         var ajaxRefreshCall = "ACTIVE" 
         const cookies = new Cookies();
         const grpid = cookies.get('activegrp');
         const userid = cookies.get('session_userid')
         const usertoken = cookies.get('session_token')

         pollRef.current = setInterval(async () => {
            if (ajaxRefreshCall === "ACTIVE") { 
               ajaxRefreshCall = "DEACTIVE" 

               var data = {
                  'userid': userid,
                  'grpid': grpid,
               };
               axios.post(global.apiurl + '/compai/analysisstatus', data, {
                  headers: {'Authorization': 'Token '+ usertoken },
                  signal: abortRef.current.signal
               }).then(response => {
                  return response.data;
               }).then(res => {

                  if (res.st === 1) {
                     if(!window.location.pathname.toString().includes(pageurl)  || grpConfirm(grpid) || res.As === "OVER"){
                        clearInterval(pollRef.current);
                        // statusUpdate({'Astatus':"VOID"})
                        setStatusCheck(false)
                     }else if(res.Eg === 0){
                        setStatusCheck(false)
                        clearInterval(pollRef.current);
                        toast.error("Right now we are under maintenance. We will be back soon."); 
                        statusUpdate({'Astatus':"VOID"})
                     }else if(res.As && res.As === "COMP") {      
                        clearInterval(pollRef.current);
                        toast.success('Competitor AI analysis completed!'); 
                        // toast.success('SERP Data loaded successfully.'); 
                        doneTimerRef.current = setTimeout(() => { 
                           // statusUpdate({'Astatus':"COMP", 'Cp':res.Cp, 'Cl': res.Cl, 'lm':res.lm, 'trk':res.Ad['track_keywords'], 'tlk':res.tlk, 'trd':res.Ad['total_domains']})
                           statusUpdate({'Astatus':"WAIT", 'fullCp':res.Cp, 'Cp':res.Cp, 'Cl': res.Cl, 'lm':res.lm, 'uCc':res.uCc, 'trk':res.Ad['track_keywords'], 'tlk':res.tlk, 'trd':res.Ad['total_domains'], 'tcc':res.tcc})
                           setStatusCheck(false)
                        }, 1000); 
                     }else if(res.As && res.As === "FAIL") {     
                        clearInterval(pollRef.current);
                        toast.error('Competitor AI analysis Failed, Please! try after sometime.'); 
                        // toast.success('SERP Data loaded successfully.'); 
                        doneTimerRef.current = setTimeout(() => { 
                           statusUpdate({'Astatus':"FAIL"})
                           setStatusCheck(false)
                        }, 1000); 
                     } else {
                        if(res.As && res.As === "SCHD" && res.Ad){
                           statusUpdate({'Astatus':"SCHD", 'trk':res.Ad['track_keywords'], 'tlk':res.Ad['total_keywords'], 'trd':res.Ad['total_domains']})
                        }
                        ajaxRefreshCall = "ACTIVE" 
                     }
                  } else {
                     toast.error(res.message);
                     clearInterval(pollRef.current);
                     statusUpdate({'Astatus':"VOID"})
                     setStatusCheck(false)
                  }                       
               }).catch((error) => {
                  // The unmount cleanup already cleared the interval and there
                  // is nothing left to update.
                  if (axios.isCancel(error)) {
                     return
                  }
                  clearInterval(pollRef.current);
                  statusUpdate({'Astatus':"VOID"})
                  setStatusCheck(false)
                  // toast.success('Please! Try after sometime.');
               });
            } 
         }, 3000);  
      }
   }

   return (
      null
   );
}
