import React, { useState, useEffect } from "react";
import { Link, useLocation, useHistory } from "react-router-dom";
import { AppButton, Input, Title, Para } from "../commonComponents/parts";
import Cookies from 'universal-cookie';
import axios from 'axios';
import WelcomeLayout from "./components/layout";
// import Glogin from "./nglogin";
import { error }  from '../contentComponents/alerts_content.json';
import {general, signup} from '../contentComponents/content.json';
import { toast } from 'react-toastify';
import Check from "../../assets/images/check.svg";
import { revealFormError } from "../commonComponents/form_feedback";
import { authErrorMessage } from "./components/auth_error";

function Signup() {

  // One ref per validated field. A blocked submit scrolls the offending field
  // into view and focuses it, so the failure cannot happen off-screen.
  const emailRef = React.useRef(null);

  const [email, setEmail] = useState('');
  const [emailsent, setEmailsent] = useState(false);
  const [sentMessage, setSentMessage] = useState('');
  const [emailerrmsg, setEmailerrmsg] = useState('');
  const [btnloading, setBtnloading] = useState(false);
  const history = useHistory();
  const location = useLocation();

  useEffect(() => {
      setEmail(location.customNameData || '')
  },[location]);

  const submitSignup = (e) => {
      e.preventDefault();
      if(!email){
          setEmailerrmsg(error.msg1);
          revealFormError(error.msg1, emailRef);
          return false;
      }else if(!(/^(([^<>()[\]\\.,;:\s@\]"]+(\.[^<>()[\]\\.,;:\s@\]"]+)*)|(\]".+\]"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(email))) {
      // }else if(!(/^\w+([\].-]?\w+)*@\w+([\].-]?\w+)*(\.\w+[a-zA-Z]{2,})+$/.test(email))) {
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
          axios.post(global.apiurl + '/user_reg_token', data, {
            headers: {'Authorization': global.token}
          }).then(res => {
            setBtnloading(false);
            const msg = res.data.message
            if(res.data.status !== "true"){          
                toast.error(msg)
            }else if(res.data.regurl){
              // No SMTP on this instance, so no email can arrive. The backend
              // hands back the continue link rather than stranding the user on
              // a "check your inbox" screen for mail that was never sent.
              toast.success(msg)
              history.push(res.data.regurl.replace("/register/", "/register"))
            }else{
              // message.success(msg)
              toast.success(msg)
              setSentMessage(msg)
              setEmail("")
              setEmailsent(true)
              // this.setState({loading:false,loadingspin:false});
              // this.props.history.push("/register-message"); 
            }
          }).catch((err) => {
              // Was silent: a failed request cleared the spinner and left the
              // form looking as though nothing had been pressed.
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
                {sentMessage || `${signup.mail_sent_msg1} ${signup.mail_sent_msg2}`}
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
              <Title class="f24x">{signup.title}</Title>
              <Para>
                {/* JSX drops the newline between two expressions, so the two
                    sentences ran together as "...stays free.Already have one?" */}
                {signup.subject1}{" "}{signup.subject2}
                <span>
                  <Link to="/login" className="primaryLink">
                    {" "}
                    {general.login}
                  </Link>
                </span>
              </Para>
            </div>


            <form className="w-100" id="signupform" autoComplete="off" onSubmit={submitSignup} noValidate>
                <div className="m-b20" ref={emailRef}>
                  <Input id="signup-email" name="email" autoComplete="username" label={general.email} span={" *"} spanclassname={"redClr"} value={email} onchange={(e) => {setEmail(e.target.value); setEmailerrmsg("")}} errmsg={emailerrmsg} error={emailerrmsg.length > 0} />
                </div>
            
                <AppButton noIcon="d-none" value={general.signup} color="primary" type="submit" loading={btnloading} disabled={btnloading} />
            </form>

            
            {/* <div className="or">or</div>

            <Glogin type={general.signup} /> */}
            {/*<AppButton
              value="Signup with google"
              color="white"
              class="shadowBtn"
              Icon={
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="17.5"
                  height="17.743"
                  viewBox="0 0 13.5 13.743"
                >
                  <g
                    id="Group_4487"
                    data-name="Group 4487"
                    transform="translate(-984.5 -645)"
                  >
                    <path
                      id="Path_503"
                      data-name="Path 503"
                      d="M197,191.833a10.749,10.749,0,0,0,1.112.91c.1.1,1.011.809,1.112.91a3.7,3.7,0,0,1,1.011-1.618,3.966,3.966,0,0,1,5.36-.4l.2.2,1.921-1.921a3.206,3.206,0,0,0-.607-.506,6.832,6.832,0,0,0-8.292.2,4.793,4.793,0,0,0-1.011,1.011A5.082,5.082,0,0,0,197,191.833Z"
                      transform="translate(788.258 456.897)"
                      fill="#e43e2b"
                      fillRule="evenodd"
                    />
                    <path
                      id="Path_504"
                      data-name="Path 504"
                      d="M197,270.719a4.2,4.2,0,0,0,.708,1.315,7.19,7.19,0,0,0,3.742,2.326,7.264,7.264,0,0,0,5.056-.607,4.489,4.489,0,0,0,1.112-.809l-1.315-1.112c-.1,0-.2-.1-.3-.2l-.1-.1c-.1,0-.1-.1-.2-.1-.1-.1-.1-.2-.3-.2a.525.525,0,0,1-.4.2,4.032,4.032,0,0,1-4.247-.3l-.607-.607a1.487,1.487,0,0,1-.506-.607,3.111,3.111,0,0,1-.4-.91,10.742,10.742,0,0,0-1.112.91C197.91,270.011,197.1,270.719,197,270.719Z"
                      transform="translate(788.258 384.181)"
                      fill="#2ba24c"
                      fillRule="evenodd"
                    />
                    <path
                      id="Path_505"
                      data-name="Path 505"
                      d="M259.326,247.854c.2,0,.2.1.3.2.1,0,.1.1.2.1l.1.1c.1.1.2.2.3.2l1.315,1.112a3.818,3.818,0,0,0,1.011-1.214,5.285,5.285,0,0,0,.708-1.517,8.111,8.111,0,0,0,.4-1.82,6.881,6.881,0,0,0-.2-2.022H257v2.73h3.742c.1.3-.3,1.011-.506,1.214a4.4,4.4,0,0,1-.607.708C259.528,247.753,259.427,247.854,259.326,247.854Z"
                      transform="translate(734.326 407.552)"
                      fill="#3c7ced"
                      fillRule="evenodd"
                    />
                    <path
                      id="Path_506"
                      data-name="Path 506"
                      d="M190.258,231.169c.1,0,.91-.708,1.112-.809a10.742,10.742,0,0,1,1.112-.91,3.124,3.124,0,0,1-.2-1.315,5.123,5.123,0,0,1,.2-1.315c-.1-.1-1.011-.809-1.112-.91a10.749,10.749,0,0,1-1.112-.91,5.976,5.976,0,0,0-.607,1.416,9.818,9.818,0,0,0,0,3.438C189.753,230.157,190.056,231.067,190.258,231.169Z"
                      transform="translate(795 423.731)"
                      fill="#f0b401"
                      fillRule="evenodd"
                    />
                  </g>
                </svg>
              }
            ></AppButton>*/}


              </div>
          </div>
        }
        </div>
      </WelcomeLayout>
    </>
  );
}

export default Signup;
