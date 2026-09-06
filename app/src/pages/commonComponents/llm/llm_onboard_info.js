import React, { useState, useEffect } from "react";
import { Title, Para, AppButton } from "../parts";
import { KSearch } from "../icons";
import "../../llmTracker/style.scss";
import GSearch from "../../../assets/images/keywordResearch/gsearch.svg";
import Notes from "../../../assets/images/keywordResearch/notes.svg";
import SNotes from "../../../assets/images/keywordResearch/snotes.svg";
import BGraph from "../../../assets/images/keywordResearch/graph.svg";
import { Grid } from "@mui/material";
import { toast } from 'react-toastify';
import Cookies from "universal-cookie";
import axios from "axios";
import LLMPrompts from "./llm_prompts";


function LLMOnboardInfo({ ...props }) {

   const [promptData, setPromptData] = useState({
      prompts: [],
      btnloading: false,
   });

   const handlePrompts = (newPrompts) => {
      setPromptData((prevState) => ({
         ...prevState,
         prompts: newPrompts,
      }));
   };

   const showToast = (type, message) => {
      toast.dismiss()
      if (type === "success") {
         toast.success(message)
      } else {
         toast.error(message)
      }
   }

   useEffect(() => {

      const savedPrompts = JSON.parse(localStorage.getItem('llmSavedPrompts') || '[]');
      if (savedPrompts.length > 0) {
         setPromptData((prevState) => ({
            ...prevState,
            prompts: savedPrompts.slice(0, 5),
         }));
         localStorage.removeItem("llmSavedPrompts")
      }

      if (localStorage.getItem('llmTrackerForm')) {
         localStorage.removeItem("llmTrackerForm")
      }

   }, []);

   let { prompts, btnloading } = promptData;

   const createLLMPrompt = () => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      const grpid = cookies.get('activegrp');
      if (!grpid) { return; }   // no project: nothing to ask about

      if (prompts.length === 0) {
         showToast("error", "Enter your prompts")
         return false;
      } else {
         setPromptData(prev => ({ ...prev, btnloading: true }));
         axios.post(global.apiurl + '/llmtracker/add', {
            'userid': userid,
            'groupid':grpid,
            'prompts': prompts,
         }, {
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if (res.status === "true") {
               showToast("success", res.message)
               props.onCreated?.()
            } else {
               showToast("error", res.message)
            }
            setPromptData(prev => ({
               ...prev,
               prompts: [],
               btnloading: false
            }));
            props.refetchLLMPrompts()
         }).catch((error) => {
    
            showToast("error", "Something went wrong")
            setPromptData(prev => ({
               ...prev,
               btnloading: false
            }));
         });
      }
   }

   return (
      <>
         <div className="kr_layout">
            <div className="justify-content-center text-center p-t80">
               <Title class="kr_title">Geo Citations</Title>
               <Para class="kr_para">Track and monitor your brand mentions across different AI models and platforms</Para>
            </div>

            <div className="d-flex justify-content-center m-t40 prompts-section">
                              <div className="col-6">
                  <div className="prompts-container">
                     <div className="prompts-title">Enter Your Prompts</div>
                     <LLMPrompts prompts={prompts} handlePrompts={handlePrompts} />
                  </div>
               </div>
            </div>
            <div className="d-flex justify-content-center gap-3 p-b25 p-t25">
               <AppButton
                  value="Create"
                  class="kr_searchbtn"
                                       onclick={createLLMPrompt}
                  loading={btnloading}
                  Icon={<KSearch width='15' height='15' />}
                  noIcon="p-r10"
               />
            </div>
            <div className="d-flex flex-wrap">
               <Grid container>
                  <Grid item xs={12} md={6} lg={3}>
                     <div className="kr_grid">
                        <img src={Notes} alt="" width={55} height={60} />
                        <Para class="m-t25 f16x"> {"Track your prompts across multiple AI models to understand which ones perform best for your specific use cases."}</Para>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={3}>
                     <div className="kr_grid">
                        <img src={BGraph} alt="" width={55} height={60} />
                        <Para class="m-t25 f16x">{"Monitor prompt performance metrics and identify patterns that lead to better AI responses and outcomes."}</Para>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={3}>
                     <div className="kr_grid">
                        <img src={GSearch} alt="" width={55} height={60} />
                        <Para class="m-t25 f16x">{"Compare prompt effectiveness across different AI platforms and models to optimize your AI strategy."}</Para>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={3}>
                     <div className="kr_grid">
                        <img src={SNotes} alt="" width={55} height={60} />
                        <Para class="m-t25 f16x">{"Generate insights and reports on prompt performance to continuously improve your AI interactions."}</Para>
                     </div>
                  </Grid>
               </Grid>
            </div>
         </div>
      </>
   );
}

export default LLMOnboardInfo; 
