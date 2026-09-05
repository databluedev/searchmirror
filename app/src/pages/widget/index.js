import React, { useCallback, useEffect, useState } from "react";
import Cookies from "universal-cookie";
import "./style.scss";
import {
   fetchOverview,
   hasRankHistory,
   whenLabel,
   attentionView,
   gapRows,
   movementView,
   keywordShift,
   answerShift,
} from "./dashboard_data";
import { allowsTeamModule } from "../../utils/team_permissions";
import DashHeader from "./components/dash_header";
import AlertBar from "./components/alert_bar";
import RecheckAction from "../commonComponents/recheck_action";
import StatRow from "./components/stat_row";
import TrendPanel from "./components/trend_panel";
import SpreadPanel from "./components/spread_panel";
import AttentionList from "./components/attention_list";
import CompetitorPanel from "./components/competitor_panel";
import AiPanel from "./components/ai_panel";
import Section from "./components/section_band";
import DashSkeleton from "./components/dash_skeleton";
import { NoProjects, LoadError, FirstRun } from "./components/dash_states";

/* The dashboard -- one project, one screen, TWO measurement systems.

   Routed at /dashboard; the directory is still called `widget` because the
   route registration lives outside this lane.

   THE LAYOUT IS FIXED, and it is now fixed in two named sections. Every figure
   on this page belongs to exactly one of them and sits under its band, which
   says which system it is, what produced it and what that costs:

     SEO -- Search rankings, from the DataBlue SERP API
       1  five stat tiles, one strip
       2  visibility trend (2fr) | position spread (1fr)
       3  needs attention (1fr) | competitors (1fr)
     GEO -- AI answers, from Geo Citations
       4  mention rate, one full-width line

   The four rows and their order are exactly what they were; what changed is
   that the reader can now tell row 4 apart from rows 1-3 without knowing the
   product. See components/section_band.js for why the distinction is carried
   by a mark, a name, a tag and a sentence rather than by a colour.

   THE TWO SECTIONS FAIL INDEPENDENTLY, because their sources do. A project
   with Geo prompts answered and no ranking run yet used to render nothing but
   the no-rankings state, and the AI section it had data for disappeared with
   it -- one system's emptiness hid the other's findings. `measured` now gates
   only the SEO section's contents, and the no-rankings state renders inside
   that section as the section's own empty state.

   An earlier cut of this composed the layout from what the payload supported --
   the coverage gap led when the project barely ranked, panels appeared and
   disappeared, columns re-proportioned. It produced a differently shaped screen
   per project, and switching projects read as the page breaking rather than as
   the numbers changing. A section that has nothing to report keeps its slot and
   says so; it never vanishes and never reflows the page.

   The honest-empty-state rule applies INSIDE each slot, not to the slot:
   "first comparison after the next run" rather than three zeros, "no competitor
   is being tracked yet" rather than an absent panel.

   Two things that used to have sections of their own and no longer do, both
   folded into the slot that already owned the subject:
     movement       -- under the trend. Same subject, different resolution: the
                       line is the score over time, movement is what the
                       keywords did over the last window.
     the coverage gap -- into NEEDS ATTENTION (the never-ranked count, then the
                       keywords a rival holds) and into COMPETITORS (who holds
                       them, and how well). It was half a screen arguing from
                       three facts; it is now those three facts. */

/* Which project the shell is pointing at. Read-only -- the cookie is written in
   the effect, so rendering never has a side effect. */
const pickActive = (projectList) => {
   const list = Array.isArray(projectList) ? projectList : [];
   if (list.length === 0) return null;
   const grpid = parseInt(new Cookies().get("activegrp"), 10);
   return list.find((item) => item && item.GY === grpid) || list[0];
};

/* Identity for the header before -- or instead of -- a payload. The project
   list the shell already holds knows the name and the domain, so a failed or
   pending request still says which project failed rather than going blank. */
const identityFrom = (row) => ({
   name: row && row.NM ? String(row.NM) : "",
   domain: row && row.DN ? String(row.DN) : "",
   region: "",
   language: "",
   device: "",
   lastChecked: "",
   nextRun: "",
});

