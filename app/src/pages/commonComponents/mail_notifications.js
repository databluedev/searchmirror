import React, { useEffect, useState , } from "react";
import { useHistory } from 'react-router-dom';
import { Para, ParaLg, Tsk } from "../commonComponents/parts";
import { Grid, Switch, Box } from "@mui/material";
import { styled } from "@mui/material/styles";
import { toast } from 'react-toastify';
import Cookies from 'universal-cookie';
import axios from 'axios';

const AntSwitch = styled(Switch)(({ theme }) => ({
  width: 28,
  height: 16,
  padding: 0,
  display: "flex",
  "&:active": {
    "& .MuiSwitch-thumb": {
      width: 15,
    },
    "& .MuiSwitch-switchBase.Mui-checked": {
      transform: "translateX(9px)",
    },
  },
  "& .MuiSwitch-switchBase": {
    padding: 2,
    "&.Mui-checked": {
      transform: "translateX(12px)",
      color: "var(--surface)",
      "& + .MuiSwitch-track": {
        opacity: 1,
        backgroundColor: theme.palette.mode === "dark" ? "#177ddc" : "#1890ff",
      },
    },
  },
  "& .MuiSwitch-thumb": {
    boxShadow: "0 2px 4px 0 rgb(0 35 11 / 20%)",
    width: 16,
    height: 16,
    borderRadius: 50,
    transition: theme.transitions.create(["width"], {
      duration: 200,
    }),
  },
  "& .MuiSwitch-track": {
    borderRadius: 16 / 2,
    opacity: 1,
    backgroundColor:
      theme.palette.mode === "dark"
        ? "rgba(255,255,255,.35)"
        : "rgba(0,0,0,.25)",
    boxSizing: "border-box",
  },
}));

const MailToggle = ({title, newtag, mnloading, name, automtnOpt, mailOptSwitchfun, content}) => {

   return(
      <Grid item xs={12} md={6} lg={6} xl={6}>
         <section className="projectCard">
            <div className="d-flex align-items-center justify-content-between m-b15">
               <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                  {title}
                  { newtag ? <span className="complable m-l10">New</span> : null }
               </ParaLg>
               { mnloading ?
                  <Tsk width={46} height={24} className="" />
               :
                  <AntSwitch
                     checked={automtnOpt[name]}
                     onChange={(e) => mailOptSwitchfun(name, e.target.checked) }
                     inputProps={{ "aria-label": "ant design" }}
                  />
               }
            </div>
            <Box className="text-justify" sx={{ maxHeight: "100px", minHeight: "100px", overflowY: "auto" }} >
               <Para class = 'p-r5'>
                 {content}
               </Para>
            </Box>
         </section>
      </Grid>
   )
}

