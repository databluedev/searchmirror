import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppButton, Title, Para, PasswordInput } from "../commonComponents/parts";
import Cookies from 'universal-cookie';
import axios from 'axios';
import WelcomeLayout from "./components/layout";
import { Bone } from "../commonComponents/page_skeleton";
import { error }  from '../contentComponents/alerts_content.json';
import {general, resetpwd} from '../contentComponents/content.json';
import { toast } from 'react-toastify';
import { revealFormError } from "../commonComponents/form_feedback";
import { authErrorMessage } from "./components/auth_error";
import Check from "../../assets/images/check.svg";
import Close from "../../assets/images/Close.svg";

function ResetPassword() {

  const [tokenstatus, setTokenstatus] = useState('');
  const [pwd, setPwd] = useState('');
  // One ref per validated field. A blocked submit scrolls the offending field
  // into view and focuses it, so the failure cannot happen off-screen.
  const pwdRef = React.useRef(null);
  const cfmpwdRef = React.useRef(null);

  const [pwderrmsg, setPwderrmsg] = useState('');
  const [cfmpwd, setCfmpwd] = useState('');
  const [cfmpwderrmsg, setCfmpwderrmsg] = useState('');
  const [btnloading, setBtnloading] = useState(false);
  // const history = useHistory();
  const location = useLocation();

  useEffect(() => {
      const cookies = new Cookies();
      const params = new URLSearchParams(location.search); 
      const prtoken = params.get('token');

      // var tokenValid = new FormData();
      // tokenValid.append('token', prtoken);
      // fetch(global.apiurl+'/reset/validate_token/', {
      //   method: 'POST',
      //   headers: {'Authorization': global.token},
      //   body: tokenValid
      // }).then(response => {
      //   return response.json();
      // }).then(res => {

      const data = {
        'token': prtoken
      };
      axios.post(global.apiurl + '/reset/validate_token/', data, {
      headers: {'Authorization': global.token}
      }).then(response => {
          return response.data;
      }).then(res => {
        if(res.status !== "true"){          
          setTokenstatus('invalid')
        }else{
          setTokenstatus('valid')
          cookies.set('Password_reset_token',prtoken,{ maxAge: global.cookiesexpire} );         
          // setTimeout(() => {
          //   this.props.history.push("/passwordchange"); 
          // }, 4000);
        }
      }).catch((error) => {
          setTokenstatus('invalid')
          // history.push("/login")
      });
  },[location]);

  const submitResetpwd = (e) => {
      e.preventDefault();
      if(!pwd){
          setPwderrmsg(error.msg3);
          revealFormError(error.msg3, pwdRef);
          return false;
      }else if(pwd.length < 8){
          setPwderrmsg(error.msg6)
          revealFormError(error.msg6, pwdRef);
          return false
      }else if(!cfmpwd){
          setCfmpwderrmsg(error.msg4);
          revealFormError(error.msg4, cfmpwdRef);
          return false;
      }else if(pwd !== cfmpwd){
          setCfmpwderrmsg(error.msg7);
          revealFormError(error.msg7, cfmpwdRef);
          return false;
      }else{
          const cookies = new Cookies();
          const Password_reset_token = cookies.get('Password_reset_token');
          setBtnloading(true)
          
          // var passchange = new FormData();
          // passchange.append('token', Password_reset_token);
          // passchange.append('password', this.state.rspasswordtwo); 
          // //password change api
          // fetch(global.apiurl+'/reset/confirm/', {
          //     method: 'POST',
          //     headers: {'Authorization': global.token},
          //     body: passchange
          // }).then(response => {
          //     return response.json();
          // }).then(res => {

          const data = {
            'token': Password_reset_token,
            'password': cfmpwd
          };
          axios.post(global.apiurl + '/reset/confirm/', data, {
              headers: {'Authorization': global.token}
          }).then(response => {
              return response.data;
          }).then(res => {
              setBtnloading(false)
              if(res.status !== "true"){          
                  setCfmpwderrmsg(error.general_msg1);
              }else{
                  setTokenstatus('success')
                  toast.success("Password reset success")
                  // this.props.history.push("/reseetmessage");          
              }
          }).catch((err) => {
              // Was silent: a rejected confirm cleared the spinner and left the
              // form unchanged, which reads as "the button does nothing".
              const message = authErrorMessage(err);
              setCfmpwderrmsg(message);
              revealFormError(message, cfmpwdRef);
              setBtnloading(false)
          });
      }
  }

  return (
    <>
      <WelcomeLayout
      >
        { tokenstatus === "invalid" ? 
            <div className="h-100vh">
              <div className="loginRightBox ">
                <div className="centerAlign">
                <div className="mx-auto">
                  <img src={Close} alt="" width="50" />
                </div>
                <div className="text-center align-self-center mb-3">
                  <Title>{general.sorry}</Title>
                  <Para>
                    {resetpwd.url_expire_msg1}{" "}
                    {resetpwd.url_expire_msg2}{" "}
                  </Para>
                </div>
                <Link to="/login/reset" className="w-100">
                  <AppButton noIcon="d-none" value={resetpwd.btn_restagn} color="primary" />
                </Link>
                </div>
              </div>
            </div>
        : tokenstatus === "valid" ?
            <div className="h-100vh">
              <div className="loginRightBox ">
                <div className="centerAlign">
                  <div className="text-center align-self-center mb-3">
                    <Title class="f24x">{resetpwd.title}</Title>
                    <Para>
                      {resetpwd.subject1}
                    </Para>
                  </div>

                  <form className="w-100" id="resetpwdform" autoComplete="off" onSubmit={submitResetpwd} noValidate>
                    <div className="m-b20" ref={pwdRef}>
                      <PasswordInput id="reset-password" name="new-password" autoComplete="new-password" label={general.new_password} span={" *"} spanclassname={"redClr"} value={pwd} onchange={(e) =>{setPwd(e.target.value); setPwderrmsg("")}} errmsg={pwderrmsg} error={pwderrmsg.length > 0} />
                    </div>
                    <div className="m-b20" ref={cfmpwdRef}>
                      <PasswordInput id="reset-confirm-password" name="confirm-password" autoComplete="new-password" label={general.confirm_password} span={" *"} spanclassname={"redClr"} value={cfmpwd} onchange={(e) => {setCfmpwd(e.target.value); setCfmpwderrmsg("")}} errmsg={cfmpwderrmsg} error={cfmpwderrmsg.length > 0} />
                    </div>
                    <AppButton noIcon="d-none" value={general.resetpwd} color="primary" type="submit" loading={btnloading} disabled={btnloading} />
                  </form>

                  <div className="d-flex w-100 justify-content-end">
                    <Link to="/login" className="lightTxtClr">
                      {general.back_to_login}
                    </Link>
                  </div>
                </div>
              </div>
            </div>
        : tokenstatus === "success" ?
            <div className="h-100vh">
              <div className="loginRightBox ">
                <div className="centerAlign">
                <div className="mx-auto">
                  <img src={Check} alt="" width="50" />
                </div>
                <div className="text-center align-self-center mb-3">
                  <Title>{resetpwd.mail_sent_title}</Title>
                  <Para>
                    {resetpwd.mail_sent_msg1}{" "}
                  </Para>
                </div>
                <Link to="/login" className="w-100">
                  <AppButton noIcon="d-none" value={general.back_to_login} color="primary" />
                </Link>
                </div>
              </div>
            </div>
        :
            /* The reset token is being checked. Two password fields and a
               button replace this, in the same containers, so the bones are
               that. See register.js for the block this shape corrects. */
            <div className="h-100vh" role="status" aria-live="polite" aria-busy="true">
              <span className="visually-hidden">Checking your reset link</span>
              <div className="loginRightBox" aria-hidden="true">
                <div className="centerAlign">
                  <div className="text-center align-self-center mb-3 w-100 d-flex flex-column align-items-center">
                    <Bone className="m-b10" width="220px" height="28px" />
                    <Bone width="280px" height="14px" />
                  </div>
                  <div className="w-100">
                    <Bone className="m-b20" height="56px" />
                    <Bone className="m-b20" height="56px" />
                    <Bone height="44px" />
                  </div>
                </div>
              </div>
            </div>
        }
      </WelcomeLayout>
    </>
  );
}

export default ResetPassword;
