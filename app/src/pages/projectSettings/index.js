import React, { useState, useEffect } from "react";
import "./style.scss";
import { useParams, useHistory } from "react-router-dom";
import { Title, Para, Text, TextLg, AppButton } from "../commonComponents/parts";
import { Box, Grid, InputLabel } from "@mui/material";
import { Input } from "@/components/ui/input";
import Tab from '@mui/material/Tab';
import { TabContext, TabList, TabPanel } from '@mui/lab';
import Cookies from 'universal-cookie';
import MailNotifications from "../commonComponents/mail_notifications";
import ConnectedApp from "../commonComponents/connected_apps";
import { CloseIcon } from "../commonComponents/icons";
import { toast } from 'react-toastify';
import axios from 'axios';
import ProjectFavIcon from "../commonComponents/project_fav_icon";
import BrandKeywords from "./components/brand_keywords";
import ConnectPanel from "./components/connect_panel";
import SerpDepthPanel from "./components/serp_depth";
import { allowsTeamAction } from "../../utils/team_permissions";

// Settings is one destination now. These used to live behind /account, reachable
// only from the avatar dropdown, while the sidebar entry called "Settings"
// showed project settings -- so the account pages were the hard ones to find
// and AI Keys was linked from nowhere at all.
import AccountsModule from "../account/components/account";
import ProfileModule from "../account/components/profile";
import SerpKeyModule from "../account/components/serp_key";
import AiKeysModule from "../account/components/ai_keys";
import UserManagement from "../userManagement";