//
function MailNotifications(props) {
   const history = useHistory();
   const [automtnOpt, setAutomtnOpt] = useState({});
   const [mnloading, setMNloading] = useState(true);
   
   // const grpid = cookies.get('activegrp')
   const grpid = props.groupId;

   useEffect(() => {
      allnotificationsdata();
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [props.groupId]);

   const allnotificationsdata = () => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')

      if(userid && grpid) {
         var data = {
           'userid': userid,
           'grpid': grpid,
         };
         axios.post(global.apiurl + '/mailoptswupdate', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if(res.status === "true") {
               setAutomtnOpt(res.OptSw);
               setMNloading(false);
            } else {
               toast.error(res.message)
               history.push("/")
            }           
         }).catch((error) => {
            // history.push("/")
         });
      }
   }

   const mailOptSwitchfun = (name,checked) => {
      setAutomtnOpt({...automtnOpt, [name]:checked})
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      
      // const cookies = new Cookies();
      // var userid = this.props.u_id ? this.props.u_id : cookies.get('session_userid');
      // var ckgrpid = this.props.g_id ? this.props.g_id : cookies.get('activegrp');

      if(userid && grpid) {
         var data = {
           'userid': userid,
           'grpid': grpid,
           'UpSw': {...automtnOpt, [name]:checked},
         };
         axios.post(global.apiurl + '/mailoptswupdate', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if (res.status !== "true") {
               toast.error("Something went wrong!")
            }else{
               toast.success("E-mail settings updated");
            }          
         }).catch((error) => {
            // history.push("/")
         });
      }
   }

   return (
      <section className={props.className}>
         <div className={props.childclassName}>
            <Grid container spacing={3} className="">

            <MailToggle 
                  title="Daily status update"
                  mnloading={mnloading} 
                  name="DS" 
                  automtnOpt={automtnOpt}
                  mailOptSwitchfun={mailOptSwitchfun}
                  content="Receive daily updates on your keyword rankings. Enable this feature to get notified each time when there is an increase or decline in  your keyword’s ranking position."
               />

               <MailToggle 
                  title="Keyword URL/Slug change"
                  mnloading={mnloading} 
                  name="URL" 
                  automtnOpt={automtnOpt}
                  mailOptSwitchfun={mailOptSwitchfun}
                  content="Any change in your Slug/ URL  may lead to changes in your keyword ranking positions. Receive an alert whenever there occurs a change by enabling this feature."
               />

               <MailToggle 
                  title="New feature snippet"
                  mnloading={mnloading} 
                  name="FS" 
                  automtnOpt={automtnOpt}
                  mailOptSwitchfun={mailOptSwitchfun}
                  content="Enable this feature to know if your website gets featured in the featured snippet. You can also sneak-a-peek at the new featured snippets that your competitors have been ranked for."
               />

               <MailToggle 
                  title="New Ad snippet"
                  mnloading={mnloading} 
                  name="ADS" 
                  automtnOpt={automtnOpt}
                  mailOptSwitchfun={mailOptSwitchfun}
                  content="The ads displayed on Google's SERP will be dynamic for any of your keywords and, you need to be be aware of those who are fighting for the same keywords. By enabling this option, you will be notified with the new ads immediately and so taking further actions on your SEO plans will be quite an easy task."
               />

               <MailToggle 
                  title="New Ratings snippet"
                  mnloading={mnloading} 
                  name="RS" 
                  automtnOpt={automtnOpt}
                  mailOptSwitchfun={mailOptSwitchfun}
                  content="Never miss out any change in your review. Turn on this feature to recieve a notification email each time when there occurs a change in your ratings. You'll be the first to know any change that happens on your page."
               />

               <MailToggle 
                  title="Cannibalization alert"
                  mnloading={mnloading} 
                  name="CNN" 
                  automtnOpt={automtnOpt}
                  mailOptSwitchfun={mailOptSwitchfun}
                  content="When more than one of your pages gets ranked for the same keyword it would dilute your site’s rankings. Beware of keyword cannibalization by turning on this feature."
               />

               <MailToggle 
                  title="No improvement keywords"
                  mnloading={mnloading} 
                  name="NIMP" 
                  automtnOpt={automtnOpt}
                  mailOptSwitchfun={mailOptSwitchfun}
                  content="No change is a sign of progress too! Turn on this feature to receive alerts even when keywords don’t get ranked and lay snug like a bug on the rug."
               />

               <MailToggle 
                  title="Search Visibility Score alert"
                  mnloading={mnloading} 
                  name="SSA" 
                  automtnOpt={automtnOpt}
                  mailOptSwitchfun={mailOptSwitchfun} 
                  content="The SearchMirror Score alert feature intimates you how efficient is your overall organic performance based on your overall ranking improvement. Enable this feature to evaluate your site’s organic efficiency every now and then."
               />

               {/* <MailToggle 
                  title="Brand Conquest alert"
                  newtag={true}
                  mnloading={mnloading} 
                  name="BA" 
                  automtnOpt={automtnOpt}
                  mailOptSwitchfun={mailOptSwitchfun}
                  content="Enable this notification to get an instant alert when your competitors attempt to target your customers through Ads."
               /> */}


               {/*<Grid item xs={12} md={6} lg={6} xl={6}>
                  <section className="projectCard">
                     <div className="d-flex align-items-center justify-content-between m-b15">
                        <ParaLg class="fB m-b0 lh26x">Daily status update</ParaLg>
                        { mnloading ?
                           <Tsk width={46} height={24} className="" />
                        :
                           <AntSwitch
                              checked={automtnOpt.DS}
                              onChange={(e) => mailOptSwitchfun('DS', e.target.checked) }
                              inputProps={{ "aria-label": "ant design" }}
                           />
                        }
                     </div>
                     <Box sx={{ maxHeight: "100px", minHeight: "100px", overflowY: "auto" }} >
                        <Para>
                          Enabling this option will help you to get acquainted with the keyword ranking updates which becomes essential to take necessary actions on SEO strategy. You will be receiving an email with your keyword ranking updates. It shows how many keywords improved, declined, and have not changed.
                        </Para>
                     </Box>
                  </section>
               </Grid>*/}

            </Grid>
         </div>
      </section>
   );
}

export default MailNotifications;
