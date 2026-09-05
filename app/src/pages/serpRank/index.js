import React, { useState, useEffect } from "react";
import { useHistory } from "react-router-dom";
import "swiper/css";
import { ParaLg, Para, Title, Tsk } from "../commonComponents/parts";
import { Button } from "@/components/ui/button";
import { AddKeywordIcon } from "../commonComponents/icons";
import Cookies from 'universal-cookie';
import axios from 'axios';
import SerpRankTable from "./serp_rank_table";
import EmailSetting from "./components/serp_rank_email_setting";
import { SerpOverview } from "./components/serp_overview";
import { toast } from 'react-toastify';
import { ModalBox, RevokeGSCAccess } from "../commonComponents/Modals";
import ProjectFavIcon from "../commonComponents/project_fav_icon";
import { allowsTeamAction } from '../../utils/team_permissions';

// GSC CONNECTION
import GSConnect from "../commonComponents/gsc_connect"
import { GoogleOAuthProvider } from '@react-oauth/google';

const gscClientId = global.gscClientId;



//
function SerpRank(props) {

   const history = useHistory();
   const [overview, setOverview] = useState(false);
   const [overviewswt, setOverviewswt] = useState(null);
   const [pageupdate, setPageupdate] = React.useState(false);
   const [basedata, setbasedata] = useState({});
   const [refresh_on, setRefresh_on] = useState(false);
   const canAddKeywords = allowsTeamAction(props.fullbasedata, "Keyword", "Add Keywords");

   const [gsctoken, setGsctoken] = useState('')
   const [openRevokeModal, setopenRevokeModal] = useState(false);
   const handleRevokeClose = () => setopenRevokeModal(false);
   const handleRevokeOpen = () => setopenRevokeModal(true);
   const refreshPage = () => { setopenRevokeModal(false); };

   useEffect(() => {
      // updateAccessToken's response outlives a route change unless the request
      // is aborted here; its .then calls setGsctoken on an unmounted component.
      const controller = new AbortController();
      global.PageTopLoader.current.continuousStart();
      const cookies = new Cookies();
      var grpid = cookies.get('activegrp')
      var apidata = {}
      var overview = true
      var gsc_token = 0
      if (props.projectList.length > 0) {
         apidata = props.projectList.filter(item => item.GY === parseInt(grpid))[0]
         if (typeof (apidata) !== "object" || apidata.length === 0) {
            apidata = props.projectList[0]
         }
         cookies.set('activegrp', apidata.GY, { path: '/', maxAge: global.cookiesexpire });
         grpid = apidata.GY
         overview = apidata.OV
         gsc_token = props.fullbasedata.gscT
      }

      setbasedata(apidata);
      setOverview(overview)
      setOverviewswt(overview)
      setGsctoken(gsc_token)

      // GSC is parked until the instance has a real OAuth client. Do not call
      // the retired page-audit token bridge in an unconfigured build.
      if (gscClientId) {
         updateAccessToken(controller.signal)
      }

      return () => controller.abort();
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [props.projectList]);

   const updateAccessToken = (signal) => {
      const cookies = new Cookies();
      const userid = cookies.get('session_userid');
      const usertoken = cookies.get('session_token');
      const grpid = cookies.get('activegrp');

      const data = {
         'userid': userid,
         'grpid': grpid
      };

      axios.post(global.apiurl + '/pageaudit/getaccesstoken', data, {
         headers: { 'Authorization': 'Token ' + usertoken },
         signal
      }).then(response => {
         return response.data;
      }).then(res => {
         if (res.status === "true") {
            setGsctoken(res.acc_tkn)
         }
         else {
            setGsctoken('')
         }
      }).catch((error) => {
         /* history.push("/keywords") */
      });
   }


   const updatefullpage = () => {
      props.baseauth("update")
      setPageupdate(!pageupdate)
   }

   const overviewSwtFun = (e) => {
      setOverviewswt(e.target.checked);
      setOverview(true);
      const cookies = new Cookies();
      const userid = cookies.get('session_userid');
      const grpid = cookies.get('activegrp');
      const usertoken = cookies.get('session_token')

      if (userid && grpid) {
         var data = {
            'userid': userid,
            'grpid': grpid,
            'view': e.target.checked,
         };
         axios.post(global.apiurl + '/project_overview_change', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {

         }).catch((error) => {
            // history.push("/")
         });
      }
   }


   const addKeywordLink = () => {
      history.push("/addkeyword")
   }

   const updateAcsToken = (token) => {
      setGsctoken(token)
   }

   return (
      <>
         {/* Object.keys(basedata).length ?*/}
         {(props.projectList.length > 0 && Object.keys(basedata).length > 0) ?
            <section className={"layout" + (refresh_on ? " refreshing-in" : "")}>
               <div>

                  <header>
                     {/* className="m-b10" */}
                     <div className="d-flex justify-content-between flex-wrap gap-3">
                        <div className="d-flex flex-wrap gap-3 align-items-center">
                           <ProjectFavIcon projectList={props.projectList} />
                           <div>
                              {/* The separator between the project name and the
                                  refresh time was a capital I -- "Local demo
                                  project I Updated: 4 days ago" -- which reads
                                  as part of the sentence. The project name was
                                  also re-cased on the way out, first letter up
                                  and the rest down, so "DataBlue" was shown as
                                  "Datablue" here while the rail beside it
                                  showed the name as stored. */}
                              <Title class="wd-title">Keyword rankings</Title>
                              <Para class="wd-subTitle m-b0 d-flex align-items-center gap-2 lh14x">
                                 <span>{basedata.NM}</span>
                                 <span aria-hidden="true">&middot;</span>
                                 <span className="d-flex align-items-center">Updated: {basedata ? basedata.rf_t : <Tsk width={100} className="m-l5 h14x" />}</span>
                              </Para>
                           </div>
                        </div>
                        <div className="d-flex align-items-center twoButton addkeyhdr dashboard flex-[0_0_auto] gap-[0.6rem]">

                           {/* <Box
                              className=""
                              sx={{ minWidth: "145px", maxWidth: "165px", flex: "0 0 auto" }}
                           >
                              <GoogleOAuthProvider clientId={gscClientId}>
                                 <GSConnect gsctoken={gsctoken} handleOpen={handleRevokeOpen} updateAcsToken={updateAcsToken} revokeOption="0" />
                              </GoogleOAuthProvider>
                           </Box> */}

                           {/* <EmailSetting /> */}

                           {canAddKeywords ? <div className="min-w-[145px] max-w-[150px] flex-[0_0_auto]">
                              <Button variant="primary" onClick={addKeywordLink} className="w-full wd-btn-add p-l0 p-r0">
                                 <span className="d-flex m-r10"><AddKeywordIcon /></span>
                                 <span>Add Keyword</span>
                              </Button>
                           </div> : null}

                        </div>
                     </div>
                  </header>

                  <div id="smoothscrollbar" className="lightscroll scroll-y-trnspnt">
                     <section className="project_overviewCard no-outline m-b30 p-t15">
                        <div className="d-flex justify-content-between align-items-center">
                           <ParaLg class="fB mb-0 lineHAuto"> Overview</ParaLg>
                           {/* This was a bespoke MUI Switch with "Hide" and "Show"
                               baked into the track's ::before/::after and an
                               --accent fill when on. --accent means "act on this",
                               so collapsing a panel was the loudest control on the
                               page, and the word inside the track named the state
                               it was NOT in. A secondary button says what pressing
                               it does, in the app's own button. */}
                           <Button
                              variant="secondary"
                              className="ovToggle"
                              aria-expanded={Boolean(overviewswt)}
                              aria-controls="serpOverviewPanel"
                              onClick={() => overviewSwtFun({ target: { checked: !overviewswt } })}
                           >
                              {overviewswt ? "Hide" : "Show"}
                           </Button>
                        </div>

                        <div id="serpOverviewPanel">
                           {overview ?
                              <SerpOverview className={overviewswt ? "" : "d-none"} basedata={basedata} update={pageupdate} />
                              : null}
                        </div>
                     </section>

                     <SerpRankTable projectList={props.projectList} fullbasedata={props.fullbasedata} basedata={basedata} updatefullpage={updatefullpage} baseauthdataUpdate={props.baseauthdataUpdate} refresh_on={refresh_on} refresh_onUpdate={(swt) => setRefresh_on(swt)} />

                  </div>
               </div>
            </section>
            : overviewswt !== null ?
               /* This branch is reached when the account has no projects at all,
                  and it used to say "No keyword found" over an illustration and
                  then, in the next line, that no PROJECT had been added -- two
                  different facts in one message, with the only way out (the Add
                  project button) commented out underneath. A rank tracker with
                  no project cannot have a keyword, so the missing project is the
                  thing to say, and the button that fixes it is the thing to
                  show. docs/DESIGN.md: micro-label, one sentence, one action,
                  no art. */
               <div className="d-flex justify-content-center align-items-center text-center h-100">
                  <div className="emptyState">
                     <p className="emptyState__label">No projects yet</p>
                     <p className="emptyState__body">
                        Add the site you want to track and the keywords you want to watch, and rankings start appearing here.
                     </p>
                     <Button variant="primary" className="emptyState__action" onClick={() => history.push("/addproject")}>
                        Add project
                     </Button>
                  </div>
               </div>
               : null}

         <ModalBox title="" onClose={handleRevokeClose} open={openRevokeModal} >
            <RevokeGSCAccess modalClose={handleRevokeClose} revokeSuccess={refreshPage} />
         </ModalBox>
      </>
   );
}

export default SerpRank;
