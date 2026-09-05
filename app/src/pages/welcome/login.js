import React, { useState, useEffect } from "react";
import { Link, useHistory } from "react-router-dom";
import { AppButton, Input, Title, Para, PasswordInput } from "../commonComponents/parts";
import { error }  from '../contentComponents/alerts_content.json';
import {general, login} from '../contentComponents/content.json';
import WelcomeLayout from "./components/layout";
// import Glogin from "./nglogin";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { cookiesremove } from "../common_fun";
import { revealFormError } from "../commonComponents/form_feedback";
import { authErrorMessage } from "./components/auth_error";
function Login() {
  // One ref per validated field. A blocked submit scrolls the offending field
  // into view and focuses it, so the failure cannot happen off-screen.
  const emailRef = React.useRef(null);
  const pwdRef = React.useRef(null);

  const [email, setEmail] = useState('');
  const [pwd, setPwd] = useState('');
  const [emailerrmsg, setEmailerrmsg] = useState('');
  const [pwderrmsg, setPwderrmsg] = useState('');
  const [btnloading, setBtnloading] = useState(false);

  const history = useHistory();

  useEffect(() => {
    const cookies = new Cookies();
    const usertoken = cookies.get('session_token')
    const userid = cookies.get('session_userid')
    if(usertoken && userid){
        history.push("/projects");        
    }else{
        cookiesremove();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const SubmitSignin = (e) => {
      e.preventDefault();

      if(!email){
          setEmailerrmsg(error.msg1)
          revealFormError(error.msg1, emailRef);
          return false;
      }else if(!(/^(([^<>()[\]\\.,;:\s@\]"]+(\.[^<>()[\]\\.,;:\s@\]"]+)*)|(\]".+\]"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(email))) {
      // }else if(!(/^\w+([\].-]?\w+)*@\w+([\].-]?\w+)*(\.\w{2,})+$/.test(email))) {
          setEmailerrmsg(error.msg2);
          revealFormError(error.msg2, emailRef);
          return false;
      }else if(!pwd){
          setPwderrmsg(error.msg3);
          revealFormError(error.msg3, pwdRef);
          return false;
      }else if(pwd.length < 6 ){
          setPwderrmsg(error.msg5);
          revealFormError(error.msg5, pwdRef);
          return false;
      }else{
          setBtnloading(true);
          const cookies = new Cookies();

          cookies.remove('session_userid', { path: '/' });
          cookies.remove('session_token', { path: '/' });
          cookies.remove('txt', { path: '/' });

          const data = {
            'username': email.toLowerCase(),
            'password': pwd
          };

          axios.post(global.apiurl + '/api/account/login/', data)
          .then(res => {
            // console.log(res.data.message);
            if(res.data.status === "true"){
                return submitres(res.data)
            }else{
              setPwderrmsg(res.data.message);
              setBtnloading(false);
            }
          }).catch((error) => {
            // Every failure ends here with a visible reason. The API answers
            // 404 both for a wrong password and for an address with no account,
            // and the two are told apart only by the sentence it returns -- so
            // show that sentence rather than branching on it. "New here? Sign
            // up" is already on this card for the second case.
            const message = authErrorMessage(error);
            setPwderrmsg(message);
            revealFormError(message, pwdRef);
            setBtnloading(false);
          });
      }
  }

  const submitres = (res) => {
      const cookies = new Cookies();
      cookies.set('session_token',res.token, { path: '/', maxAge: global.cookiesexpire }); 
      global.token = 'Token '+res.token;  
      cookies.set('session_userid',res.id, { path: '/', maxAge: global.cookiesexpire });
      cookies.set('txt','show', { path: '/', maxAge: global.cookiesexpire }); 
      cookies.set('session_username', res.username, { path: '/', maxAge: global.cookiesexpire }); 
      cookies.set('session_usermail', res.email, { path: '/', maxAge: global.cookiesexpire });   
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
              // if(res.sidelist > 0 || res.sb_s === "cancelled" || res.sb_s === "expire" || res.sb_s === "dead"){
              //     history.push("/dashboard");   
              //     // this.props.history.push("/app/dashboard");   
              // } else if (res.skipstatus === "on") {
              //     history.push("/demo");  
              //     // this.props.history.push("/app/demo");  
              // }else{
              //     history.push("/dashboard");   
              //     // this.props.history.push("/wizard");
              // }
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

  // const clickcheck = () => {
  //   // console.log("tyest checking")
  // }

  return (
    <>
      <WelcomeLayout
      >
        <section id="welcomeScrollbar">
          <div className="loginRightBox">
            <div className="centerAlign">
              <div className="text-center align-self-center mb-3">
                <Title class="f24x">{login.title}</Title>
                <Para>
                  {login.subject1} <br />
                                    {login.subject2}{" "}
                  <span>
                    <Link to="/signup" className="primaryLink">
                      {" "}
                      {general.signup}
                    </Link>
                  </span>
                </Para>
              </div>
              <form className="w-100" id="loginform" autoComplete="off" onSubmit={SubmitSignin} noValidate>
                <div className="m-b20" ref={emailRef}>
                  <Input id="login-email" name="email" autoComplete="username" label={general.email} span={" *"} spanclassname={"redClr"} value={email} onchange={(e) => {setEmail(e.target.value); setEmailerrmsg("")}} errmsg={emailerrmsg} error={emailerrmsg.length > 0} />
                </div>
                <div className="m-b20" ref={pwdRef}>
                  <PasswordInput id="login-password" name="password" autoComplete="current-password" label={general.password} span={" *"} spanclassname={"redClr"} value={pwd} onchange={(e) =>{setPwd(e.target.value); setPwderrmsg("")}} errmsg={pwderrmsg} error={pwderrmsg.length > 0} />
                </div>
                <AppButton noIcon="d-none" id="againbtnclick" value={general.login} color="primary" type="submit" loading={btnloading} disabled={btnloading} class="m-b20" />

                <div className="m-b30">
                  {" "}
                  <Link to="/login/reset" className="lightTxtClr">
                    {general.forgt_yr_pwd}
                  </Link>{" "}
                </div>
                {/*<div className="or">or</div> */} 
              </form>

              {/*<Glogin type={general.signin} />*/}
              
            </div>
          </div>
        </section>
      </WelcomeLayout>
    </>
  );
}

export default Login;
