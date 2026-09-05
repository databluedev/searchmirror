import React, { useState, useEffect } from "react";
import { useHistory } from "react-router-dom";
import { AppButton} from "../commonComponents/parts";
import { error }  from '../contentComponents/alerts_content.json';
import Cookies from 'universal-cookie';
import axios from 'axios';
import { GoogleOAuthProvider } from '@moeindana/google-oauth';
import { GoogleLogin } from '@moeindana/google-oauth';

function Glogin(props) {
  const emailerrmsg = useState('');
  const [btnloading, setBtnloading] = useState(true);

  const history = useHistory();
  const clientId = global.clientId;
  

  useEffect(() => {
   document.getElementById('appbtn').hidden = true;

  }, []);


  const submitres = (res) => {
      const cookies = new Cookies();
      cookies.set('session_token',res.token, { path: '/', maxAge: global.cookiesexpire }); 
      global.token = 'Token '+res.token;  
      cookies.set('session_userid',res.id, { path: '/', maxAge: global.cookiesexpire });
      cookies.set('txt','show', { path: '/', maxAge: global.cookiesexpire }); 
      cookies.set('session_username', res.username, { path: '/', maxAge: global.cookiesexpire }); 
      cookies.set('session_usermail', res.email, { path: '/', maxAge: global.cookiesexpire });   

      if ('type' in res) { 
        if (res.type === "newaccount") { 
          console.log("- FPR Init -", res.email)
          window.fpr("referral",{email: res.email})
          console.log("- FPR Done -")
        } 
      } 

      const sdata = {
         'userid': res.id,
         'username': res.username,
         'email': res.email
      };
      axios.post(global.apiurl + '/new_user_create', sdata, {
        headers: {'Authorization': global.token}
      }).then(response => {
         return response.data;
      }).then(rs => {
         if(rs.status === 'true') {

            const data = {
               'userid': res.id,
               'count': 'GRPCNTONLY'
            };
            axios.post(global.apiurl + '/menu_details', data, {
            headers: {'Authorization': global.token}
            }).then(response => {
               const res = response.data
               if (response.status !== 200) {
                    document.getElementById("againbtnclick").click();
               }else if(res.status === "true") {
                    setBtnloading(false);
                    history.push("/projects");     
               } else {
                    const cookies = new Cookies();  
                    cookies.remove('session_userid', { path: '/' });
                    cookies.remove('session_token', { path: '/' });
                    cookies.remove('txt', { path: '/' });
                    cookies.remove('ckgrp', { path: '/' });
                    cookies.remove('activegrp', { path: '/' });
                    cookies.remove('lastmenuopen', { path: '/' }); 
                    cookies.remove('session_username', { path: '/' }); 
                    cookies.remove('session_usermail', { path: '/' }); 
                    cookies.remove('_ACTGS', { path: '/' }); 
                    cookies.remove('view', { path: '/' }); 
                    localStorage.clear();
                    history.push('/login')    
                    // message.error("user details api data not fetch")
               }
            }).catch((error) => {
               history.push("/login");  
            });
         }
      }).catch((error) => {
         history.push("/login");  
      });
  }

  const gloginsubmit = (req) => {
      if (req.email) {
          setBtnloading(true);
          var email = req.email;
          if (!(/^\w+([\].-]?\w+)*@\w+([\].-]?\w+)*(\.\w{2,3})+$/.test(email))) {
              emailerrmsg(error.msg13);
              setBtnloading(false);
              // this.setState({ gloginloading: false });
              return false;
          } else {
              const cookies = new Cookies();

              cookies.remove('session_userid', { path: '/' });
              cookies.remove('session_token', { path: '/' });
              cookies.remove('txt', { path: '/' });
              
              var campaign = "" //Campaign
              var medium = "" //Medium
              var source = "" //Source
              var referral = "" //Referral
              if(typeof(cookies.get('cmp')) === "undefined" || cookies.get('cmp') === "" || cookies.get('cmp').length === 0) { 
                 campaign = "NA"
              }else{
                 campaign = cookies.get('cmp')
              }
              if(typeof(cookies.get('mdm')) === "undefined" || cookies.get('mdm') === "" || cookies.get('mdm').length === 0) { 
                 medium = "NA"
              }else{
                 medium = cookies.get('mdm')
              }
              if(typeof(cookies.get('src')) === "undefined" || cookies.get('src') === "" || cookies.get('src').length === 0) { 
                 source = "NA"
              }else{
                 source = cookies.get('src')
              }
              if(typeof(cookies.get('ref')) === "undefined" || cookies.get('ref') === "" || cookies.get('ref').length === 0) { 
                 referral = "NA"
              }else{
                 referral = cookies.get('ref')
              }
              const data = {
                    'email': email.toLowerCase(),
                    'name': req.name,
                    'googleId': req.kid,
                    'campaign': campaign,
                    'medium': medium,
                    'source': source,
                    'referral': referral,
              };
              axios.post(global.apiurl + '/api/account/Glogin/', data, {
              headers: {'Authorization': global.token}
              }).then(response => {
                  return response.data;
              }).then(res => {
                  return submitres(res)
              }).catch(err => {
                  history.push("/");
              });
          }
      }
  }

   const onSuccess = (res) => {
      document.getElementById('appbtn').hidden = false;
      document.getElementById('customglogin').hidden = true;
      gloginsubmit(res);
   };

   const onFailure = (res) => {
         gloginfail(res);
   };

   const gloginfail = (res) => {
      if (res.error === "idpiframe_initialization_failed" && res.details === "Cookies are not enabled in current environment.") {
         document.getElementById('appbtn').hidden = true;
         document.getElementById('customglogin').hidden = false;
      }
      setBtnloading(false);
   }

   const gloginopen = () => {
      setBtnloading(true);
   }

   return (
    <div onClick={gloginopen}>
      <AppButton
         value={(props.type || "Login") +" with Google"}
         color="white"
         class="shadowBtn"
         id="appbtn"
         loading={btnloading} 
         disabled={btnloading}
      ></AppButton>
      {clientId ? (
      <GoogleOAuthProvider clientId={clientId}>
         <div id="customglogin">
         <GoogleLogin
            onSuccess={onSuccess}
            onError={onFailure}
            width="330px"
            text ={props.type === "Sign up" ?"signup_with" : "signin_with"}
            size = "large"
            logo_alignment = "center"
         />
         </div>
      </GoogleOAuthProvider>
      ) : null}
    </div>
  );
}

export default Glogin;