const Dashboard = (props) => {
   const { projectList, fullbasedata } = props;
   const [state, setState] = useState({ loading: true, error: "", data: null });
   const [attempt, setAttempt] = useState(0);

   const retry = useCallback(() => setAttempt((n) => n + 1), []);

   useEffect(() => {
      const row = pickActive(projectList);
      if (!row) {
         setState({ loading: false, error: "", data: null });
         return undefined;
      }

      /* The shell's project switcher writes this cookie, but a stale one
         survives a deleted project. Reconcile before the request, because
         fetchOverview reads the cookie rather than taking a parameter -- the
         same contract every other call in this app uses. */
      const cookies = new Cookies();
      if (String(cookies.get("activegrp")) !== String(row.GY)) {
         cookies.set("activegrp", row.GY, { path: "/", maxAge: global.cookiesexpire });
      }

      const controller = new AbortController();
      let live = true;
      setState((current) => ({ ...current, loading: true, error: "" }));

      fetchOverview(controller.signal).then((result) => {
         if (!live || result.cancelled) return;
         setState({
            loading: false,
            error: result.ok ? "" : result.error,
            data: result.ok ? result.data : null,
         });
      });

      return () => {
         live = false;
         controller.abort();
      };
   }, [projectList, attempt]);

   const activeRow = pickActive(projectList);
   const canAddProject = !fullbasedata || fullbasedata.ac_typ !== "team";

   if (!activeRow) {
      return (
         <section className="layout">
            <header>
               <h1 className="wd-title">Dashboard</h1>
            </header>
            <NoProjects canAddProject={canAddProject} />
         </section>
      );
   }

   const data = state.data;
   const measured = data ? hasRankHistory(data) : false;
   const attention = data ? attentionView(data) : null;

   return (
      <section className="layout">
         <DashHeader
            project={data ? data.project : identityFrom(activeRow)}
            projectList={projectList}
            showRunMeta={Boolean(data)}
         />

         {state.loading ? <DashSkeleton /> : null}

         {!state.loading && state.error ? <LoadError message={state.error} onRetry={retry} /> : null}

         {!state.loading && data ? (
            <>
               {/* Above both sections, because every alert this API sends is
                   about the project itself -- no keywords, no schedule, a check
                   that left keywords without data -- and each one names
                   keywords or ranking in its own text, so it is self-labelling
                   where the figures below are not. */}
               <AlertBar
                  alerts={data.alerts}
                  run={data.run}
                  renderAction={(action) => (
                     <RecheckAction action={action} grpid={data.project && data.project.id} onDone={retry} />
                  )}
               />

               <Section system="seo">
                  {measured ? (
                     <>
                        <StatRow data={data} />

                        <div className="dashRow dashRow--wide">
                           <TrendPanel
                              visibility={data.visibility}
                              movement={data.movement}
                              view={movementView(data.movement)}
                              shift={keywordShift(data)}
                           />
                           <SpreadPanel spread={data.spread} />
                        </div>

                        <div className="dashRow dashRow--even">
                           <AttentionList
                              groups={attention.groups}
                              rows={attention.rows}
                              gaps={allowsTeamModule(fullbasedata, "CompAi") ? gapRows(data) : []}
                           />
                           <CompetitorPanel
                              competitors={allowsTeamModule(fullbasedata, "CompAi") ? data.competitors : []}
                           />
                        </div>
                     </>
                  ) : (
                     /* Not an empty panel -- an empty SECTION. No ranking run
                        has finished, so no row of this section's grid would
                        have anything in it, and three panels of "nothing yet"
                        say less than one sentence does. It is scoped to this
                        section: the AI section below has its own source and is
                        unaffected by a project that has never ranked. */
                     <FirstRun nextRun={whenLabel(data.project.nextRun)} />
                  )}
               </Section>

               {allowsTeamModule(fullbasedata, "LLMTracker") ? (
                  <Section system="geo">
                     <AiPanel ai={data.ai} shift={answerShift(data.ai)} />
                  </Section>
               ) : null}
            </>
         ) : null}
      </section>
   );
};

export default Dashboard;
