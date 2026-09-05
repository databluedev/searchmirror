import React, { useState, useEffect } from "react";
import { Link, useHistory, useParams, useLocation } from "react-router-dom";
import "./style.scss";

import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';

// Header
import { Para, Title, AppIconButton, Tsk } from "../commonComponents/parts";
import { BacklinkIcon, RefreshIcon } from "../commonComponents/icons";

//Tab package
import Tab from '@mui/material/Tab';
import { TabContext , TabList, TabPanel } from '@mui/lab';

import KWOverview from "./components/overview_tab";
import KWCompetitors from "./components/competitors_tab";
import KwNotesPopup from "./components/kw_notes_popup";
import KeywordHistoryChart from "../serpRank/components/kw_history_graph";

import KWDelete from "../serpRank/components/keyword_delete";

import RefreshBar from "../commonComponents/refresh_bar";
import { Tooltip, CircularProgress } from "@mui/material";

import NotesTab from "./components/kw_notes_table";
import { allowsTeamAction } from "../../utils/team_permissions";

function KeywordOverview(props) {

   const history = useHistory();
   const location = useLocation();
   let { kwid } = useParams();
   const [backlink, setBacklink] = useState("/keywords");
   const canManageTags = allowsTeamAction(props.fullbasedata, "Keyword", "Manage Tag");
   const canRefreshKeywords = allowsTeamAction(props.fullbasedata, "Keyword", "Manual Refresh");
   const canDeleteKeywords = allowsTeamAction(props.fullbasedata, "Keyword", "Delete Keywords");
   const canManageNotes = allowsTeamAction(props.fullbasedata, "Keyword", "Manage Notes");
   // /typoerrorfix is mapped to ("Keyword", "Add Keywords") server-side -- a
   // spelling fix can create a second keyword row. Gate on what it checks.
   const canFixSpelling = allowsTeamAction(props.fullbasedata, "Keyword", "Add Keywords");
   // Same right, and for the same reason: /kwconfigsave changes what the next
   // check measures and what it costs. There is no separate "edit keyword"
   // action in the role editor, so this gate and the server's are one fact.
   const canEditConfig = allowsTeamAction(props.fullbasedata, "Keyword", "Add Keywords");

   
   const [keyid, setKeyid] = useState(null);
   const [basedata, setBasedata] = useState({ 'kw_c':0 });
   const [kwdata, setKwdata] = useState({});
   const [notedata, setNotedata] = useState({
      dataRows: [],
      noteDate: [],
      totalRows: -1
   });
   const [adlist, setAdlist] = useState([]);
   const [comp, setComp] = useState({});

   const [adsLoading, setAdsLoading] = useState(true);
   const [comptrLoading, setComptrLoading] = useState(true);

   const [tabview, setTabview] = React.useState('1');
   const [refresh_on, setRefresh_on] = useState(null);
   const onRefreshTriggerFunc = React.useRef(null)
   const onRefreshCheckFunc = React.useRef(null)


   const cookies = new Cookies();
   const usertoken = cookies.get('session_token')
   const userid = cookies.get('session_userid')
   const grpid = cookies.get('activegrp')

   useEffect(() => {
      if(typeof(kwid) !== "undefined") {
         setKeyid(kwid - global.keywordsecret)
      } else {
         toast.error('Something went wrong!')
         history.push('/')
      }

      if(location.state && location.state.back !== undefined) {
         setBacklink(location.state.back)
         keyworddata(kwid - global.keywordsecret)
      } else if(location.state && location.state.kwdata !== undefined && location.state.basedata !== undefined) {
         setKwdata(location.state.kwdata)
         setBasedata(location.state.basedata)

         var apitype = location.state.kwdata.srs ? "half" : "full"
         keyworddata(kwid - global.keywordsecret, apitype, location.state.kwdata)
      } else {
         keyworddata(kwid - global.keywordsecret)
      }

      setTimeout(() => {
         global.PageTopLoader.current.complete();
      }, 1000);
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [location]);


   const keyworddata = (kid=keyid, apitype="full", olddata=kwdata) => {

      if(userid && grpid && kid !== 0) { 
         var data = {
            'userid': userid,
            'grpid': grpid,
            'kwid': kid,
            'type': apitype,
         };
         axios.post(global.apiurl + '/keyauth', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if (res.status !== "true") {
               toast.error(res.message)
               history.push('/')
            } else {
               if(res.data) {
                  setKwdata({...olddata, ...res.data});
               }

               if(res.hdata) {
                  setBasedata({...basedata, ...res.hdata});
               }

               setRefresh_on(res.mrK === "onk" ? true : false);

               if(res.mrK && (res.mrK === "onk" || res.mrK === "onv")){
                  onRefreshCheckFunc.current(userid, grpid, res.mrK)
               }
            }
         }).catch((error) => {
            history.push("/")
         });
      }
   }

   const handleChange = (event, newValue) => {
      setTabview(newValue);
      if(newValue === "3" && (adsLoading || comptrLoading)) {
         alladsget(keyid);
         allcompsget('tp')
      } else if(newValue === "4") {
         fetchNotes();
      }
   };

   const getKeyId = () => {
      var keyidd = 0
      if (keyid === null) {
         if(typeof(kwid) !== "undefined") {
            keyidd = kwid - global.keywordsecret   
         }
      } else {
         keyidd = keyid
      }

      return keyidd 
   }

   const tabledataUpdate = (data, flag="") => {
      if (flag !== "update") { 
         setKwdata(data[0])
      }

      if (tabview === "4") { 
         fetchNotes()
      } 
      return true
   }

   const onRefresh = (count) => {
      console.log("onRefresh "+ count); 
      setKwdata({...kwdata, 'nt':count}) 
   }

   const fetchNotes = (limit=10, page=1) => {
      setNotedata({
         ...notedata,
         dataRows: [], 
         noteDate: [],
         totalRows: -1
      })
            
      try {
         const cookies = new Cookies();
         const userToken = cookies.get('session_token')
         const userId = cookies.get('session_userid')
         const grpId = cookies.get('activegrp')
         const keyId = getKeyId()

         if(userId && grpId && keyId) {
            var data = {
               'userid': userId,
               'grpid': grpId,
               'kid': keyId,
               'lmt': limit,
               'prt': page  
            };
            
            axios.post(global.apiurl + '/dm90ZlldhbGx19fbmXM', data, {
               headers: {'Authorization': 'Token '+ userToken }
            }).then(response => {
               return response.data;
            }).then(res => {
               if (res.st === 1) {
                  if (res.dt.length) {
                     setKwdata({...kwdata, 'nt':res.ct})
                     setNotedata({
                        ...notedata,
                        dataRows: res.dt,
                        noteDate: res.nl,
                        totalRows: res.ct
                     })
                  
                  } else {
                     setKwdata({...kwdata, 'nt':res.ct}) 
                     setNotedata({
                        ...notedata,
                        dataRows: null,
                        noteDate: res.nl,
                        totalRows: res.ct
                     })
                  
                  } 
               } else {
                  toast.error(res.message)
                  // window.location.reload(); 
               }
            }).catch((error) => {
               toast.error("Request failed, Try again later")
               // window.location.reload(); 
            }); 
         }
      } catch (error) {
         toast.error("Try again later")
         // window.location.reload(); 
      }
   }

   const alladsget = () => {

      if(userid && grpid && keyid) {    
         var data = {
            'userid': userid,
            'grpid': grpid,
            'kwid': keyid,
         };
         axios.post(global.apiurl + '/kwads', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {

            if(res.status === "true") {
               setAdlist(res.lst);
               setAdsLoading(false);
            } else {
               toast.error(res.message)
            }
         }).catch((error) => {
            // history.push("/")
         });
      }
   }

   const allcompsget = (type="tp") => {
      setComptrLoading(true);
       
      if(userid && grpid && keyid) {    

         var data = {
            'userid': userid,
            'grpid': grpid,
            'kwid': keyid,
            'type': type,
         };
         axios.post(global.apiurl + '/kwcomps', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {    
            if(res.status === "true") {
               setComp(res.cmp);
               setComptrLoading(false);
            } else {
               toast.error(res.message);
               setComptrLoading(false);
            }
         }).catch((error) => {
            // history.push("/")
         });
      }
   }
  

   const tagUpdate = (data) =>{
      setKwdata({...kwdata, 'tg':data})
   }

   const backpage = () => {
      if(basedata.kw_c === 1){
         history.push("/")
      }else{
         history.push("/keywords")
      }
   }

   const refreshUpdate = (refreshSwt, status="init") => {
      setRefresh_on(refreshSwt);
      if(status === "success"){
         keyworddata();
         setAdsLoading(true);
         setTabview('1');
      }
   }


   return (
      <>
         <section className={"layout kw-overview"+(refresh_on ? " refreshing-in": "")}>
            <div>
               <header>
                  <div className="d-flex justify-content-between flex-wrap gap-3">
                     <div className="d-flex align-items-center gap-3">
                        <span>
                          <Link to={backlink}>
                              <AppIconButton aria-label="Back to keywords" class="sp-backbtn" Icon={<BacklinkIcon />} />
                          </Link>
                        </span>
                        {/* The keyword is the subject of this page; the project
                            is the context it sits in. They used to be the other
                            way round -- the 26px page title named the project,
                            which is the same on every keyword in it, and the
                            keyword you actually navigated to was the 13px
                            sub-line. The keyword was also being re-cased on the
                            way out -- first letter up, the rest down. A keyword
                            is the literal string sent to Google, so it is shown
                            exactly as it was entered. */}
                        <div>
                           <Title class="wd-title lh22x m-b10 d-flex align-items-center">
                              {kwdata.KW ? kwdata.KW : <Tsk width={200} height={22} />}
                           </Title>
                           <Para class="wd-subTitle d-flex align-items-center lh14x m-b0">
                              {basedata.NM ? basedata.NM : <Tsk width={100} height={14} />}
                           </Para>
                        </div>
                     </div>

                     <div className="d-flex align-items-center twoButton flex-[0_0_auto] gap-[0.6rem]">
                        {canRefreshKeywords ? <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"Refresh this keyword"} >
                           <div>
                              <AppIconButton
                                aria-label="Refresh this keyword"
                                class="boxIcon"
                                onclick={(keyid && refresh_on === false) ? () => onRefreshTriggerFunc.current()  : null}
                                Icon={ (keyid && refresh_on === false) ? <RefreshIcon height="18" width="18" color="currentColor" /> : refresh_on ? <CircularProgress size={20} /> : <Tsk width={30} />  }
                              />
                           </div>
                        </Tooltip> : null}
                        
                        {canDeleteKeywords ? <KWDelete kwtype={"kwoverview"} selectedRowIds={[keyid]} updatefullpage={backpage} basedata={basedata} /> : null}

                        {canManageNotes ? <div>
                          <KwNotesPopup kwdata={kwdata} keyid={keyid} tabledataUpdate={tabledataUpdate} />
                        </div> : null}
                     </div>
                  </div>
               </header>

               <div className="keywordDetail">
                  <div className="w-full">
                     <TabContext value={tabview}>
                       {/* Pill tabs come from the MUI theme -- selected fills
                           --accent-weak, the indicator underline is off. The
                           strip needs no border of its own; the page header
                           already closed with a hairline right above it. */}
                       <div className="kwTabStrip">
                           <TabList onChange={handleChange} variant="scrollable" scrollButtons={false} aria-label="Keyword detail sections">
                              <Tab label="Overview" value="1" />
                              <Tab label="Rank History" value="2" />
                              {/* Not "Competitors": the side rail carries a
                                  destination by that exact name on this same
                                  screen, so two controls one metre apart
                                  answered to one word and only one of them
                                  stayed on the keyword. */}
                              <Tab label="SERP Competitors" value="3" />
                              <Tab label={"Notes"+(kwdata && kwdata.nt ? " ("+kwdata.nt+")" : "")}  value="4" />
                           </TabList>
                       </div>
                       <TabPanel value="1"><KWOverview kwdata={kwdata} tagUpdate={tagUpdate} keyid={keyid} canManageTags={canManageTags} canFixSpelling={canFixSpelling} canEditConfig={canEditConfig} reloadKeyword={() => keyworddata(keyid)} /></TabPanel>
                       <TabPanel value="2"><KeywordHistoryChart kwdata={kwdata} ntscnt={kwdata.nt} className="m-t30" /></TabPanel>
                       <TabPanel value="3"><KWCompetitors adlist={adlist} adsLoading={adsLoading} comp={comp} comptrLoading={comptrLoading} allcompsget={allcompsget} /></TabPanel>
                       <TabPanel value="4"><NotesTab kwdata={kwdata} keyid={keyid} notedata={notedata} onRefresh={onRefresh} tabledataUpdate={tabledataUpdate} canManageNotes={canManageNotes} /></TabPanel>
                     </TabContext>
                  </div>
               </div>

            </div>
         </section>
         <RefreshBar onRefreshTriggerFunc={onRefreshTriggerFunc} onRefreshCheckFunc={onRefreshCheckFunc} kwids={[keyid]} refresh_on={refresh_on} refreshUpdate={refreshUpdate} pageurl={kwdata.KW ? kwdata.KW.split(' ').join('_').toLowerCase() : ""} />
      </>
   );
}

export default KeywordOverview; 
