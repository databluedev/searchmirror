import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { AppButton, Input, Title, Para } from "../commonComponents/parts";
import Cookies from 'universal-cookie';
import axios from 'axios';
import WelcomeLayout from "./components/layout";
import { error }  from '../contentComponents/alerts_content.json';
import {general, forgetpwd} from '../contentComponents/content.json';
import { toast } from 'react-toastify';
import Check from "../../assets/images/check.svg";
import { revealFormError } from "../commonComponents/form_feedback";
import { authErrorMessage } from "./components/auth_error";

function ForgotPassword() {

  // One ref per validated field. A blocked submit scrolls the offending field
  // into view and focuses it, so the failure cannot happen off-screen.
  const emailRef = React.useRef(null);

  const [email, setEmail] = useState('');
  const [emailsent, setEmailsent] = useState(false);
  const [emailerrmsg, setEmailerrmsg] = useState('');
  const [btnloading, setBtnloading] = useState(false);
  // const history = useHistory();
  const location = useLocation();

  useEffect(() => {
      setEmail(location.customNameData || '')
  },[location]);

  const submitResetpwd = (e) => {
      e.preventDefault();
      if(!email){
          setEmailerrmsg(error.msg1);
          revealFormError(error.msg1, emailRef);
          return false;
      }else if(!(/^(([^<>()[\]\\.,;:\s@\]"]+(\.[^<>()[\]\\.,;:\s@\]"]+)*)|(\]".+\]"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(email))) {
      // }else if(!(/^\w+([\].-]?\w+)*@\w+([\].-]?\w+)*(\.\w{2,3})+$/.test(email))) {
          setEmailerrmsg(error.msg2);
          revealFormError(error.msg2, emailRef);
          return false;
      }  
      else{
          setBtnloading(true);
          const cookies = new Cookies();

          cookies.remove('session_userid', { path: '/' });
          cookies.remove('session_token', { path: '/' });
          cookies.remove('txt', { path: '/' });

          const data = {
            'email': email.toLowerCase(),
          };
          axios.post(global.apiurl + '/reset/', data, {
            headers: {'Authorization': global.token}
          }).then(res => {
            setBtnloading(false);
            const msg = res.data.message
            if(res.data.status !== "true"){          
                // setEmailerrmsg(msg)
                toast.error(msg)
            }else{
              toast.success(msg)
              setEmail("")
              setEmailsent(true)
              // this.setState({loading:false,loadingspin:false});
              // this.props.history.push("/register-message"); 
            }
          }).catch((err) => {
              // error.response was dereferenced without a guard, so a request
              // that never reached the API threw here instead of clearing the
              // spinner, and the button stayed loading for good.
              const message = authErrorMessage(err);
              setEmailerrmsg(message);
              revealFormError(message, emailRef);
              setBtnloading(false);
          });
      }
  }

  return (
    <>
      <WelcomeLayout
      >
        <div className="h-100vh">
          { emailsent === true ?
            <div className="loginRightBox ">
              <div className="centerAlign">
              <div className="mx-auto">
                <img src={Check} alt="" width="50" />
              </div>
              <div className="text-center align-self-center mb-3">
                <Title>{general.check_yr_email}</Title>
                <Para>
                  {forgetpwd.mail_sent_msg1}
                  {forgetpwd.mail_sent_msg2}{" "}
                </Para>
              </div>
              <Link to="/login" className="w-100">
                <AppButton noIcon="d-none" value={general.back_to_login} color="primary" />
              </Link>
              </div>
            </div>
          :
            <div className="loginRightBox ">
              <div className="centerAlign">
                <div className="text-center align-self-center mb-3">
                  <Title class="f24x">{forgetpwd.title}</Title>
                  <Para>
                    {forgetpwd.subject1}
                  </Para>
                </div>

                <form className="w-100" id="resetpwdform" autoComplete="off" onSubmit={submitResetpwd} noValidate>
                  <div className="m-b20" ref={emailRef}>
                    <Input id="forgot-email" name="email" autoComplete="username" label={general.email} span={" *"} spanclassname={"redClr"} value={email} onchange={(e) => {setEmail(e.target.value); setEmailerrmsg("")}} errmsg={emailerrmsg} error={emailerrmsg.length > 0} />
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
          }
        </div>
      </WelcomeLayout>
    </>
  );
}

export default ForgotPassword;
