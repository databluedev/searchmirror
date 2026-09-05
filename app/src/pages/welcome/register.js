import React, { useState, useEffect } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";
import { AppButton, Input, Title, Para, SelectMenu, PasswordInput,} from "../commonComponents/parts";
import WelcomeLayout from "./components/layout";
import axios from 'axios';
import Cookies from 'universal-cookie';
// import Glogin from "./nglogin"; 
import { Bone } from "../commonComponents/page_skeleton";
import { error }  from '../contentComponents/alerts_content.json';
import {general, registerpg} from '../contentComponents/content.json';
import Close from "../../assets/images/Close.svg";
import { revealFormError } from "../commonComponents/form_feedback";


function Register() {
  const history = useHistory();
  const location = useLocation();
  const [tokenstatus, setTokenstatus] = useState('');
  const [registrationToken, setRegistrationToken] = useState('');
  const [email, setEmail] = useState('');
  const [uname, setUname] = useState('');
  const [designation, setDesignation] = useState('');
  const [pwd, setPwd] = useState('');
  const [cfpwd, setCfpwd] = useState('');
  // One ref per validated field. A blocked submit scrolls the offending field
  // into view and focuses it, so the failure cannot happen off-screen.
  const unameRef = React.useRef(null);
  const designationRef = React.useRef(null);
  const pwdRef = React.useRef(null);
  const cfpwdRef = React.useRef(null);

  const [Unmerrmsg, setUnmerrmsg] = useState('');
  const [dsgnerrmsg, setDsgnerrmsg] = useState('');
  const [pwderrmsg, setPwderrmsg] = useState('');
  const [cfpwderrmsg, setCfpwderrmsg] = useState('');
  const [btnloading, setBtnloading] = useState(false);
  // const menulist = useState(['Founder','Chief Executive Officer','Chief Marketing Officer','Head of Marketing','Marketing Analyst','SEO Analyst','Marketing Consultant','Marketing Manager','Marketing Agency'])
   const menulist = global.designations



  useEffect(() => {

    const params = new URLSearchParams(location.search);
    const prtoken = params.get('userregtoken');
    if (prtoken === null){
      history.push("/signup");  
    }else{
    setRegistrationToken(prtoken);

    // var tokenValid = new FormData();
    // tokenValid.append('userregtoken', prtoken);
    // fetch(global.apiurl+'/user_regtoken_verify', {
    //   method: 'POST',
    //   headers: {'Authorization': global.token},
    //   body: tokenValid
    // }).then(response => {

    const data = {
      'userregtoken': prtoken
    };
    axios.post(global.apiurl + '/user_regtoken_verify', data, {
    headers: {'Authorization': global.token}
    }).then(response => {
        return response.data;
    }).then(res => {
      if(res.status !== "true"){    
        setTokenstatus('invalid')
      }else{
        setTokenstatus('valid')
        setEmail(res.email);
      }
      
    }).catch((error) => {
        setTokenstatus('invalid')
        // history.push("/login");  
    });
    }
  }, [location,history]);

const capitalizeFirstLetter = (x) => { 
    return x[0].substring(0, 1).toUpperCase() + x[0].slice(1); 
}

const selectlstChange = (event) => {
    const { target: { value }, } = event;

    setDsgnerrmsg('');
    setDesignation(value);
};

const SubmitRegister = (e) => {
    e.preventDefault();
    // this.setState({loading:true})
    let usernametrim = uname.trim()
  if(!usernametrim){
      setUnmerrmsg(error.msg8);
      revealFormError(error.msg8, unameRef);
      return false
  }else if(usernametrim.length < 3){
      setUnmerrmsg(error.msg11)
      revealFormError(error.msg11, unameRef);
      return false
  }else if(!(/^[a-zA-Z ]+$/.test(usernametrim))){
      setUnmerrmsg(error.msg12);
      revealFormError(error.msg12, unameRef);
      return false
  }else if(!pwd){
      setPwderrmsg(error.msg3)
      revealFormError(error.msg3, pwdRef);
      return false
  }else if(pwd.length < 8){
      setPwderrmsg(error.msg6)
      revealFormError(error.msg6, pwdRef);
      return false
  }else if(!cfpwd){
    setCfpwderrmsg(error.msg4);
    revealFormError(error.msg4, cfpwdRef);
    return false
  }else if(pwd !== cfpwd){
    setCfpwderrmsg(error.msg10);
    revealFormError(error.msg10, cfpwdRef);
    return false
  }else{
    setBtnloading(true);
      
    var campaign = "" //Campaign
    var medium = "" //Medium
    var source = "" //Source
    var referral = "" //Referral
    const cookies = new Cookies();
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
       'username': usernametrim,
       'designation': designation,
       'email': email.toLowerCase(),
       'password': pwd,
       'password2': cfpwd,
       'campaign': campaign,
       'medium': medium,
       'source': source,
       'referral': referral,
       'userregtoken': registrationToken,
    };
    axios.post(global.apiurl + '/api/account/register/', data, {
      headers: {'Authorization': global.token}
    }).then(response => {
        return response.data;
    }).then(resp => {
        if(resp.status==='true') {
                
            var usersetid = resp.id;
            var smusername = resp.username;
            var smuseremail = resp.email;
            var smusertoken = resp.token;
            global.token = 'Token '+smusertoken;

            if (typeof window.fpr === "function") {
              window.fpr("referral", { email: resp.email });
            }

            //User Settings create
            // formdata.append('userid', usersetid);
            // formdata.append('username', smusername);
            // formdata.append('email', smuseremail);
            // fetch(global.apiurl+'/new_user_create', {
            //       method: 'POST',
            //       headers: {'Authorization':global.token},
            //       body: formdata,
            //   }).then(response => {
            //       return response.json();
            //   }).then(res => {

            const data = {
              'userid': usersetid,
              'username': smusername,
              'email': smuseremail,
            };
            axios.post(global.apiurl + '/new_user_create', data, {
              headers: {'Authorization': global.token}
            }).then(response => {
                return response.data;
            }).then(res => {
                if(res.status==='true') {
                    // this.setState({loading:false,loadingspin:false,loginprocess: false,gloginloading:false});                                                                 
                    cookies.set('session_token',smusertoken, { path: '/' }); 
                    cookies.set('session_userid',usersetid, { path: '/' });
                    cookies.set('txt','show', { path: '/' });
                    cookies.set('session_usermail', smuseremail, { path: '/' });
                    cookies.set('session_username', smusername, { path: '/' });
                    
                    //menu_detailscreate
                    // var formdatared = new FormData();
                    // formdatared.append('userid', usersetid);      
                    // formdatared.append('count', 'GRPCNTONLY');  
                    // fetch(global.apiurl + '/menu_details', {   
                    //     method: 'POST',
                    //     headers: { 'Authorization': global.token },
                    //     body: formdatared
                    // }).then(response => {
                    //     return response.json();
                    // }).then(res => {

                    const data = {
                      'userid': usersetid,
                      'count': 'GRPCNTONLY',
                    };
                    axios.post(global.apiurl + '/menu_details', data, {
                      headers: {'Authorization': global.token}
                    }).then(response => {
                        return response.data;
                    }).then(res => {
                        setBtnloading(false);
                        if(res.status === "true") {
                            // this.setState({loading:false,loadingspin:false,loginprocess: false,gloginloading:false});
                            // this.props.history.push("/app/dashboard");   
                            history.push("/projects");   
                        }
                    }).catch( err => {
                        setBtnloading(false);
                        history.push("/");   
                    });

                    // //Referral Process
                    // if(cookies.get('refid')){
                    //   var refformdata = new FormData();
                    //   refformdata.append('ref_id', cookies.get('refid'));
                    //   refformdata.append('refregid', usersetid);
                    //   fetch(global.apiurl + '/refregadd', { 
                    //     method: 'POST',
                    //     headers: { 'Authorization': global.token },
                    //     body: refformdata
                    //   }).then(response => {
                    //     return response.json();
                    //   }).then(res => { 
                    //     if (res.status !== "true") {
                    //       console.log(res.message);
                    //     }else{
                    //       console.log(res.message);
                    //       cookies.remove('refid', { path: '/' });
                    //     }
                    //   });
                    // }
                }      
            });
          } else { 
                // this.setState({loading:false})
                setBtnloading(false);
                var msgobj = resp.message
                for (var key in msgobj) {
                  setCfpwderrmsg(capitalizeFirstLetter(msgobj[key]))  
                  // message.error(this.capitalizeFirstLetter(msgobj[key]))  
                }
            }    
          }).catch(err => {
              setBtnloading(false);
              const message = err.response && err.response.data && err.response.data.message
                ? err.response.data.message
                : "Registration failed. Please try again.";
              setCfpwderrmsg(typeof message === "string" ? message : "Registration failed. Please try again.");
              revealFormError(message, cfpwdRef);
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
                  <Title>{registerpg.mail_expire_msg1}</Title>
                  <Para>
                    {registerpg.mail_expire_msg2}{" "}
                  </Para>
                </div>
                <Link to="/signup" className="w-100">
                  <AppButton noIcon="d-none" value={general.back_to_singup} color="primary" />
                </Link>
                </div>
              </div>
            </div>
        : tokenstatus === "valid" ?
            <section id="welcomeScrollbar">
              <div className="loginRightBox ">
                <div className="centerAlign">
                  <div className="text-center align-self-center mb-3">
                    <Title class="f24x">{registerpg.title}</Title>
                    <Para>
                      {registerpg.subject1}
                      {registerpg.subject2}
                      <span>
                        <Link to="/login" className="primaryLink">
                          {" "}
                          {general.login}
                        </Link>
                      </span>
                    </Para>
                  </div>

                  <form className="w-100" id="registerform" autoComplete="off" onSubmit={SubmitRegister} noValidate>
                    <div className=" m-b20" ref={unameRef}>
                      <Input id="register-name" name="name" autoComplete="name" label={registerpg.yr_good_name} span={" *"} spanclassname={"redClr"} value={uname} onchange={(e) => {setUname(e.target.value); setUnmerrmsg("")}} errmsg={Unmerrmsg} error={Unmerrmsg.length > 0} />
                    </div>
                    <div className=" m-b20" ref={designationRef}>
                      <SelectMenu label={general.designation} placeholder={general.select_yr_designation} value={designation} menulist={menulist} onchange={selectlstChange} errmsg={dsgnerrmsg} error={dsgnerrmsg.length > 0} />
                    </div>
                    <div className=" m-b20" ref={pwdRef}>
                      <PasswordInput id="register-password" name="new-password" autoComplete="new-password" label={general.password} span={" *"} spanclassname={"redClr"} value={pwd} onchange={(e) =>{setPwd(e.target.value); setPwderrmsg("")}} errmsg={pwderrmsg} error={pwderrmsg.length > 0} />
                    </div>
                    <div className=" m-b20" ref={cfpwdRef}>
                      <PasswordInput id="register-confirm-password" name="confirm-password" autoComplete="new-password" label={general.confirm_password} span={" *"} spanclassname={"redClr"} value={cfpwd} onchange={(e) =>{setCfpwd(e.target.value); setCfpwderrmsg("")}} errmsg={cfpwderrmsg} error={cfpwderrmsg.length > 0} />
                    </div>
                    <AppButton noIcon="d-none" value={general.signup} color="primary" type="submit" loading={btnloading} disabled={btnloading} class="" />
                  </form>

                  {/*<div className="or">or</div> */} 
                  {/*<Glogin type={general.signup} />*/} 
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
            </section>
        :
            /* The invitation token is being checked. What replaces this is the
               registration form above -- title, one line of prose and four
               fields over a button -- so the bones are that, inside the same
               .loginRightBox / .centerAlign the form uses, which is what keeps
               the widths from jumping when it lands. The four bars this
               replaced were a fixed 350px block painted with a literal grey
               hex that _tokens.scss does not define. */
            <section id="welcomeScrollbar" role="status" aria-live="polite" aria-busy="true">
              <span className="visually-hidden">Checking your invitation link</span>
              <div className="loginRightBox" aria-hidden="true">
                <div className="centerAlign">
                  <div className="text-center align-self-center mb-3 w-100 d-flex flex-column align-items-center">
                    <Bone className="m-b10" width="220px" height="28px" />
                    <Bone width="280px" height="14px" />
                  </div>
                  <div className="w-100">
                    <Bone className="m-b20" height="56px" />
                    <Bone className="m-b20" height="56px" />
                    <Bone className="m-b20" height="56px" />
                    <Bone className="m-b20" height="56px" />
                    <Bone height="44px" />
                  </div>
                </div>
              </div>
            </section>
        }
      </WelcomeLayout>
    </>
  );
}

export default Register;