// The tab strip, its titles, its subtitles and its URL slugs in one place:
// /settings/apikey and the "API Key" tab cannot drift apart because they are
// the same string.
//
// Every tab used to print the project-settings subtitle -- "Recipients,
// connected apps and branded keywords for this project" -- over the API key
// form, the AI key form, the profile form and the member list, none of which
// are about a project at all. A tab that describes the wrong screen is worse
// than no subtitle, so each one now states what its own panel does.
//
// `project` is the only project-scoped tab; the rest belong to the account,
// which is why they must stay reachable with no project selected.
const TABS = [
   {
      value: "project",
      label: "Project settings",
      subtitle: "Recipients, connected apps and branded keywords for this project.",
      projectScoped: true,
   },
   {
      value: "account",
      label: "Account",
      // There is no plan and no usage on this panel -- this is a free,
      // self-hosted, bring-your-own-key product, and what the panel actually
      // holds is the password form and the note on how the account is closed.
      // The DataBlue credit balance, the only usage figure the product has,
      // is on the API Key tab and says so there.
      subtitle: "Change your password, or close this account.",
   },
   {
      value: "profile",
      label: "Profile",
      // The password is on the Account tab, not this one. This subtitle named
      // a control that is not on the panel it describes.
      subtitle: "Your name, e-mail and contact details.",
   },
   {
      value: "apikey",
      label: "DataBlue API Key",
      // Everything that decides what a DataBlue request costs lives here: the
      // key, pages per keyword, and extraction depth. The first two are
      // account-wide, the third is per project -- hence the project picker.
      subtitle: "Your DataBlue key, and what each rank check asks Google for.",
      projectScoped: true,
   },
   {
      value: "aikeys",
      label: "AI Keys",
      subtitle: "Provider keys for the AI features: content, competitors and Geo Citations.",
   },
   {
      value: "members",
      label: "Members",
      subtitle: "Team members, their roles and what each role may do.",
   },
];

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function SettingsManagement(props) {

   let { settingSlug, groupId } = useParams();
   const history = useHistory();
   const cookies = new Cookies();
   const isTeam = props.fullbasedata.ac_typ === "team";
   const availableTabs = isTeam ? TABS.slice(0, 1) : TABS;
   const canManageRecipients = allowsTeamAction(props.fullbasedata, "Settings", "Manage Recipients");
   const canManageBrandedKeywords = allowsTeamAction(props.fullbasedata, "Settings", "Manage Branded Keywords");
   const canManageConnectedApps = allowsTeamAction(props.fullbasedata, "Settings", "Manage Connected Apps");

   /* Which tab is open is a property of the address bar, not of this
      component. It used to be state, synced from the URL by handleAccountTitle
      -- and handleAccountTitle was only ever called from inside
      `if (projectList.length > 0)`, so with no projects the sync never ran and
      every /settings/* address rendered the Project settings tab. That made
      API Key and AI Keys unreachable on a brand-new account: the one thing a
      new user must do before anything else works is enter the DataBlue key, and
      the only route to that form landed them somewhere else.

      Reading the slug straight off the URL removes the sync rather than fixing
      it, so the two cannot disagree again. handleChange only has to navigate. */
   const activeTab = availableTabs.some((t) => t.value === settingSlug) ? settingSlug : "project";
   const activeTabMeta = availableTabs.find((t) => t.value === activeTab) || availableTabs[0];

   const [data, setData] = useState({
      baseData: {},                       // CHOOSEN PROJECT DATA
      projectList: props.projectList,     // COMPLETE PROJECT LIST
      loading: true,                     // PAGE ON LOADING
   });

   const [tags, setTags] = useState([]);

   const [oldtags, setOldtags] = useState([]);
   // Free BYOK product: there is no premium tier to gate this on.
   const [updateLoading, setUpdateLoading] = useState(false);
   const [reciptmailid, setReciptmailid] = useState('')

   const handleInitialise = (projectList) => {
      const cookies = new Cookies();
      var grpid = cookies.get('activegrp')

      var apidata = {}

      if (projectList.length > 0) {
         apidata = projectList.filter(item => item.GY === parseInt(grpid))[0];
         if (typeof (apidata) !== "object" || apidata.length === 0) {
            apidata = projectList[0];
         }
         cookies.set('activegrp', apidata.GY, { path: '/', maxAge: global.cookiesexpire });

         setData({
            ...data,
            baseData: apidata,
            loading: true,
         })
      }
   }

   const addTags = (event) => {
      const tag = event.target.value.trim().toLowerCase();
      if (event.key !== "Enter" || tag === "") {
         return;
      }
      if (!EMAIL_PATTERN.test(tag)) {
         toast.error("Enter valid e-mail");
      } else if (tags.length >= 5) {
         toast.error("Maximum 5 recipient e-mails only allowed");
      } else if (tags.some((email) => email.toLowerCase() === tag)) {
         toast.error('The email is already added.');
      } else {
         setTags([...tags, tag]);
         setReciptmailid('');
      }
   };

   const removeTags = (index) => {
      setTags([...tags.filter((tag) => tags.indexOf(tag) !== index)]);
   };

   var { loading } = data;
   const [grpId, setGrpId] = useState(groupId)
   const hasProject = (props.projectList || []).length > 0;


   useEffect(() => {
      // Without this the request outlives the route change and its .then calls
      // setTags on a component that is already gone.
      const controller = new AbortController();
      const cookies = new Cookies();
      if (groupId === undefined || groupId === '') {
         setGrpId(cookies.get('activegrp'))
      }
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid');
      const ckgrpid = parseInt(cookies.get('activegrp'));
      // Recipients belong to a project. With none there is no id to ask about,
      // and parseInt(undefined) posted a NaN that serialises to null.
      if (Number.isInteger(ckgrpid)) {
         var data = {
            'userid': userid,
            'grpid': ckgrpid
         };
         axios.post(global.apiurl + '/rpntmailupdate', data, {
            headers: { 'Authorization': 'Token ' + usertoken },
            signal: controller.signal
         }).then(response => {
            return response.data;
         }).then(res => {
            // console.log('...............response',res)
            if (res.status !== "true") {
               // console.log(res.message);
               toast.error(res.message)
            } else {
               // console.log(res)
               setTags(res.rp_m)
               setOldtags(res.rp_m)
            }
         }).catch((error) => {
            // console.log('.......error receiving data')
         });
      }
      handleInitialise(props.projectList)

      return () => controller.abort();
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, []);



   const reciptmailchgfun = (e) => {
      var value = e.target.value;
      if (value.length > 80) {
         toast.error('Maximum length exceeded')
      } else {
         setReciptmailid(value);
      }
   }

   const handleChange = (event, newValue) => {
      // The URL is the only record of which tab is open, so a settings tab can
      // be linked and reloaded rather than only reached by clicking.
      history.replace(newValue === "project" ? "/settings" : "/settings/" + newValue);
   };

   const rcpntMailUpdate = () => {
      setUpdateLoading(true)
      var gtags = tags;
      const currenttag = tags;
      const tag = reciptmailid.trim();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid');
      const ckgrpid = parseInt(cookies.get('activegrp'));

      if (userid && ckgrpid) {
         if (!EMAIL_PATTERN.test(tag) && tag !== "") {
            toast.error("Enter valid e-mail");
            setUpdateLoading(false);
            return false;
         } else if (gtags.length > 5 || (gtags.length === 5 && tag !== "")) {
            toast.error("Maximum 5 recipient e-mails only allowed");
            setUpdateLoading(false);
            return false;
         } else if (currenttag.filter(tags => tags === tag).length !== 0 && tag !== "") {
            toast.error("E-mail was already added");
            setUpdateLoading(false);
            return false;
         } else if (JSON.stringify(tags) === JSON.stringify(oldtags) && tag === "") {
            toast.error("Add new recipient e-mail")
            setUpdateLoading(false);
            return false;
         } else {
            var data = {
               'userid': userid,
               'grpid': ckgrpid,
               'rp_m': tag === '' ? tags : [...tags, tag]
            };
            axios.post(global.apiurl + '/rpntmailupdate', data, {
               headers: { 'Authorization': 'Token ' + usertoken }
            }).then(response => {
               return response.data;
            }).then(res => {
               // console.log('.............update respi',res)
               if (res.status !== "true") {
                  toast.error(res.message)
               } else {
                  toast.success(res.message)
                  setTags(res.rp_m)
               }
               setReciptmailid('')
               setUpdateLoading(false);
            }).catch((error) => {
               // console.log('update error',error);
            });
         }
      }
   }

   return (
      <>
         {loading ?
            <section className="layout">
               <div>
                  <header>
                     <div className="d-flex flex-wrap gap-3 align-items-center">
                        {/* The project picker only belongs beside a tab that is
                            about a project; on Profile or API Key it offered a
                            choice that changed nothing on screen. */}
                        {activeTabMeta.projectScoped && hasProject ? <ProjectFavIcon projectList={props.projectList} /> : null}
                        <div>
                           <Title class="wd-title">{activeTabMeta.label}</Title>
                           <Para class="wd-subTitle">{activeTabMeta.subtitle}</Para>
                        </div>
                     </div>
                  </header>

                  <div className="keywordDetail prjtsettingstab">
                     <Box sx={{ width: '100%', typography: 'body1' }}>
                        <TabContext value={activeTab}>
                           <div className="tabStrip">
                              <TabList
                                 onChange={handleChange}
                                 variant="scrollable"
                                 scrollButtons={false}
                                 aria-label="scrollable prevent tabs example"
                              >
                                 {availableTabs.map((t) => (
                                    <Tab key={t.value} label={t.label} value={t.value} />
                                 ))}
                              </TabList>
                           </div>
                           <TabPanel value="project">
                              {!hasProject ?
                                 /* Everything on this tab is scoped to a project
                                    id. Without one the forms would post against
                                    nothing; the other tabs stay usable, which is
                                    the point -- the API key has to be enterable
                                    before the first project exists. */
                                 <div className="emptyState">
                                    <p className="emptyState__label">No projects</p>
                                    <p className="emptyState__body">
                                       Report recipients, connected apps and branded
                                       keywords all belong to a project. Add one and
                                       this tab fills in &mdash; the other tabs work
                                       without it.
                                    </p>
                                 </div>
                                 :
                              <>
                              <div>
                                 <Grid container spacing={3} className="">
                                    <Grid item xs={12} md={12} lg={5}>
                                       <Text class="text-justify">
                                          You can add up to <span className="fB">5 recipients</span> for automated e-mails on this project.
                                       </Text>
                                       <div className="addtag m-t30">
                                          <div className="tags-input">
                                             <InputLabel shrink>Who should receive this project's scheduled reports.</InputLabel>
                                             <Input
                                                id="outlined-basic"
                                                onKeyUp={(event) => (event.key === "Enter" ? addTags(event) : null)}
                                                onBlur={props.onchange}
                                                placeholder="demo@gmail.com"
                                                onChange={reciptmailchgfun}
                                                value={reciptmailid}
                                                disabled={!canManageRecipients}
                                             />

                                             <h2 className="smallTitle m-b15 m-t15">Recipients</h2>

                                             {tags.length === 0 ?
                                                <InputLabel shrink>No recipients added</InputLabel>
                                                :
                                                <ul>
                                                   {tags.map((tag, index) => (
                                                      <li key={index}>
                                                         <span>{tag}</span>
                                                         {canManageRecipients ? (
                                                            <span className="close m-l10" onClick={() => removeTags(index)}>
                                                               <CloseIcon />
                                                            </span>
                                                         ) : null}
                                                      </li>
                                                   ))}
                                                </ul>
                                             }
                                             {canManageRecipients ? (
                                                <AppButton
                                                   onclick={rcpntMailUpdate}
                                                   loading={updateLoading}
                                                   value="Update"
                                                   class="m-t30 wd-btn-add"
                                                   noIcon="d-none"
                                                ></AppButton>
                                             ) : (
                                                <Text class="secondaryClr m-t15">Read-only access.</Text>
                                             )}
                                          </div>
                                       </div>
                                    </Grid>
                                    <Grid item xs={12} md={12} lg={7} className="d-none d-md-block">
                                    </Grid>
                                 </Grid>
                              </div>

                              {/* Connected apps and branded keywords were tabs of
                                  their own. They are short, they belong to the same
                                  project, and stacking them costs one scroll instead
                                  of two clicks. */}
                              <div className="settingsSection">
                                 <TextLg class="fB lineHAuto m-b5">Connected apps</TextLg>
                                 {/* Live connection status for this project,
                                     above the controls that change it. It was
                                     the top strip of the dashboard, where it was
                                     the most prominent element on the page and
                                     reported both integrations unavailable on a
                                     default install. */}
                                 <ConnectPanel />
                                 <ConnectedApp className="" groupId={grpId} canManage={canManageConnectedApps} />
                              </div>

                              <div className="settingsSection">
                                 <TextLg class="fB lineHAuto m-b5">Branded keywords</TextLg>
                                 <BrandKeywords canManage={canManageBrandedKeywords} />
                              </div>
                              </>
                              }
                           </TabPanel>
                           {!isTeam ? <>
                              <TabPanel value="account">
                                 <AccountsModule baseauth={props.baseauth} />
                              </TabPanel>

                              <TabPanel value="profile">
                                 <ProfileModule />
                              </TabPanel>

                              <TabPanel value="apikey">
                                 <SerpKeyModule />
                                 {/* Depth is per project while the key and
                                     pages above are per account, so it names
                                     its scope and follows the project picker in
                                     the header. */}
                                 <div className="settingsSection">
                                    <SerpDepthPanel grpid={parseInt(cookies.get('activegrp'), 10)} />
                                 </div>

                                 <div className="settingsSection">
                                    <h2 className="smallTitle m-b15">Tracking schedule</h2>
                                    <p className="depthNote">
                                       <span className="depthNoteLead">Every project is checked once a day, overnight.</span> Runs
                                       start in the 01:00 hour, server time, and projects are spread across
                                       it so they do not all call the provider at once. Each run bills your
                                       own DataBlue key.
                                    </p>
                                    <p className="depthNote">
                                       <span className="depthNoteLead">Need it sooner?</span> Refresh on the
                                       Keywords page re-checks a project immediately. That is billed the same
                                       way, and it does not change the daily schedule.
                                    </p>
                                 </div>
                              </TabPanel>

                              <TabPanel value="aikeys">
                                 <AiKeysModule />
                              </TabPanel>

                              <TabPanel value="members">
                                 {/* Its Team and Roles panels read a context built in
                                     that page, so it is embedded whole rather than
                                     pulled apart -- `embedded` drops its page shell. */}
                                 <UserManagement embedded projectList={props.projectList} fullbasedata={props.fullbasedata} />
                              </TabPanel>
                           </> : null}
                        </TabContext>
                     </Box>
                  </div>
               </div>
            </section>
            :
            <div className="d-flex justify-content-center align-items-center text-center h100vh">
               <div className="loading" />
            </div>
         }
      </>
   );

}

export default SettingsManagement;
