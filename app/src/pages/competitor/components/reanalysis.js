import React, { useState } from "react";
import Cookies from 'universal-cookie';
import { AppIconButton,AppButton } from "../../commonComponents/parts";
import { Tooltip } from "@mui/material";
import Zoom from '@mui/material/Zoom';
import { toast } from 'react-toastify';
import { useHistory } from "react-router-dom";
import axios from 'axios';
import { NavSpark } from "../../commonComponents/railIcons";
 
function ReanalysisComponent(props) {

   const[loading,setLoading] = useState(false);
   const history = useHistory();

   const startAnalysis = () =>{
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token');
      const userid = cookies.get('session_userid');
      const grpid = cookies.get('activegrp');
      if(props.addlm <= 0){
         toast.error("Sorry! You have reached your limit.")  
      }else if(userid && grpid) {
         setLoading(true)
         var data = {
            'userid': userid,
            'grpid': grpid,
         };
         axios.post(global.apiurl + '/compai/startanalysis', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if(res.st !== 1){
               toast.error(res.message)  
            }else {
               if(res.Eg !== 1){
                  toast.warning("Right now we are under maintenance. We will be back soon.");
                  setLoading(false); 

               }else if(res.Ac > 0){
                  toast.warning("Another project Competitor in Analysis process.");
                  setLoading(false);
               }else{
                  // if(!window.location.pathname.toString().includes(pageurl)){
                  // }
                  if(props.pageUpdate){
                     props.pageUpdate()
                     // props.statusUpdate({'Astatus':"SCHD", 'tlk':res.tlk})
                     // props.onReanalysisTriggerFunc.current()
                  }else{
                     history.push('/competitors');
                  }

               }
            }
         }).catch((error) => {
            // history.push("/")
         });
      }
   }
   return (
      <>
      {props.pageType === "comparison"?
         <>
         <AppButton
            value="Start Analysis"
            noIcon="d-none"
            onclick={startAnalysis}
            loading={loading}
         />
         </>
      :
      <Tooltip title="Reanalysis" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
         <div>
            <AppIconButton 
               onclick={startAnalysis}
               aria-label="Re-analyse competitors"
               class="compLottieIcon" 
               Icon={ 
                  loading ?
                     <span className="loading loading--inline" />
                  :
                     <NavSpark />
                  } 
            />    
         </div>
      </Tooltip>
      }
      </>
   );
}

export default ReanalysisComponent;