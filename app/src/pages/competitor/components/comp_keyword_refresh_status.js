import React, { useEffect } from "react";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';

export default function CompKeywordRefreshStatus({ refreshCnt, homeApi, pageurl }) {

   const [statusCheck, setStatusCheck] = React.useState(false);

   // The poll is kicked off from a data-driven effect and keeps ticking after
   // the route changes: without this teardown the interval, its in-flight
   // request and the completion timeout all outlive the component and then
   // update state on nothing.
   const pollRef = React.useRef(null);
   const doneTimerRef = React.useRef(null);
   const abortRef = React.useRef(null);
   if (abortRef.current === null) {
      abortRef.current = new AbortController();
   }
   useEffect(() => () => {
      clearInterval(pollRef.current);
      clearTimeout(doneTimerRef.current);
      abortRef.current.abort();
   }, []);

   useEffect (() => {
      
      // setPjtids(refresh_pjtid)
      if(statusCheck !== true && refreshCnt > 0){
         onRefreshCompleteCheck()
      }

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [refreshCnt]);

   const grpConfirm = (projectid=0,compPrjtid=0) =>{
      const cookies = new Cookies();
      const grpid = cookies.get('activegrp')
      const comp_grpid = cookies.get('__sp_cgrp__')
      return (projectid !== grpid || comp_grpid !== compPrjtid)
   }

   const onRefreshCompleteCheck = () => {
      setStatusCheck(true)
      var ajaxRefreshCall = "ACTIVE" 
      const cookies = new Cookies();
      const userid = cookies.get('session_userid')
      const grpid = cookies.get('activegrp')
      const comp_grpid = cookies.get('__sp_cgrp__')
      const usertoken = cookies.get('session_token')

      pollRef.current = setInterval(async () => {
         if (ajaxRefreshCall === "ACTIVE") { 
            ajaxRefreshCall = "DEACTIVE" 

            var data = {
               'userid': userid,
               'grpid': grpid,
               'cgrpid': comp_grpid,
            };
            axios.post(global.apiurl + '/compai/keywordstatus', data, {
               headers: {'Authorization': 'Token '+ usertoken },
               signal: abortRef.current.signal
            }).then(response => {
               return response.data;
            }).then(res => {

               if (res.st === 1) {
                  if(!window.location.pathname.toString().includes(pageurl) || grpConfirm(grpid,comp_grpid) ){
                     clearInterval(pollRef.current);
                     setStatusCheck(false)
                  }else if(res.Engmd === 0){
                     setStatusCheck(false)
                     clearInterval(pollRef.current);
                     // toast.error("Under maintenance mode. we'll back soon"); 
                     homeApi()
                  }else if(res.rkw === 0) {     
                     clearInterval(pollRef.current);
                     toast.success('SERP Data loaded successfully.'); 
                     doneTimerRef.current = setTimeout(() => { 
                        homeApi()
                        setStatusCheck(false)
                     }, 1000); 
                  } else {
                     ajaxRefreshCall = "ACTIVE" 
                  }
               } else {
                  toast.error(res.message);
                  clearInterval(pollRef.current);
                  setStatusCheck(false)
               }                       
            }).catch((error) => {
               // The unmount cleanup already cleared the interval and there is
               // nothing left to update.
               if (axios.isCancel(error)) {
                  return
               }
               clearInterval(pollRef.current);
               setStatusCheck(false)
               // toast.success('Please! Try after sometime.');
            });
         } 
      }, 10000);  
   }

   return (
      null
   );
}
