import React, { useState, useEffect } from "react";
import { useHistory } from "react-router-dom";
import { ModalBox, ProjectDelete, ProjectEdit } from "../commonComponents/Modals";
import { MenuItem, Tooltip, Zoom, Pagination, Stack } from "@mui/material";
import { FillArrow, GoLinkIcon } from "../commonComponents/icons";
import "./style.scss";
import { Para, Text, Title, AppTooltip, AppButton, Tsk } from "../commonComponents/parts";
import { DataEmptyIcon, AddProjectIcon } from "../commonComponents/icons";
import ClickAway from "../commonComponents/click_away";
import ProjectMetric from "./components/project_status";
import TrendSpark from "./components/trend_spark";
import ScoreRing from "./components/score_ring";
import DashHeader from "./components/dashboard_header";
import ProjectRefreshStatus from "./components/project_refresh_status";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { fstLtrCapitalfun, url_to_host } from "../common_fun";
import { toast } from 'react-toastify';
import ProjectInfoModalComponent from "./components/ProjectInfoModalComponent";
import SiteMark from "../commonComponents/site_mark";

const projectPageLimit = 20

/* Some projects store their domain without a scheme ("semrush.com"), and a bare
   host in href= is a relative URL -- the link navigated to /semrush.com inside
   the portal instead of leaving it. */
const externalHref = (domain) =>
   !domain ? undefined : /^https?:\/\//i.test(domain) ? domain : "https://" + domain;

/* Has this project ever been scored?

   ss is 0 both for a project whose rankings are genuinely bottomed out and for
   one that has never been measured, so it cannot answer this on its own. bss is
   the discriminator: serp/serializers.py:163 returns max(score_history), or the
   -1 sentinel when the history is empty -- and an empty history is exactly
   "never scored". The tooltip below reads "not available" off the same test.

   ss is checked as well as a belt-and-braces guard: a project showing a real
   score must never be blanked because the discriminator alone said no.

   All three of ss, yss and bss are now recomputed from the keyword rank arrays
   by the same shared.scoring call /erocs_wdt makes, so they cannot disagree
   with the dashboard. They used to read the stored Groups.score_meter and
   top_score snapshots, which is what made the same project read 34 here and 37
   there, and left bss stale enough to blank a live score of 100.

   A score is a measurement; "yesterday" and a delta are claims about TWO of
   them. On a project's first measured day there is only one: yss falls back to
   ss (serializers.py:152) and bss equals it, so every naive test passes and the
   row would assert a yesterday that never happened -- to the newest user, on
   their newest project, which is the worst audience for a confident wrong
   number. t_c is the count the score is built from, so it is the honest gate,
   and it is the same field name /erocs_wdt has always returned as dt.t_c. */
const hasScore = (prjt) => prjt.bss >= 0 || Number(prjt.ss) > 0;

/* Is there a previous measurement to compare against? Absent t_c (an older
   backend) this reads false and the comparison is simply not drawn, which is
   the safe direction: silence is not a wrong claim. */
const hasPrevious = (prjt) => Number(prjt.t_c) > 1;

const Decline = (
   <div>
      <Text class="fB m-b5">What is Declined?</Text>
      <Para class="m-0">
         Number of keywords with a setback in today's rankings.
         {/* Number of keywords with setback in rankings. */}
      </Para>
   </div>
);

//
const Improve = (
   <div>
      <Text class="fB m-b5">What is Improved?</Text>
      <Para class="m-0">
         Number of keywords that improved in today's rankings.
         {/* The number of keywords whose ranking position has increased.
       Tracker score is an accurate indicator of your site's overall organic performance . */}
      </Para>
   </div>
)


const Firstpos = (
   <div>
      <Text class="fB m-b5">What is in the first position?</Text>
      <Para class="m-0">
         Number of keywords ranking in 1st position in Google's SERP today.
         {/* Number of keywords ranking on 1st position in Google's SERP. */}
      </Para>
   </div>
);

/* One metric, one name. This number, the panel on /dashboard and the figure
   over the Keywords table are the same measurement, and calling it three
   things ("SearchMirror score", "Search Visibility Score", "Score") hid the
   fact that they did not agree. The name says what is measured, so it stays
   true of a fork and of a rename. */
const SScore = (
   <div>
      <Text class="fB m-b5">What is the Search Visibility Score?</Text>
      <Para class="m-0">
         Each tracked keyword contributes according to its current Google position. First position has the most weight; an unranked keyword contributes zero. The result is normalized to a score out of 100.
      </Para>
   </div>
);

