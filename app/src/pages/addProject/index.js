import React, { useState, useEffect } from "react";
import { Link, useHistory } from "react-router-dom";
import Header from "../commonComponents/header";
import { TagsInput, KeywordInput, BrandKeywordInput } from "../commonComponents/manage_tag";
import { CloseIcon, DesktopIcon, MobileIcon, AddProjectIcon, GoOverviewPageIcon } from "../commonComponents/icons";
import { Grid, InputLabel } from "@mui/material";
import "./style.scss";
import { AppButton, SmallText, Input, SelectLang, KNRSelectRegion, Para, AppTooltip, SelectMenu } from "../commonComponents/parts";
import { Switch, CircularProgress } from "@mui/material";
import { styled } from "@mui/material/styles";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';
import { CsvUpload } from "./components/csv_upload";
import { ModalBox, ConfirmDialog, PropertyModalBox } from "../commonComponents/Modals";
import { useGoogleLogin } from '@react-oauth/google';
import SafeGoogleOAuthProvider from '../commonComponents/safe_google_oauth';
import ComingSoon from '../commonComponents/coming_soon';
import GSC_connection from "./components/gsc";
import GA_connection from "./components/ga_connection";
import PropertyModel from "./components/property_model";
import GSCPropertyModel from "../commonComponents/gsc_property_model"
import { revealFormError } from "../commonComponents/form_feedback";
import { findSearchRegion, normalizeSearchDefaults } from "../common_fun";
import { SerpDepthChoice, DEPTH_LITE, DEPTH_ADVANCED, writeSerpDepth } from "../projectSettings/components/serp_depth";


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
            backgroundColor: "var(--accent)",
         },
      },
   },
   "& .MuiSwitch-thumb": {
      boxShadow: "0 2px 4px 0 rgb(0 35 11 / 20%)",
      width: 12,
      height: 12,
      borderRadius: 6,
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

function AddProject(props) {

   const history = useHistory();
   const [wsurl, setWsurl] = useState('');
   const [ckurl, setCkurl] = useState('');

   const [domainvalidate, setDomainvalidate] = useState('notvalid');
   const [wsurlerrmsg, setWsurlerrmsg] = useState('');
   // One ref per validated field. A blocked submit scrolls the offending
   // field into view and focuses it, so the failure cannot happen off-screen.
   const wsurlRef = React.useRef(null);
   const regionRef = React.useRef(null);
   const langRef = React.useRef(null);
   const pnameRef = React.useRef(null);
   const keywordRef = React.useRef(null);
   const gaPropertyRef = React.useRef(null);
   const trackDayRef = React.useRef(null);

   const [pname, setPname] = useState('');
   const [pnmerrmsg, setPnmerrmsg] = useState('');
   const [lang, setLang] = useState("");
   const [langerrmsg, setLangerrmsg] = useState('');
   const [btnloading, setBtnloading] = useState(false);
   const [langoptions, setLangoptions] = useState([]);
   // Region and keywords used to fail with a toast only, which vanishes before
   // the user has looked back at the form. These mirror the toast next to the
   // control that is actually wrong -- presentation of an existing failure,
   // not a new validation rule.
   const [rgnerrmsg, setRgnerrmsg] = useState('');
   const [kwerrmsg, setKwerrmsg] = useState('');
   const [remainkeyaddcount, setRemainkeyaddcount] = useState(0);
   const kwUnlimited = remainkeyaddcount > 1000000;
   // Under BYOK the keyword allowance defaults to serp.models.UNMETERED (1e9),
   // and the UI shows allowance-minus-used, so it arrives as ~999,999,99x --
   // just under the sentinel, never equal to it. A real plan cap is in the
   // tens or hundreds; anything past a million is the unmetered value, not a
   // limit worth printing (it was showing "999999992" twice on this page).
   const [platform, setPlatform] = useState("desktop");
   // /addnewkey has no "adv" field, so this is held here and written with
   // /prjctserpmode once the new group id comes back. Lite until asked.
   const [serpAdvanced, setSerpAdvanced] = useState(DEPTH_LITE);
   const [tagopt, setTagopt] = useState(false);
   const [selectedtags, setSelectedtags] = useState([]);
   const [keywordlist, setKeywordlist] = useState([]);
   const [onCallLoad, setOnCallLoad] = useState(true);
   const [dmnchckreturnurl, setDmnchckreturnurl] = useState('');

   const [rgoptions, setRgoptions] = useState([]);
   const [fltrregion, setfltrRegion] = useState([]);
   const [region, setRegion] = useState("");
   const [isocode, setIsocode] = useState("");
   const [countryname, setCountryname] = useState("");

   const [loadKeywords, setLoadKeywords] = useState(-1);

   const [gscToken, setGSCToken] = useState("");
   const [gscProperty, setGSCProperty] = useState("")
   const [gscProperties, setGSCProperties] = useState([]);
   const [gscPrtyMdlVsble, setGSCPrtyMdlVsble] = React.useState(false);
   const [revokeGSCModal, setGSCRevokeModal] = React.useState(false);

   const [weekDays, setWeekDays] = React.useState(["Daily", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]);
   const [trackDay, setTrackDay] = React.useState('');
   const [trackDayErr, setTrackDayErr] = React.useState('');

   const [gaToken, setGARfrshTkn] = useState("")
   const [editPrjtMdlVsble, setEdtPrjtMdlVsble] = useState(false)
   const [data, setData] = useState(null)
   const [revokeGA, setRevokeGA] = useState(false)
   const [property, setProperty] = useState("")

   // Brand Keywords
   const [brandKWSwitch, setBrandKWSwitch] = useState(false);
   const [brandOpts, setBrandOpts] = useState([]);
   // Search Console and Analytics are parked until the instance configures a
   // Google OAuth client; with no client id their controls render nothing.
   const googleConfigured = Boolean(global.gscClientId || global.gaClientId);
   const [dmPlatform, setDmPlatform] = useState('')
   const [dmPlatformErr, setDmPlatformErr] = useState('')

   useEffect(() => {
      global.PageTopLoader.current.continuousStart();
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')

      const data = {
         'userid': userid,
         'grpid': 0
      };
      axios.post(global.apiurl + '/getsetting', data, {
         headers: { 'Authorization': 'Token ' + usertoken }
      }).then(response => {
         return response.data;
      }).then(res => {
         if (res.status !== "true") {
            const msg = res.message;
            toast.error(msg)
         } else {
            if (res.g_l >= res.pPL || res.u_kw >= res.pKL) {
               history.push("/");
               // window.location.assign(window.location.origin+"/app"); 
            }
            setLangoptions(res.lnge)
            setRgoptions(res.rg)
            setfltrRegion(res.rg)
            setRemainkeyaddcount(res.pKL - res.u_kw)

            const defaults = normalizeSearchDefaults(res.rg, res.lnge, res.DR);
            setIsocode(defaults.isocode)
            setRegion(defaults.region)
            setCountryname(defaults.countryname)
            setLang(defaults.language)
         }
      }).catch((error) => {
         // history.push("/login");  
      });

      setTimeout(() => {
         global.PageTopLoader.current.complete();
      }, 1000);

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, []);

   const projectNameChgfun = (e) => {
      if ((/^[a-zA-Z0-9 ]+$/.test(e.target.value) || e.target.value === "") && e.target.value.length < 31) {
         setPname(e.target.value);
         setPnmerrmsg("")
      }
   }

   const addKeyword = (event) => {
      const cookies = new Cookies();
      const userid = cookies.get('session_userid');

      var pattern = new RegExp('^((ft|htt)ps?:\\/\\/)?' + // protocol
         '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|' + // domain name and extension
         '((\\d{1,3}\\.){3}\\d{1,3}))' + // OR ip (v4) address
         '(\\:\\d+)?' + // port
         '(\\/[-a-z\\d%@_.~+&:]*)*' + // path
         '(\\?[;&a-z\\d%@_.,~+&:=-]*)?' + // query string
         '(\\#[-a-z\\d_]*)?$', 'i'); // fragment locator

      var urls = wsurl;

      if (userid) {
         if (!wsurl.trim()) {
            setWsurlerrmsg("Enter URL");
            revealFormError("Enter URL", wsurlRef);
            return false
         } else if (!pattern.test(wsurl)) {
            setWsurlerrmsg("Enter a valid URL");
            revealFormError("Enter a valid URL", wsurlRef);
            return false
         } else if (region.length === 0) {
            setRgnerrmsg("Select your region");
            revealFormError("Select your region", regionRef);
            return false
         } else if (lang.length === 0) {
            setLangerrmsg("Select your language")
            revealFormError("Select your language", langRef);
            return false
         } else if (!pname.trim()) {
            setPnmerrmsg("Enter project name")
            revealFormError("Enter project name", pnameRef);
            return false
         } else if (!/^[a-zA-Z0-9 ]+$/.test(pname)) {
            setPnmerrmsg("Not allowed special characters");
            revealFormError("Not allowed special characters", pnameRef);
            return false;
         } else if (keywordlist.length === 0) {
            setKwerrmsg("Add at least one keyword to track")
            revealFormError("Add at least one keyword to track", keywordRef);
            return false
         } else if (domainvalidate === "notvalid") {
            setWsurlerrmsg("Domain is invalid. Enter the correct domain name");
            revealFormError("Domain is invalid. Enter the correct domain name", wsurlRef);
            return false
         } else if (gaToken && !property) {
            revealFormError("Select the Google Analytics property to track", gaPropertyRef);
            return false
         } else if (trackDay.length === 0) {
            setTrackDayErr("Select Your Tracking Schedule");
            revealFormError("Select your tracking schedule", trackDayRef);
            return false
         } else {
            var exactdomain = false;
            addfreshkeyfn(wsurl, keywordlist, pname, exactdomain);
         }
      }
   }

   const addfreshkeyfn = (wsurl, keywordlist, pname, exactdomain) => {
      const cookies = new Cookies();
      const userid = cookies.get('session_userid');
      const usertoken = cookies.get('session_token')

      setBtnloading(true)

      const data = {
         'userid': userid,
         'url': wsurl,
         'keyword': keywordlist,
         'platform': platform,
         'region': region,
         'countryname': countryname,
         'isocode': isocode,
         'language': lang,
         'exactdomain': false,
         'gsctoken': gscToken,
         'gsc_property': gscProperty,
         'ga_property': property,
         'ga_token': gaToken,
         'trackDay': trackDay[0]
      };

      if (dmPlatform.length !== 0) {
         data['dmPlatform'] = dmPlatform[0]
      }

      if (tagopt === true && selectedtags.length > 0) {
         data['tags'] = selectedtags;
      }

      if (brandKWSwitch === true && brandOpts.length > 0) {
         data['brand_keywords'] = brandOpts;
      }

      data['newGrp'] = JSON.stringify({
         'fk_user': userid,
         'group_name': pname,
         'domain_name': dmnchckreturnurl,
      });

      if (onCallLoad === true) {
         setOnCallLoad(false);

         axios.post(global.apiurl + '/addnewkey', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(resp => {
            if (resp.status === 'true') {
               if (resp.message === 'warning') {
                  toast.warning(resp.errormsg)
               }
               // Only fired for Advanced: Lite is the stored default.
               if (serpAdvanced === DEPTH_ADVANCED && resp.grpid) {
                  writeSerpDepth(resp.grpid, DEPTH_ADVANCED).catch(() => {
                     toast.warning("Project created, but the extraction depth stayed on Lite. Set it in Project settings.")
                  });
               }
               setTimeout(() => {
                  cookies.set('ckgrp', resp.grpid, { path: '/', maxAge: global.cookiesexpire });
                  cookies.set('activegrp', resp.grpid, { path: '/', maxAge: global.cookiesexpire });
                  if (resp.Engmd === 0) {
                     toast.error("Manual refresh is currently disabled. You'll have it back soon.")
                  }
                  history.push('/');
               }, 1500);
            } else {
               setBtnloading(false)

               if (resp.message === 'warning') {
                  toast.warning(resp.errormsg)
               } else {
                  toast.error(resp.message)
               }
            }
            setOnCallLoad(true)
         }).catch(err => {
            setOnCallLoad(true)
            setBtnloading(false)
         });
      }
   }


   const selectlstChange = (event) => {
      const { target: { value }, } = event;

      setLangerrmsg('');
      setLang(value);
   };

   const keywordDelete = (i) => {
      setKeywordlist([...keywordlist.filter((tag, index) => index !== i)]);
   };

   // Website Target Keywords - Axios
   const target_keywords_scrap = (e) => {
      const cookies = new Cookies();
      const userid = cookies.get('session_userid');
      const usertoken = cookies.get('session_token');

      if (wsurl !== ckurl) {
         setCkurl(wsurl);

         const data = {
            'userid': userid,
            '_stN_': wsurl,
         };

         setLoadKeywords(0)

         axios.post(global.apiurl + '/AP_d2V20ic2ZJnV5d2V90YX9ylZXRfaZHM', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(resp => {
            if (resp.status === 1) {
               setDomainvalidate("valid");
               setDmnchckreturnurl(resp.st)
               setKeywordlist(resp.ds)
               setLoadKeywords(1)
            } else if (resp.status === 0) {
               setDomainvalidate("valid");
               setDmnchckreturnurl(resp.st)
               setKeywordlist([])
               toast.error("No Keyword Suggestions found for the Website")
               setLoadKeywords(-1)
            } else if (resp.status === -1) {
               setWsurlerrmsg(resp.ms);
               setDomainvalidate("notvalid");
               setKeywordlist([])
               setLoadKeywords(-1)
            } else {
               setKeywordlist([])
               toast.error("Sorry, Keyword Suggestions temporarily unavailable!")
               setLoadKeywords(-1)
            }
         }).catch(err => {
            setKeywordlist([])
            toast.error("Try again later! ")
            setLoadKeywords(-1)
         });
      }
   }

   const doAction = (cval) => {
      setCkurl("")
      if (cval === "clear") {
         setKeywordlist([])
         setLoadKeywords(2)
      } else if (cval === "reload") {
         setLoadKeywords(0)
         setTimeout(() => {
            target_keywords_scrap()
         }, 1000);
      }
   }

   const rgselectlstChange = (event) => {
      const { target: { value }, } = event;
      const selected = findSearchRegion(rgoptions, value);
      setRegion(selected ? selected.RN : "");
      setCountryname(selected ? selected.Rcnt : "");
      setIsocode(selected ? selected.Rcd : "");
      setRgnerrmsg("");
   }

   const regionListdataUpdate = (data) => {
      setfltrRegion(data);
   }

   const menuOpen = () => {
      setfltrRegion(rgoptions);
   }

   const emptyfun = () => {

   }

   const Improved = (
      <div>
         <Para class="m-0">
            Add relevent tags to your keywords .
         </Para>
      </div>
   );

   const BrandKeyword = (
      <div>
         <Para class="m-0">
            Branded keywords are any search queries that are directly associated with your brand, products, or services.
         </Para>
      </div>
   );

   const GSCInfo = (
      <div>
         <Para class="m-0">
            Integrate your Google Search Console (GSC) account to effortlessly monitor keyword performance.
         </Para>
      </div>
   );

   const TrackingInfo = (
      <div>
         <Para class="m-0">
            Each week, tracking will occur on the chosen day
         </Para>
      </div>
   );
   const ChoosePlatInfo = (
      <div>
         <Para class='m-0'>
            Select the category of your domain to proceed. Choose <b>E-commerce</b> for online stores and businesses or <b>Non E-commerce</b> for informational, service-based,
         </Para>
      </div>
   )
   const GAInfo = (
      <div>
         <Para class="m-0">
            Integrate your Google Analytics account to effortlessly monitor website traffic.
         </Para>
      </div>
   )

   const revokeConfirmed = () => {
      setGSCToken("")
      setGSCProperty("")
      setGSCProperties([])
      setGSCRevokeModal(false)
      toast.success("GSC Account Revoked")
   }
   const handleGaRevoke = () => {
      setGARfrshTkn("")
      setProperty("")
      setRevokeGA(false)
      toast.success('GA Account Revoked')
   }

   const handlePropertySelect = (property_data) => {
      setProperty(property_data.property)
      setEdtPrjtMdlVsble(false)
   }

   const handleGSCPropertySelect = (property) => {
      // console.log(property)
      setGSCProperty(property)
      setGSCPrtyMdlVsble(false)
   }

   const handleTrackDay = (event) => {
      const { target: { value }, } = event;
      setTrackDay(typeof value === "string" ? value.split(",") : value[0]);
      setTrackDayErr("")
   };
   const handlePlatform = (event) => {
      const { target: { value }, } = event;
      setDmPlatform(typeof value === "string" ? value.split(",") : value[0]);
      setDmPlatformErr("")
   };

   return (
      <>
         <PropertyModalBox title="Choose An Account" onClose={() => { setEdtPrjtMdlVsble(!editPrjtMdlVsble); setData(null) }} open={editPrjtMdlVsble} >
            <PropertyModel data={data} handlePropertySelect={handlePropertySelect} />
         </PropertyModalBox>

         <PropertyModalBox title="Choose a Property" onClose={() => setGSCPrtyMdlVsble(!gscPrtyMdlVsble)} open={gscPrtyMdlVsble} >
            <GSCPropertyModel gscdata={gscProperties} handleGSCPropertySelect={handleGSCPropertySelect} />
         </PropertyModalBox>

         <ModalBox title="" open={revokeGSCModal} onClose={() => { setGSCRevokeModal(false) }}>
            <ConfirmDialog
               title="Revoke GSC Access"
               cancelTitle="Cancel"
               confirmTitle="Revoke"
               modalCancel={() => { setGSCRevokeModal(false) }}
               modalConfirm={revokeConfirmed}
               content="Do you want to revoke access to the linked GSC account?"
            />
         </ModalBox>

         <ModalBox title="" open={revokeGA} onClose={() => { setRevokeGA(false) }}>
            <ConfirmDialog
               title="Revoke GA Access"
               cancelTitle="Cancel"
               confirmTitle="Revoke"
               modalCancel={() => { setRevokeGA(false) }}
               modalConfirm={handleGaRevoke}
               content="Do you want to revoke access to the linked GA account?"
            />
         </ModalBox>

         <section className="layout addProject">
            <div>
               <Header
                  rightside="d-none"
                  title="Add Project"
                  subTitle="Enter your project details in all the required fields below"
                  class=""
                  backlink="/projects"
               />

               <div>
                  <div className="m-b70">
                     <Grid container spacing={3} className="">
                        <Grid item xs={12} md={5} lg={3}>

                           <div className="m-b20" ref={wsurlRef}>
                              <Input label={"Website URL"} span={" *"} spanclassname={"redClr"} placeholder="https://www.tracker.example" value={wsurl} onblur={target_keywords_scrap} onchange={(e) => { setWsurl(e.target.value); setWsurlerrmsg("") }} errmsg={wsurlerrmsg} error={wsurlerrmsg.length > 0} />
                           </div>

                           <div className=" m-b20" ref={regionRef}>
                              <InputLabel shrink>
                                 Region <span className="redClr">*</span>
                              </InputLabel>
                              {/* Error goes through the control's own errmsg prop so it
                                  carries aria-invalid and aria-describedby; it clears
                                  itself the moment a region is picked. */}
                              <KNRSelectRegion rgName="aprgrndrName text-truncate" className="rgaddKwd" placeholder={"Region"} menuOpen={menuOpen} fullList={rgoptions} menulist={fltrregion} value={region !== "" ? "" + isocode + " " + region + " (" + countryname + ")" : countryname} onchange={rgselectlstChange} regionUpdate={regionListdataUpdate} rgcode={isocode} rgname={region} rgcnt={countryname} errmsg={rgnerrmsg} error={rgnerrmsg.length > 0 && region.length === 0} />
                           </div>

                           <div className=" m-b20" ref={langRef}>
                              <InputLabel shrink>
                                 Language <span className="redClr">*</span>
                              </InputLabel>

                              <SelectLang placeholder={"Select the language"} value={lang} menulist={langoptions} onchange={selectlstChange} errmsg={langerrmsg} error={langerrmsg.length > 0} />
                           </div>

                           <div className="m-b20" ref={pnameRef}>
                              <Input label={"Project name"} span={" *"} spanclassname={"redClr"} placeholder="SearchMirror" value={pname} onchange={projectNameChgfun} errmsg={pnmerrmsg} error={pnmerrmsg.length > 0} />
                           </div>

                           <div className="platformSelect">
                              <InputLabel shrink>
                                 Platform <span className="redClr">*</span>
                              </InputLabel>
                              <div
                                 style={{
                                    display: "grid",
                                    gridTemplateColumns: "85px 85px",
                                    gap: "15px",
                                 }}
                              >
                                 <label className="labl">
                                    <input type="radio" name="radioname" value="desktop" onClick={(e) => { setPlatform(e.target.value) }} defaultChecked />

                                    <div>
                                       <div className="icon">
                                          <DesktopIcon />
                                       </div>
                                       Desktop
                                    </div>
                                 </label>

                                 <label className="labl">
                                    <input type="radio" name="radioname" value="mobile" onClick={(e) => { setPlatform(e.target.value) }} />

                                    <div>
                                       <div className="icon">
                                          <MobileIcon />
                                       </div>
                                       Mobile
                                    </div>
                                 </label>
                              </div>
                           </div>

                           {/* Under Platform: one decision about what is asked of
                               Google. Unlike Platform it is per project. */}
                           <div className="depthSelect">
                              <InputLabel shrink>
                                 {/* No required mark -- it never blocks the submit. */}
                                 SERP extraction depth
                              </InputLabel>
                              <SerpDepthChoice
                                 value={serpAdvanced}
                                 onChange={setSerpAdvanced}
                                 name="serpdepth-addproject"
                                 note={
                                    serpAdvanced === DEPTH_ADVANCED
                                       ? "Applies to every keyword in this project. It is saved right after the project is created, and the first rank check is queued at the same moment — so that first check may still run at Lite."
                                       : "Applies to every keyword in this project, and can be changed later on the DataBlue API Key tab."
                                 }
                              />
                           </div>
                        </Grid>

                        <Grid item xs={12} md={8} lg={5}>
                           <div className="keyword" ref={keywordRef}>
                              <div className="parent">
                                 <div>
                                    <h2 className="smallTitle m-b5">
                                       Keywords <span className="redClr">*</span>
                                    </h2>
                                    <SmallText class="mb-0">
                                       {kwUnlimited ? "Add as many keywords as you like" : `You can add up to ${remainkeyaddcount} keywords`}
                                    </SmallText>
                                 </div>

                                 <CsvUpload keywordlist={keywordlist} kwupdatefun={(kw) => setKeywordlist(kw)} limit={remainkeyaddcount} />
                              </div>


                              <div className={"box" + (kwerrmsg && keywordlist.length === 0 ? " boxError" : "")}>
                                 <div
                                    style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}
                                 >
                                    <div className="w-100">
                                       <KeywordInput selectedtags={keywordlist} tagupdatefun={(tag) => setKeywordlist(tag)} limit={remainkeyaddcount} invalid={kwerrmsg.length > 0 && keywordlist.length === 0} errorid="addproject-keywords-error" />
                                    </div>
                                    {keywordlist.map((tag, index) => (
                                       <div className="tag new" key={index}>
                                          {tag}
                                          <span className="close" onClick={() => keywordDelete(index)}>
                                             <CloseIcon color="var(--surface)" />
                                          </span>
                                       </div>
                                    ))}
                                 </div>
                              </div>

                              {/* Clears itself as soon as a keyword exists. */}
                              {kwerrmsg && keywordlist.length === 0 ?
                                 <div className="fieldError m-b5" id="addproject-keywords-error">{kwerrmsg}</div>
                                 : null}

                              <div className="d-flex justify-content-between align-items-center">
                                 {loadKeywords === 0 ?
                                    <div className="d-flex m-l0">
                                       <CircularProgress size={14} className="mt-1" />
                                       <Para class="m-l5 m-b5 f12x f-semi"> Looking for top ranked keywords </Para>
                                    </div>
                                    : loadKeywords === 1 ?
                                       <Para class="m-l0 m-b5 f12x cursorP pClr f-semi" onclick={() => doAction("clear")} > Clear Keywords </Para>
                                       : loadKeywords === 2 ?
                                          <Para class="m-l0 m-b5 f12x cursorP pClr f-semi" onclick={() => doAction("reload")} > Show suggestions </Para>
                                          :
                                          <div> </div>
                                 }

                                 {kwUnlimited ? null : (
                                 <SmallText class="d-flex justify-content-end m-b5 f-semi">
                                    Remaining:{" "}
                                    <span className="txtClr m-l5">{remainkeyaddcount - keywordlist.length} keywords</span>
                                 </SmallText>
                                 )}
                              </div>

                           </div>
                        </Grid>
                        <Grid item xs={12} md={5} lg={4}>
                           <div className="addtag m-b10">
                              <div className="d-flex align-items-center justify-content-between p-b5">
                                 <div>
                                    <h2 className="smallTitle m-b5">Add Tags
                                       <span className="m-l5">
                                          <AppTooltip place="bottom-start" title={Improved} />
                                       </span>
                                    </h2>
                                    <SmallText class="mb-0">Enter multiple tags </SmallText>
                                 </div>
                                 <div>
                                    <AntSwitch
                                       checked={tagopt}
                                       onChange={(e) => { setTagopt(e.target.checked) }}
                                       inputProps={{ "aria-label": "ant design" }}
                                    />
                                 </div>
                              </div>
                              {tagopt ? <TagsInput selectedtags={selectedtags} tagupdatefun={(tag) => setSelectedtags(tag)} othertg={[]} othertagupdatefun={emptyfun} othertags={[]} /> : null}
                           </div>
                           <div className="my-3 border-t border-line" />
                           <div className="addtag m-b10">
                              <div className="d-flex align-items-center justify-content-between p-b5">
                                 <div>
                                    <h2 className="smallTitle m-b5">Add Branded Keywords
                                       <span className="m-l5">
                                          <AppTooltip place="bottom-start" title={BrandKeyword} />
                                       </span>
                                    </h2>
                                    <SmallText class="mb-0">Enter Branded Keywords  Ex: SearchMirror Blog</SmallText>
                                 </div>
                                 <div>
                                    <AntSwitch
                                       checked={brandKWSwitch}
                                       onChange={(e) => { setBrandKWSwitch(e.target.checked) }}
                                       inputProps={{ "aria-label": "ant design" }}
                                    />
                                 </div>
                              </div>
                              {brandKWSwitch ? <BrandKeywordInput selectedtags={brandOpts} tagupdatefun={(tag) => setBrandOpts(tag)} othertg={[]} othertagupdatefun={emptyfun} othertags={[]} /> : null}
                           </div>
                           <div className="my-3 border-t border-line" />
                           <div className="m-b20" ref={trackDayRef}>
                              <h2 className="smallTitle m-b5">Tracking Schedule <span className="redClr">*</span>
                                 <span className="m-l5">
                                    <AppTooltip place="bottom-start" title={TrackingInfo} />
                                 </span>
                              </h2>
                              <div><SelectMenu value={trackDay} menulist={weekDays} placeholder="Select" onchange={handleTrackDay} errmsg={trackDayErr} error={trackDayErr.length > 0} /></div>
                           </div>
                           {/* "Choose Your Platform" offered E-commerce / Non
                               E-commerce -- a site TYPE, on a form where
                               "Platform *" already means Desktop or Mobile. Two
                               fields, one word, different questions. It is now
                               labelled for what it asks.

                               It and the two integration blocks below only feed
                               the Search Console and Analytics connections, and
                               those are parked until the instance has a Google
                               OAuth client. With no client id GSC_connection and
                               GA_connection render nothing, so the page showed
                               two headings with an info icon and no control
                               under either, and a dropdown whose answer went
                               nowhere. Nothing here appears unless a client id
                               makes it real. */}
                           {!googleConfigured ? (
                              /* Hidden entirely before, so nobody learned it
                                 was coming. Shown and inert instead -- the same
                                 treatment Project Settings gives it. */
                              <ComingSoon title="Google Search Console and Analytics">
                                 Connect your Search Console and Analytics data to see clicks and
                                 impressions beside your rankings. Not available yet — it needs a
                                 server-side sign-in flow, which is being built.
                              </ComingSoon>
                           ) : null}
                           {googleConfigured ? <>
                           <div className="m-b20">
                              <h2 className="smallTitle m-b5">Site type
                                 <span className="m-l5">
                                    <AppTooltip place="bottom-start" title={ChoosePlatInfo} />
                                 </span>
                              </h2>
                              <div><SelectMenu value={dmPlatform} menulist={['Non E-commerce', 'E-commerce']} placeholder="Select" onchange={handlePlatform} errmsg={dmPlatformErr} error={dmPlatformErr.length > 0} /></div>
                           </div>
                           <div>
                              <div className="d-flex justify-content-between gap-2">
                                 <div>
                                    <h2 className="smallTitle m-b5">GSC Integration
                                       <span className="m-l5">
                                          <AppTooltip place="bottom-start" title={GSCInfo} />
                                       </span>
                                    </h2>
                                    <SafeGoogleOAuthProvider clientId={global.gscClientId}>
                                       <GSC_connection platform={dmPlatform} setDmPlatformErr={setDmPlatformErr} gscToken={gscToken} setGSCRevokeModal={setGSCRevokeModal} setGSCToken={setGSCToken} setGSCProperties={setGSCProperties} setGSCPrtyMdlVsble={setGSCPrtyMdlVsble} gscProperties={gscProperties} gscProperty={gscProperty} />
                                    </SafeGoogleOAuthProvider>
                                 </div>
                                 <div ref={gaPropertyRef}>
                                    <h2 className="smallTitle m-b5">GA Integration
                                       <span className="m-l5">
                                          <AppTooltip place="bottom-start" title={GAInfo} />
                                       </span>
                                    </h2>
                                    <SafeGoogleOAuthProvider clientId={global.gaClientId}>
                                       <GA_connection platform={dmPlatform} setDmPlatformErr={setDmPlatformErr} property={property} setRevokeGA={setRevokeGA} gaToken={gaToken} setGARfrshTkn={setGARfrshTkn} setData={setData} setEdtPrjtMdlVsble={setEdtPrjtMdlVsble} />
                                    </SafeGoogleOAuthProvider>
                                 </div>
                              </div>
                              {/* <h2 className="smallTitle m-b5">GSC Integration
                                 <span className="m-l5">
                                    <AppTooltip place="bottom-start" title={GSCInfo} />
                                 </span>
                              </h2>
                              {
                                 !gscToken ?
                                    <div>
                                       <Box className="keyWrd" sx={{ minWidth: "170px", maxWidth: "170px", flex: "0 0 auto" }}>
                                          <AppButton value="Connect GSC" class="wd-btn-add p-l0 p-r0" onclick={handleGoogleSignin}>
                                          </AppButton>
                                       </div>
                                    </div> :
                                    <div>
                                       <Box className="keyWrd" sx={{ minWidth: "170px", maxWidth: "170px", flex: "0 0 auto" }}>
                                          <AppButton value="Revoke GSC" class="wd-btn-add p-l0 p-r0" onclick={() => setGSCRevokeModal(true)}>
                                          </AppButton>
                                       </div>
                                    </div>
                              } */}
                           </div>
                           </> : null}
                        </Grid>
                     </Grid>
                  </div>

                  <div className="footer">
                     <div>
                        <Link to={"/projects"}>
                           <AppButton value="Cancel" color="white" class="borderBtn" noIcon="d-none"></AppButton>
                        </Link>
                     </div>
                     <div>
                        <AppButton noIcon="d-none" class="wd-btn-add" value="Add Project" color="primary" type="submit" onclick={addKeyword} loading={btnloading} disabled={btnloading} />
                     </div>
                  </div>
               </div>
            </div>
         </section >
      </>
   );
}

export default AddProject;
