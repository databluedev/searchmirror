import React, { useState,useEffect } from "react";
import {
   AppButton,
   SelectMenu,
   Input
} from "../../commonComponents/parts";
import { Grid } from "@mui/material";
import {general,profile} from '../../contentComponents/content.json';
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';
import { revealFormError } from "../../commonComponents/form_feedback";


const designations = global.designations;
const nameRegex = /^[a-zA-Z ]*$/;
const cszRegex = /^[a-zA-Z0-9-\b ]*$/;
// const addressRegex = /^[A-Za-z0-9'\.\-\s\_\#\(\)\/, ]*$/;
const addressRegex = /^[A-Za-z0-9\s,'./+\\_#()-]*$/;

function ProfileModule({ children, ...props }) {
   // One ref per required field, in the order they appear on screen. A blocked
   // submit scrolls the first offending field into view and focuses it.
   const nameRef = React.useRef(null);
   const ad1Ref = React.useRef(null);
   const designationRef = React.useRef(null);
   const countryRef = React.useRef(null);
   const stateRef = React.useRef(null);
   const cityRef = React.useRef(null);
   const zipRef = React.useRef(null);
   const [countryList,setCountryList] = useState([]);
   const [userName,setUserName] = useState('');
   const [userEmail,setUserEmail] = useState('');
   const [designation,setDesignation] = useState('');
   const [country,setCountry] = useState('');
   const [errorText, setErrorText] = React.useState();
   const [isFormSubmit, setIsFormSubmit] = useState(false);
   const [saveLoading,setSaveLoading] = useState(false);
   const [pageLoading,setPageLoading] = useState(true);
   
   const [userInfo,setUserInfo] = useState({
      ad1 : "as",
      ad2 : "sa",
      com : "sag",
      des : "",
      co : "",
      st : "",
      ct : "",
      zc : ""
   })
   const userInfoErrors = useState({
      ad1 : "",
      ad2 : "",
      com : "",
      des : "",
      co : "",
      st : "",
      ct : "",
      zc : ""
   })
   useEffect(() => {
      const cookies = new Cookies();
      const userid = cookies.get('session_userid');
      const usertoken = cookies.get('session_token');
      const name = cookies.get('session_username'); 
      const email = cookies.get('session_usermail');
	
      const data = {
         'userid': userid,
      };
      axios.post(global.apiurl + '/country_list', data, {
         headers: {'Authorization': 'Token '+ usertoken }
      }).then(response => {
         return response.data;
      }).then(res => {
         if(res.status === "true"){
            setCountryList(res.country_list)
         }
         else{
            toast.error(res.message)
         }
      });
      if(userid && usertoken && name && email){
         setUserName(name);
         setUserEmail(email)
      }
      axios.post(global.apiurl + '/profile_settings', data, {
         headers: {'Authorization': 'Token '+ usertoken }
      })
      .then(response => {
         return response.data;
      }).then(res => {
         if(res.status === "true"){
            const usrAddr = res.adrs;
            if(usrAddr.co){
               setCountry([usrAddr.co]);
            }
            if(usrAddr.des){
               setDesignation([usrAddr.des]);
            }
            setUserInfo({
               ad1: usrAddr.ad1 || "",
               ad2: usrAddr.ad2 || "",
               com: usrAddr.com || "",
               ct: usrAddr.ct || "",
               st: usrAddr.st || "",
               zc: usrAddr.zc || ""
            });
            setPageLoading(false)
         }else{
            toast.error(res.message)
         }
      });
      // eslint-disable-next-line react-hooks/exhaustive-deps
   },[]);

   const selectlstChange = (event) => {
      const { target: { value }, } = event;
  
      setDesignation(
        typeof value === "string" ? value.split(",") : value[0]
      );
   };
   const selectcountryChange = (event) => {
      const { target: { value }, } = event;

      setCountry(
         typeof value === "string" ? value.split(",") : value[0]
      );
   };

   const handleName = (event) => {
      if (event.target.value.match(nameRegex)) {
         if(event.target.value.length < 3){
            setErrorText("Should contain at least 3 characters in your name")
         }else{
            setErrorText("")
         }
         setUserName(event.target.value);
      }
   }
   const handleCSZ = (event) => {
      if (event.target.value.match(cszRegex)) {
         setUserInfo( {...userInfo,[event.target.name]: event.target.value} );
      }
   }
   const handleAddress = (event) => {
      if (event.target.value.match(addressRegex)){
         setUserInfo( {...userInfo,[event.target.name]: event.target.value} );
      }
   }

   const cancelButton = () =>{
      setUserInfo({
         ad1 : "",
         ad2 : "",
         com : "",
         des : "",
         co : "",
         st : "",
         ct : "",
         zc : ""
      });
      setDesignation('');
      setCountry('');
   }

   const formValidation = () => {
      var newusername = userName.trim();
      var add1 = userInfo.ad1 !== "" ? userInfo.ad1.trim() : userInfo.ad1;
      var cntry = country;
      var designatn = designation;
      var state = userInfo.st.trim();
      var city = userInfo.ct.trim();
      var zip = userInfo.zc.trim();

      /* The name is the only thing this form needs. The postal block --
         address, designation, country, state, city, ZIP -- came from the
         commercial product, where it was the invoicing address. This build has
         no billing (backend/payment is on disk and unrouted), and nothing in it
         reads those fields, so requiring them meant an operator could not
         correct the spelling of their own name without inventing a street
         address first. Country made it worse: /country_list answers with a
         single entry, so it is a mandatory dropdown with one option.

         The fields stay, because an instance may still want them on record.
         They are simply no longer a gate. */
      var required = [
         [newusername, nameRef, 'Name field is required!'],
      ];

      var missing = required.filter(function (field) { return field[0] === ''; })[0];
      if(missing){
         return { ref: missing[1], message: missing[2] };
      }

      if(newusername.length < 3){
         setErrorText("Should contain at least 3 characters in your name")
         return { ref: nameRef, message: "Should contain at least 3 characters in your name" };
      }
      else{
         return true;
      }
   }

   
   const handleSubmit = () =>{
      // e.preventDefault();
      setIsFormSubmit(true);
      const formSubmit = formValidation();
      if (formSubmit === true) {
         setIsFormSubmit(false);
         setSaveLoading(true);
         var userAddress = {
            ad1 : userInfo.ad1,
            ad2 : userInfo.ad2,
            com : userInfo.com,
            des : designation[0],
            co : country[0],
            st : userInfo.st,
            ct : userInfo.ct,
            zc : userInfo.zc
         }
         const cookies = new Cookies();
         const userid = cookies.get('session_userid');
         const usertoken = cookies.get('session_token')
         const data = {
            'userid': userid,
            'uname': userName,
            'adrs': userAddress
         };
         // console.log('.............dtasent',data);
         axios.post(global.apiurl + '/profile_settings', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if(res.status === "true"){
               toast.success(res.message)
               cookies.set('session_username', userName, { path: '/', maxAge: global.cookiesexpire });
               setSaveLoading(false);
            }else{
               toast.error(res.message)
               setSaveLoading(false);
            }
         });
         // console.log('...........user',data);
      } else {
         revealFormError(formSubmit.message, formSubmit.ref);
      }
   }
   return (
      <>
         {pageLoading ?
            <div className="d-flex justify-content-center align-items-center text-center h100vh">
               <div className="loading" /> 
            </div>
         :
         <>
         <div className="m-b70 m-t25 profile-page">
            <Grid container className="">
               <Grid item xs={12} md={12} lg={10}>
               <Grid container spacing={3} className="">
                  <Grid item xs={12} md={6} lg={6}>
                     <div ref={nameRef}>
                     <Input required={true} span={'*'} name="nm" 
                     // error={!!errorText} errmsg={errorText}
                     error={isFormSubmit ? userName === ""? true : !!errorText : false} 
                     errmsg={isFormSubmit ? userName === ""? 'Name field is required!' : errorText : ''} 
                         
                     label={general.name} placeholder="Enter name" maxlength={30} value={userName} onchange={handleName}/>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={6}>
                     <div>
                     <Input
                        label={general.email}
                        value={userEmail}
                        placeholder="Ex: user@gmail.com"
                        disabled={true}
                     />
                     </div>
                  </Grid>
                  <Grid item xs={12} md={12} lg={12}>
                     <Grid container spacing={3}>
                     <Grid item xs={12} md={6} lg={6}>
                        <div ref={ad1Ref}>
                           <Input label={profile.address} 
                           // error={!!userInfoErrors.ad1} errmsg={userInfoErrors.ad1} 
                           error={!!userInfoErrors.ad1} 
                           errmsg={userInfoErrors.ad1} 
                        
                           name="ad1" maxlength={75} placeholder={profile.address1} value={userInfo.ad1} onchange={handleAddress}/>
                        </div>
                     </Grid>
                     <Grid item xs={12} md={6} lg={6}>
                        <div>
                           <Input error={!!userInfoErrors.ad2} errmsg={userInfoErrors.ad2} name="ad2" maxlength={75} placeholder={profile.address2} value={userInfo.ad2} onchange={handleAddress}/>
                        </div>
                     </Grid>
                     </Grid>
                  </Grid>
                  <Grid item xs={12} md={6} lg={6}>
                     <div>
                     <Input name="com" 
                     error={!!userInfoErrors.com} errmsg={userInfoErrors.com} 
                     maxlength={100}  label={profile.company} placeholder={profile.company_name} value={userInfo.com} onchange={handleCSZ}/>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={6}>
                     <div className="dropdownSelect" ref={designationRef}>
                        <SelectMenu name="des" 
                        // error={!!userInfoErrors.des} errmsg={userInfoErrors.des} 
                        error={!!userInfoErrors.des} 
                        errmsg={userInfoErrors.des}
                        
                        label={general.designation} placeholder={general.select_yr_designation} menulist={designations} value={designation} onchange={selectlstChange}/>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={6}>
                     <div className="dropdownSelect" ref={countryRef}>
                     <SelectMenu 
                     // error={!!userInfoErrors.co} errmsg={userInfoErrors.co} 
                     error={!!userInfoErrors.co} 
                     errmsg={userInfoErrors.co}
                     
                     label={profile.country} placeholder={profile.select_yr_country} menulist={countryList} value={country} onchange={selectcountryChange}/>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={6}>
                     <div ref={stateRef}>
                     <Input name="st" 
                     // error={!!userInfoErrors.st} errmsg={userInfoErrors.st} 
                     error={!!userInfoErrors.st} 
                     errmsg={userInfoErrors.st} 
                        
                     maxlength={50}  label={profile.state} placeholder={profile.update_yr_state} value={userInfo.st} onchange={handleCSZ}/>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={6}>
                     <div ref={cityRef}>
                     <Input name="ct" 
                     // error={!!userInfoErrors.ct} errmsg={userInfoErrors.ct}
                     error={!!userInfoErrors.ct} 
                     errmsg={userInfoErrors.ct} 
                      
                     maxlength={50}  label={profile.city} placeholder={profile.update_yr_city} value={userInfo.ct} onchange={handleCSZ}/>
                     </div>
                  </Grid>
                  <Grid item xs={12} md={6} lg={6}>
                     <div ref={zipRef}>
                     <Input name="zc" 
                     // error={!!userInfoErrors.zc} errmsg={userInfoErrors.zc}
                     error={!!userInfoErrors.zc} 
                     errmsg={userInfoErrors.zc} 
                      
                     maxlength={15}  label={profile.zipcode} placeholder={profile.update_yr_zipcode} value={userInfo.zc} onchange={handleCSZ} />
                     </div>
                  </Grid>
               </Grid>

               </Grid>
            </Grid>
         </div>
         <div className="footer">
            <div>
               <AppButton
                  onclick={cancelButton}
                  value="Cancel"
                  color="white"
                  class="borderBtn"
                  noIcon="d-none"
               ></AppButton>
            </div>
            <div>
               <AppButton
                  value="Save"
                  loading={saveLoading}
                  class="wd-btn-add"
                  noIcon="d-none"
                  type="submit"
                  onclick={handleSubmit}
               ></AppButton>
            </div>
         </div>
         </>
         }
      </>
   );
}
export default ProfileModule; 
