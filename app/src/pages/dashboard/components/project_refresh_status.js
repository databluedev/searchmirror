import React, { useEffect } from "react";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';

export default function ProjectRefreshStatus({ engineMode, homedata, homeApi, pageurl }) {

   const [pjtids, setPjtids] = React.useState([]);
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
      
      const refresh_pjtid = [] 
      homedata.forEach(item => {
        if (item.mrk === 1) {
          refresh_pjtid.push(item.GY);
        }
      });

      setPjtids(refresh_pjtid)
      if(statusCheck !== true && engineMode === 1 && refresh_pjtid.length > 0){
         onRefreshCompleteCheck(refresh_pjtid)
      }

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [homedata]);

   const onRefreshCompleteCheck = (projectids=pjtids) => {
      setStatusCheck(true)
      var ajaxRefreshCall = "ACTIVE" 
      const cookies = new Cookies();
      const userid = cookies.get('session_userid')
      const usertoken = cookies.get('session_token')

      pollRef.current = setInterval(async () => {
         if (ajaxRefreshCall === "ACTIVE") { 
            ajaxRefreshCall = "DEACTIVE" 

            var data = {
               'userid': userid,
               'grpid': projectids,
            };
            axios.post(global.apiurl + '/projectrefreshstatus', data, {
               headers: {'Authorization': 'Token '+ usertoken },
               signal: abortRef.current.signal
            }).then(response => {
               return response.data;
            }).then(res => {

               if (res.status === "true") {
                  if(!window.location.pathname.toString().includes(pageurl)){
                     clearInterval(pollRef.current);
                     setStatusCheck(false)
                  }else if(res.Engmd === 0){
                     setStatusCheck(false)
                     clearInterval(pollRef.current);
                     // toast.error("Under maintenance mode. we'll back soon"); 
                     homeApi()
                  }else if(res.grpids && (res.grpids.length === 0 || JSON.stringify(res.grpids) !== JSON.stringify(projectids))) {     
                     clearInterval(pollRef.current);
                     // toast.success('SERP Data loaded successfully.'); 
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
      }, 15000);  
   }

   return (
      null
   );
}