const Trend = (
   <div>
      <Text class="fB m-b5">What is Trend?</Text>
      <Para class="m-0">
         Improved keywords minus declined keywords, one mark per day for the last 7 days.
         A bar above the line is a day your rankings gained overall; below it, a day they lost.
         A tick on the line is a day nothing moved.
      </Para>
   </div>
);

function Dashboard(props) {
   // const [completed, setCompleted] = useState(0);
   // const theme = useTheme();

   const [activeProjectId, setActiveProjectId] = React.useState(0);
   const [activeProjectName, setActiveProjectName] = React.useState(0);
   const [delPrjtMdlVsble, setDelPrjtMdlVsble] = React.useState(false);
   const [editPrjtMdlVsble, setEdtPrjtMdlVsble] = React.useState(false);
   const [effectupdate, setEffectupdate] = React.useState(false);

   // info start
   const [projectInfo, setProjectInfo] = useState({
      domainStatus: "",
      register: "",
      domainCreated: "",
      domainUpdate: "",
      domainExpiry: "",
      organization: "",
      state: "",
      country: "",
      domainIcon: ""
   })
   const [viewPrjtModal, setViewPrjtModal] = React.useState(false);
   //info end

   const deleteProjectMdlOpen = (pid) => {
      setDelPrjtMdlVsble(true);
      setActiveProjectId(pid);
      const cookies = new Cookies();
      cookies.set('activegrp', pid, { path: '/', maxAge: global.cookiesexpire });
   };

   const deleteProjectMdlClose = () => {
      setDelPrjtMdlVsble(false);
      // if (data === "update"){
      //     props.baseauth("update")
      //     setEffectupdate(!effectupdate)
      // }
   };

   const editProjectMdlOpen = (pid, pname) => {
      setEdtPrjtMdlVsble(true);
      setActiveProjectId(pid);
      setActiveProjectName(pname);
      const cookies = new Cookies();
      cookies.set('activegrp', pid, { path: '/', maxAge: global.cookiesexpire });
   };

   const editProjectMdlClose = () => {
      setEdtPrjtMdlVsble(false);
      // if (data === "update"){
      //     props.baseauth("update")
      //     setEffectupdate(!effectupdate)
      // }
   };

   //  info start
   const viewProjectMdlOpen = (pinfo) => {
      setProjectInfo({
         ...projectInfo,
         domainStatus: pinfo.dn_s === "ON" ? 'Active' : 'InActive',
         register: pinfo.dn_d.RG === "" || pinfo.dn_d.RG === undefined || pinfo.dn_d.RG === null ? 'NA' : pinfo.dn_d.RG,
         domainCreated: pinfo.dn_d.CD === "" || pinfo.dn_d.CD === undefined || pinfo.dn_d.CD === null ? 'NA' : pinfo.dn_d.CD,
         domainUpdate: pinfo.dn_d.UD === "" || pinfo.dn_d.UD === undefined || pinfo.dn_d.UD === null ? 'NA' : pinfo.dn_d.UD,
         domainExpiry: pinfo.dn_d.ED === "" || pinfo.dn_d.ED === undefined || pinfo.dn_d.ED === null ? 'NA' : pinfo.dn_d.ED,
         organization: pinfo.dn_d.OG === "" || pinfo.dn_d.OG === undefined || pinfo.dn_d.OG === null ? 'NA' : pinfo.dn_d.OG,
         state: pinfo.dn_d.ST === "" || pinfo.dn_d.ST === undefined || pinfo.dn_d.ST === null ? 'NA' : pinfo.dn_d.ST,
         country: pinfo.dn_d.CO === "" || pinfo.dn_d.CO === undefined || pinfo.dn_d.CO === null ? 'NA' : pinfo.dn_d.CO,
         domainUrl: pinfo.D_N,
         domainName: pinfo.G_N === "" ? 'NA' : pinfo.G_N,
      });
      setViewPrjtModal(true);
   }
   const closeviewProjectMdlOpen = () => {
      setViewPrjtModal(false);
   };


   //info end
   const updatefullpage = () => {
      props.baseauth("update")
      setEffectupdate(!effectupdate)
   }

   const history = useHistory();
   const [project, setProject] = useState({ 'page': 1, 'filterdata': [], 'displaydata': [], 'fulldata': [], 'apiloader': true, 'engineMode': 0 });
   // const [homedata, setHomedata] = useState([]);
   // const [apiloader, setApiloader] = useState(true);
   // const [engineMode, setEngineMode] = React.useState(0);


   useEffect(() => {
      // The request outlives a route change unless it is torn down here; its
      // callback updates state on this page.
      //
      // This used to ALSO drive the shell's top progress line on a fixed 2s
      // timer while the row skeleton below ran -- two loading idioms at once on
      // one screen, and a timer that had nothing to do with when the request
      // actually finished. The skeleton is the shape of the list that lands, so
      // it is the one that stays.
      const controller = new AbortController();
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      if (!usertoken || !userid) {
         history.push("/login");
      }

      var data = {
         'userid': userid,
      };
      axios.post(global.apiurl + '/homeauth', data, {
         headers: { 'Authorization': 'Token ' + usertoken },
         signal: controller.signal
      }).then(response => {
         return response.data;
      }).then(res => {
         if (res.status !== "true") {
            toast.error(res.message)
         } else {
            setProject(olddata => ({ ...olddata, 'apiloader': false, 'engineMode': res.Eng, 'fulldata': res.data, 'filterdata': res.data, 'displaydata': res.data.slice(0, projectPageLimit) }))
            // setEngineMode(res.Eng)
            // setHomedata(res.data)
            // setApiloader(false)
         }
      }).catch((error) => {
         // history.push("/")
      });

      return () => {
         controller.abort();
      };

      // SmoothScrollbar("#smoothscrollbar", );
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [effectupdate]);

   const addprojectlink = () => {
      if (props.fullbasedata && props.fullbasedata.ac_typ !== "team") {
         history.push("/addproject")
         return false;
      } else {
         toast.error('Please wait! Your dashboard is getting ready ...')
         return false;
      }
   }

   // Event Handling
   const routeProjectPage = (projectdata) => {
      const cookies = new Cookies();
      cookies.set('activegrp', projectdata.GY, { path: '/', maxAge: global.cookiesexpire });
      history.push('/dashboard')
   };

   const homeApi = () => {
      setEffectupdate(!effectupdate)
   }

   const dataUpdate = (data) => {
      setProject(olddata => ({ ...olddata, 'page': 1, 'filterdata': data, 'displaydata': data.slice(0, projectPageLimit) }))
   }

   const pageChange = (event, value) => {
      setProject(olddata => ({ ...olddata, 'page': value, 'displaydata': project.filterdata.slice((value * projectPageLimit) - projectPageLimit, value * projectPageLimit) }))
   };
   const keywordsPage = (projectdata) => {
      const cookies = new Cookies();
      cookies.set('activegrp', projectdata.GY, { path: '/', maxAge: global.cookiesexpire });
   };

   /* The whole row is the hit target for the keyword list, so the navigation
      the "View Keywords" link used to do now happens here. keywordsPage stays
      the one place the active project cookie is set. */
   const openKeywords = (projectdata) => {
      keywordsPage(projectdata);
      history.push("/keywords");
   };

   /* Score direction beside the ring: a signed number and an arrow, never
      colour alone. Same three-way comparison the card used, but "Raising" /
      "Dropping" only said which way -- the delta says which way and how far, in
      a third of the width. */
   const scoreDelta = (prjt) => {
      const delta = (Number(prjt.ss) || 0) - (Number(prjt.yss) || 0);
      if (delta > 0) {
         return (
            <span className="prjDelta rankUp">
               <span className="arrow green d-flex"><FillArrow /></span>
               {"+" + delta}
            </span>
         );
      }
      if (delta < 0) {
         return (
            <span className="prjDelta rankDown">
               <span className="arrow red d-flex"><FillArrow /></span>
               {delta}
            </span>
         );
      }
      return <span className="prjDelta rankFlat">0</span>;
   };
   const canManageProjects = props.fullbasedata.ac_typ !== "team";

   return (
      <>
         {/* info start */}
         <ProjectInfoModalComponent
            prjData={projectInfo}
            IsModalOpened={viewPrjtModal}
            onCloseModal={closeviewProjectMdlOpen}
         />
         {/* info end */}

         <section className="layout" onClick={props.handleClick} id="smoothscrollbar">
            <DashHeader fullbasedata={props.fullbasedata} canManageProjects={canManageProjects} addproject={addprojectlink} dataUpdate={dataUpdate} fulldata={project.fulldata} projectPageLimit={projectPageLimit} />

            <div className="px-2">

               {canManageProjects ? <ModalBox title="" onClose={deleteProjectMdlClose} open={delPrjtMdlVsble} >
                  <ProjectDelete pid={activeProjectId} modalClose={deleteProjectMdlClose} updatefullpage={updatefullpage} />
               </ModalBox> : null}

               {canManageProjects ? <ModalBox title="" onClose={editProjectMdlClose} open={editPrjtMdlVsble} >
                  <ProjectEdit pid={activeProjectId} pname={activeProjectName} modalClose={editProjectMdlClose} updatefullpage={updatefullpage} />
               </ModalBox> : null}


               {/* Project list.

                   Was a two-up grid of tall cards, then a list whose every row
                   repeated the same four uppercase column labels -- eighty of
                   them on a page of twenty projects, each one eating the width
                   its own number needed. The labels are constant down a column,
                   so they are stated once in a header that shares the rows'
                   grid, and a row now holds only what differs: the project, a
                   week of movement, three counters and its score.

                   The whole row is still the hit target for the keyword list it
                   leads to; the domain link, the info icons and the kebab all
                   stop the click from reaching it. */}
               {project.displaydata.length > 0 ?
                  <>
                     <div className="prjList">
                        <div className="prjListHead">
                           <span />
                           <span className="prjHeadCell">
                              <span className="prjHeadText">Project</span>
                           </span>
                           <div className="prjData">
                              <span className="prjHeadCell">
                                 <span className="prjHeadText">Trend</span>
                                 <span className="prjInfo"><AppTooltip place="bottom-end" title={Trend} /></span>
                              </span>
                              <span className="prjHeadCell prjHeadNum">
                                 <span className="prjHeadText">Improved</span>
                                 <span className="prjInfo"><AppTooltip place="bottom-end" title={Improve} /></span>
                              </span>
                              <span className="prjHeadCell prjHeadNum">
                                 <span className="prjHeadText">Declined</span>
                                 <span className="prjInfo"><AppTooltip place="bottom-end" title={Decline} /></span>
                              </span>
                              <span className="prjHeadCell prjHeadNum prjColFp">
                                 <span className="prjHeadText">First pos</span>
                                 <span className="prjInfo"><AppTooltip place="bottom-end" title={Firstpos} /></span>
                              </span>
                              <span className="prjHeadCell">
                                 <span className="prjHeadText">Visibility</span>
                                 <span className="prjInfo"><AppTooltip place="bottom-end" title={SScore} /></span>
                              </span>
                           </div>
                           <span />
                        </div>

                        {project.displaydata.map((prjt, idx) => {
                           /* The beam carries "this project is being crawled"
                              at row scale, legible from anywhere in the row
                              rather than only from its left edge. The favicon
                              slot used to swap the site mark for a spinner as
                              well, which said the same thing a second time in a
                              second idiom and hid the one piece of identity the
                              row leads with. */
                           const crawling = prjt.mrk === 1 && project.engineMode === 1;
                           const scored = hasScore(prjt);
                           const compared = scored && hasPrevious(prjt);
                           return (
                              <div
                                 key={idx}
                                 className={crawling ? "prjRow beamBorder" : "prjRow"}
                                 role="link"
                                 tabIndex={0}
                                 onClick={() => openKeywords(prjt)}
                                 onKeyDown={(e) => {
                                    if (e.key === "Enter" || e.key === " ") {
                                       e.preventDefault();
                                       openKeywords(prjt);
                                    }
                                 }}
                              >
                                 <div className="prjFavicon">
                                    <SiteMark domain={prjt.D_N} />
                                 </div>

                                 {/* Name loud, everything else about the project
                                     on one quiet line under it. The keyword count
                                     used to hold a column that was the first thing
                                     dropped as the viewport narrowed; as prose it
                                     survives every width. */}
                                 <div className="prjIdentity">
                                    <span className="prjName">{fstLtrCapitalfun(prjt.G_N)}</span>
                                    <span className="prjSub">
                                       <a
                                          href={externalHref(prjt.D_N)}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="prjDomain"
                                          onClick={(e) => e.stopPropagation()}
                                       >
                                          <span className="text-truncate">{url_to_host(prjt.D_N)}</span>
                                          <GoLinkIcon height={10} width={10} />
                                       </a>
                                       <span className="prjDot" aria-hidden="true">&middot;</span>
                                       <span className="prjSubItem">{prjt.kw_ln} {prjt.kw_ln === 1 ? "keyword" : "keywords"}</span>
                                       <span className="prjDot" aria-hidden="true">&middot;</span>
                                       <span className="prjSubItem">
                                          {prjt.rf_t ? "updated " + prjt.rf_t : <Tsk width={78} height={12} />}
                                       </span>
                                    </span>
                                 </div>

                                 <div className="prjData">
                                    <TrendSpark improved={prjt.ikw} declined={prjt.dkw} />
                                    <ProjectMetric title="Improved" kvalue={prjt.ikw} />
                                    <ProjectMetric title="Declined" kvalue={prjt.dkw} />
                                    <ProjectMetric title="First Position" label="First pos" kvalue={prjt.fpk} className="prjColFp" />

                                    <div className="prjScoreCell">
                                       <span className="prjSrOnly">Search Visibility Score</span>
                                       <Tooltip
                                          /* Three states, not two. "Measured once"
                                             is as wrong for a project that has
                                             never been measured as "yesterday" is
                                             for one measured once. */
                                          title={scored
                                             ? <>
                                                {compared
                                                   ? <>Yesterday, it was {prjt.yss} · </>
                                                   : <>Measured once so far · </>}
                                                best {prjt.bss >= 0 ? prjt.bss : "NA"}
                                             </>
                                             : <span className="newlightTxtClr fM">Not measured yet</span>}
                                          placement="top"
                                          TransitionComponent={Zoom}
                                          classes={{ tooltip: "Tltpsmall" }}
                                       >
                                          <span className="prjScore">
                                             <ScoreRing value={prjt.ss} known={scored} />
                                             {/* A delta is a claim about two
                                                 measurements. An unscored project
                                                 has none and a first-day one has
                                                 a single measurement, so neither
                                                 gets a number here. */}
                                             {scored && compared ? scoreDelta(prjt) : null}
                                          </span>
                                       </Tooltip>
                                    </div>
                                 </div>

                                 <div className="prjMenu" onClick={(e) => e.stopPropagation()}>
                                    <ClickAway>
                                       <MenuItem className="primaryHover" onClick={() => routeProjectPage(prjt)}>Overview</MenuItem>
                                       <MenuItem className="primaryHover" onClick={() => viewProjectMdlOpen(prjt)}>Info</MenuItem>
                                       {canManageProjects ? <MenuItem className="primaryHover" onClick={() => editProjectMdlOpen(prjt.GY, prjt.G_N)}>Rename</MenuItem> : null}
                                       {canManageProjects ? <MenuItem className="primaryHover" onClick={() => deleteProjectMdlOpen(prjt.GY)}>Delete</MenuItem> : null}
                                    </ClickAway>
                                 </div>
                              </div>
                           );
                        })}
                     </div>

                     {project.filterdata.length > projectPageLimit ?
                        <Stack className="d-flex m-t30 align-items-center justify-content-end" spacing={2}>
                           <Pagination count={project.filterdata.length % projectPageLimit === 0 ? project.filterdata.length / projectPageLimit : Math.floor(project.filterdata.length / projectPageLimit) + 1} variant="outlined" color="primary" page={project.page} onChange={pageChange} />
                        </Stack>
                        : null}
                  </>
                  : project.apiloader === false ?
                     /* docs/DESIGN.md, Empty state: micro-label, one sentence,
                        one primary action. The action was missing -- the screen
                        told someone with no projects that they had no projects
                        and left them to go and find the button in the header. */
                     <div className="prjEmpty">
                        <DataEmptyIcon />
                        <Title>No project found</Title>
                        <div>Looks like you haven’t added a project yet.</div>
                        {canManageProjects ? <div className="prjEmptyAction">
                           <AppButton
                              value="Add Project"
                              class="wd-btn-add p-l0 p-r0 shinySweep"
                              onclick={addprojectlink}
                              Icon={<AddProjectIcon />}
                           />
                        </div> : null}
                     </div>

                     :
                     <div className="prjList">
                        {(props.projectList || [1, 2, 3]).map((prjt, idx) => (
                           <div className="prjRow" key={idx}>
                              <Tsk width={32} height={32} />
                              <div className="prjIdentity">
                                 <Tsk width={"45%"} height={18} />
                                 <Tsk width={"70%"} height={13} />
                              </div>
                              <div className="prjData">
                                 <Tsk width={80} height={26} />
                                 <Tsk width={"100%"} height={20} />
                                 <Tsk width={"100%"} height={20} />
                                 <Tsk className="prjColFp" width={"100%"} height={20} />
                                 <Tsk width={"100%"} height={36} />
                              </div>
                              <span />
                           </div>
                        ))}
                     </div>
               }
            </div>
         </section>
         <ProjectRefreshStatus engineMode={project.engineMode} homedata={project.fulldata} homeApi={homeApi} pageurl={"projects"} />
      </>
   );
}

export default Dashboard;
