import React, { useState,useEffect } from "react";
import { useHistory } from "react-router-dom";
import "../style.scss";

import {
   AppButton,
   TextLg,
   PasswordInput,
   Para, ParaLg
} from "../../commonComponents/parts";
import { Grid } from "@mui/material";
import {general,account} from '../../contentComponents/content.json';
import { error }  from '../../contentComponents/alerts_content.json';
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';
import { revealFormError } from "../../commonComponents/form_feedback";



function AccountsModule({ children, ...props }) { 
   // One ref per validated field. A blocked submit scrolls the offending field
   // into view and focuses it, so the failure cannot happen off-screen.
   const oldPwdRef = React.useRef(null);
   const newPwdRef = React.useRef(null);
   const cfmPwdRef = React.useRef(null);

   const [oldPwd, setOldPwd] = useState('');
   const [oldPwderrmsg, setOldPwderrmsg] = useState('');
   const [newPwd, setNewPwd] = useState('');
   const [newPwderrmsg, setNewPwderrmsg] = useState('');
   const [cfmPwd, setCfmpwd] = useState('');
   const [cfmPwderrmsg, setCfmpwderrmsg] = useState('');
   const [chngBtnloading, setChngBtnloading] = useState(false)
   const [isFormSubmit, setIsFormSubmit] = useState(false);
   const [oldPwdVsble, setOldPwdVsble] = useState(true);

   const history = useHistory();

   useEffect (() => {
     
      accoutData();
   },[props.projectList]);

   const accoutData = () => {
      // account setting get data
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')

      if(userid){
         const data = {
            'userid': userid,
         };
         axios.post(global.apiurl + '/account_settings', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            // console.log('.....accoutData...res',res);
            if(res.At === "enable"){
               setOldPwdVsble(true);
            }else{
               setOldPwdVsble(false);
               setOldPwd('-')
            }
         });
      }
   }

   const spacekey = (event) => {
		if (event.keyCode === 32) {
			toast.error("Space key not allowed");
			event.preventDefault();
			return false;
		}
		return true;
	}

   const submitChangepwd = (e) => {
      e.preventDefault();
      setIsFormSubmit(true)
      if(oldPwdVsble === true){
         if(!oldPwd){
            setOldPwderrmsg(error.msg3);
            revealFormError(error.msg15, oldPwdRef);
            return false;
         }
      }
      if(!newPwd){
          setNewPwderrmsg(error.msg3);
          revealFormError(error.msg16, newPwdRef);
          return false;
      }else if(newPwd.length < 8 || !(/^(?=.*[0-9])(?=.*[!@#$%^&*])[a-zA-Z0-9!@#$%^&*]{8,16}$/.test(newPwd))){
         setNewPwderrmsg(error.msg18)
          revealFormError(error.msg18, newPwdRef);
          return false
      }else if(!cfmPwd){
          setCfmpwderrmsg(error.msg4);
          revealFormError(error.msg17, cfmPwdRef);
          return false;
      }else if(newPwd !== cfmPwd){
          setCfmpwderrmsg(error.msg7);
          revealFormError(error.msg7, cfmPwdRef);
          return false;
      }else{
         if(oldPwdVsble === true){
            setOldPwderrmsg('');
         }
         setNewPwderrmsg('');
         setCfmpwderrmsg('');
         setChngBtnloading(true);
         const cookies = new Cookies();
         const usertoken = cookies.get('session_token');
         const userid = cookies.get('session_userid');
         if(userid){
            const data = {
               'userid': userid,
               'old_password': oldPwd,
               'new_password': newPwd,
               'confirm_new_password': cfmPwd,
            };
            axios.put(global.apiurl + '/api/account/changepassword/', data, {
               headers: {'Authorization': 'Token '+ usertoken }
            }).then(response => {
               return response.data;
            }).then(res => {
               // console.log('........submitres',res);
               const msg = res.message;
               setIsFormSubmit(false);
               setChngBtnloading(false);
               setOldPwd('');
               setNewPwd('');
               setCfmpwd('');
               if (res.status !== "true") {
                  toast.error(msg)
               }else{
                  toast.success(msg)
                  cookies.remove('session_userid', { path: '/' }); 
                  cookies.remove('session_token', { path: '/' });
                  cookies.remove('txt', { path: '/' });
                  cookies.remove('ckgrp', { path: '/' });
                  cookies.remove('activegrp', { path: '/' });
                  cookies.remove('lastmenuopen', { path: '/' }); 
                  cookies.remove('session_username', { path: '/' }); 
                  cookies.remove('session_usermail', { path: '/' });  
                  localStorage.clear();
                  history.push('/login'); 
               }
            });
         }
      }
   }
   return (
      <>
         <div className="m-b70 m-t25">
            <Grid container className="">
               <Grid item xs={12} md={6} lg={4}>
               <form className="w-100" id="changepwdform" autoComplete="off" onSubmit={submitChangepwd} noValidate>
                  <Grid container spacing={3} className="">
                     <Grid item xs={12} md={12} lg={12}>
                        {/* <Title class="mb-0 lineHAuto">Change Password</Title> */}
                        <div>
                        <TextLg class="lineHAuto m-b15 changePassword">Change Password</TextLg>
                        </div>
                     </Grid>
                     {oldPwdVsble?
                     <Grid item xs={12} md={12} lg={12}>
                        <div ref={oldPwdRef}>
                           <PasswordInput label={general.old_password} span={" *"} value={oldPwd} 
                           onchange={(e) =>{setOldPwd(e.target.value); setOldPwderrmsg("")}} 
                           error={isFormSubmit ? oldPwd === "" ? true : oldPwderrmsg.length > 0 : false} 
                           errmsg={isFormSubmit ? oldPwd === ""? error.msg15 : oldPwderrmsg : ''} 
                           maxlength={30}
                           onkeydown={spacekey}/>
                        </div>
                     </Grid>
                     :
                     <>
                     </>
                     }
                     <Grid item xs={12} md={12} lg={12}>
                        <div ref={newPwdRef}>
                           <PasswordInput label={general.new_password} span={" *"} value={newPwd} 
                           onchange={(e) =>{setNewPwd(e.target.value); setNewPwderrmsg("")}} 
                           error={isFormSubmit ? newPwd === "" ? true : newPwderrmsg.length > 0 : false} 
                           errmsg={isFormSubmit ? newPwd === ""? error.msg16 : newPwderrmsg : ''} 
                           maxlength={30}
                           onkeydown={spacekey}/>
                        </div>
                     </Grid>
                     <Grid item xs={12} md={12} lg={12}>
                        <div ref={cfmPwdRef}>
                           <PasswordInput label={general.reEnter_password} span={" *"} value={cfmPwd} 
                           onchange={(e) => {setCfmpwd(e.target.value); setCfmpwderrmsg("")}} 
                           error={isFormSubmit ? cfmPwd === "" ? true : cfmPwderrmsg.length > 0 : false} 
                           errmsg={isFormSubmit ? cfmPwd === ""? error.msg17 : cfmPwderrmsg : ''}
                           maxlength={30}
                           onkeydown={spacekey}/>
                        </div>
                     </Grid>
                     <Grid item xs={12} md={12} lg={12}>
                        <div>
                           <AppButton
                           loading={chngBtnloading}
                           value="Change"
                           noIcon="d-none"
                           class="changePwdBtn wd-btn-add" 
                           onclick={submitChangepwd}
                           type="submit"
                           ></AppButton>
                        </div>
                     </Grid>
                  </Grid>
                  </form>
               </Grid>
               <Grid item xs={12} md={6} lg={5} className="demoDelSec">
                  <Grid container spacing={3} className="">
                     <Grid item xs={12} md={12} lg={12}>
                        <div>
                        <section className="projectCard">
                           <div className="d-flex align-items-center justify-content-between m-b15">
                              <ParaLg class="fB m-b0 lh26x">{account.delete_yr_account}</ParaLg>
                           </div>
                           <div className="text-justify max-h-[100px] min-h-[60px] overflow-y-auto">
                              <Para class = 'p-r5'>
                              When you delete your account your entire project details and ranking data will be permanently removed. Please, ensure that you understand the impact of deleting your account.
                              </Para>
                           </div>
                           {/* Account deletion is done by asking the operator:
                               there is no self-service endpoint. On a
                               self-hosted install with no contact address
                               configured there is nobody to send the reader to,
                               and a button whose href is empty reloads the page
                               -- so it is replaced by the instruction it was
                               standing in for. */}
                           <div>
                              {global.contactUs ?
                                 <a rel="noreferrer" href={global.contactUs} target="_blank">
                                    <AppButton
                                       class="deleteAccBtn"
                                       value={account.delete_account}
                                       noIcon="d-none"
                                    ></AppButton>
                                 </a>
                                 :
                                 <Para class="secondaryClr m-b0">Contact the administrator of this instance to have your account removed.</Para>
                              }
                           </div>
                        </section>
                        </div>
                     </Grid>
                  </Grid>
               </Grid>
            </Grid>
         </div>
      </>
   );
}
export default AccountsModule; 
