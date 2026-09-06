import React, { useState, useEffect, useRef } from "react";
import { Title, Para, AppButton } from "../commonComponents/parts";
import { KSearch } from "../commonComponents/icons";
import "./style.scss";
import GSearch from "../../assets/images/keywordResearch/gsearch.svg";
import Notes from "../../assets/images/keywordResearch/notes.svg";
import SNotes from "../../assets/images/keywordResearch/snotes.svg";
import BGraph from "../../assets/images/keywordResearch/graph.svg";
import { Grid } from "@mui/material";
import { TextField } from "@mui/material";
import CEditRegionList from "./components/cedit_region_list";
import { spacing } from "@mui/system";
import { toast } from 'react-toastify';
import Cookies from "universal-cookie";
import axios from "axios";
import CEditSecondaryKeywords from "./components/cedit_secondary_keywords";


function CEditOnboardInfo({ ...props }) {

   const primaryKeywordRef = useRef(null);

   const [planData, setPlanData] = useState({
      primaryKeyword: "",
      secondaryKeywords: [],
      btnloading: false,
      regionDetails: {
         countryname: props.kwdSearchDetails.Rcnt,
         region: props.kwdSearchDetails.RN,
         isocode: props.kwdSearchDetails.Rcd
      },
   });

   const handleSecondaryKeywords = (newKeywords) => {
      setPlanData((prevState) => ({
         ...prevState,
         secondaryKeywords: newKeywords,
      }));
   };

   const rgDataUpdate = (data) => {
      setPlanData(prev => ({
         ...prev,
         regionDetails: {
            countryname: data.countryname,
            region: data.region,
            isocode: data.isocode
         }
      }));
   }

   const showToast = (type, message) => {
      toast.dismiss()
      if (type === "success") {
         toast.success(message)
      } else {
         toast.error(message)
      }
   }

   useEffect(() => {
      const contentPlannerSeed = JSON.parse(localStorage.getItem('contentPlannerSeed') || 'null');
      if (contentPlannerSeed && contentPlannerSeed.primaryKeyword) {
         setPlanData((prevState) => ({
            ...prevState,
            primaryKeyword: contentPlannerSeed.primaryKeyword,
            secondaryKeywords: Array.isArray(contentPlannerSeed.secondaryKeywords)
               ? contentPlannerSeed.secondaryKeywords.slice(0, 5)
               : [],
         }));
         localStorage.removeItem('contentPlannerSeed');
      }

      if (localStorage.getItem('contentPlannerForm')) {
         localStorage.removeItem("contentPlannerForm")
      }

      if (primaryKeywordRef.current) {
         primaryKeywordRef.current.focus();
      }

   }, []);

   let { primaryKeyword, secondaryKeywords, regionDetails, btnloading } = planData;

   const createContentPlan = () => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      const grpid = cookies.get('activegrp')
      if (!grpid) { return; }   // no project: nothing to ask about
      let region_name = regionDetails.region
      let region_code = regionDetails.isocode
      let country_name = regionDetails.countryname

      if (primaryKeyword.trim() === "") {
         showToast("error", "Enter your primary keyword")
         return false;
      } else if (primaryKeyword.length < 3) {
         showToast("error", "Primary Keyword should be minimum 3 characters in length")
         return false;
      } else if (secondaryKeywords.length > 0 && secondaryKeywords.includes(primaryKeyword)) {
         showToast("error", "Secondary keywords must not match your primary keyword.")
         return false;
      } else if (country_name.length === 0) {
         showToast("error", "Select your region")
         return false;
      } else {
         setPlanData(prev => ({ ...prev, btnloading: true }));
         axios.post(global.apiurl + '/contentmanager/create', {
            'userid': userid,
            'grpid': grpid,
            'primary_keyword': primaryKeyword.trim(),
            'secondary_keywords': secondaryKeywords,
            'region_name': region_name,
            'region_code': region_code,
            'country_name': country_name,
         }, {
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if (res.status === "true") {
               showToast("success", res.message)
            } else {
               showToast("error", res.message)
            }
            setPlanData(prev => ({
               ...prev,
               primaryKeyword: "",
               secondaryKeywords: [],
               regionDetails: {
                  countryname: "United States",
                  region: "google.com",
                  isocode: "us",
               },
               btnloading: false
            }));
            props.refetchContentPlans()
         }).catch((error) => {
            console.log(error)
            showToast("error", "Something went wrong")
            setPlanData(prev => ({
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
               <Title class="kr_title">Content Planner</Title>
               <Para class="kr_para">Create and optimize your content with real-time NLP analysis</Para>
            </div>

            <div className="d-flex flex-wrap gap-3 m-t40 justify-content-center align-items-center">
               <div className="col-5 d-grid gap-3">
                  <div className="kr_srch">
                     <TextField
                        inputRef={primaryKeywordRef}
                        className="search kr_searchInput kr_rsearchInput"
                        label=""
                        type="search"
                        inputProps={{ maxLength: 512 }}
                        variant="outlined"
                        fullWidth
                        autoFocus={true}
                        placeholder="Primary Keyword"
                        value={primaryKeyword}
                        onChange={(e) => setPlanData({ ...planData, primaryKeyword: e.target.value })}
                        autoComplete="off"
                        classes={{ clearIndicator: { color: "red" } }}
                     />
                  </div>
                  <div className="kr_region kr_rregion">
                     <CEditRegionList regionData={props.regionData} lastKwdRegion={planData.regionDetails} rgDataUpdate={rgDataUpdate} />
                  </div>
               </div>
               <div className="col-5">
                  <div>
                     <CEditSecondaryKeywords primaryKeyword={primaryKeyword} secondaryKeywords={secondaryKeywords} handleSecondaryKeywords={handleSecondaryKeywords} />
                  </div>
               </div>
            </div>
            <div className="d-flex justify-content-center gap-3 p-b25 p-t25">
               <AppButton
                  value="Create"
                  class="kr_searchbtn"
                  onclick={createContentPlan}
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
                        <Para class="m-t25 f16x"> {"Scan your website and competitors to collect all ranking keywords, SEO metrics, and content data for deep insights."}</Para>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={3}>
                     <div className="kr_grid">
                        <img src={BGraph} alt="" width={55} height={60} />
                        <Para class="m-t25 f16x">{"Organize keywords by topic, intent, and relevance — forming keyword clusters that align with user needs and search patterns."}</Para>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={3}>
                     <div className="kr_grid">
                        <img src={GSearch} alt="" width={55} height={60} />
                        <Para class="m-t25 f16x">{"Compare your keyword presence with competitors. Identify keyword gaps, high-potential areas, and ranking opportunities"}</Para>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={3}>
                     <div className="kr_grid">
                        <img src={SNotes} alt="" width={55} height={60} />
                        <Para class="m-t25 f16x">{"Allow content ideas to seamlessly redirect to the built-in content editor — enabling your team to write and optimize content efficiently."}</Para>
                     </div>
                  </Grid>
               </Grid>
            </div>
         </div>
      </>
   );
}

export default CEditOnboardInfo; 
