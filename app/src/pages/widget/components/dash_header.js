import React from "react";
import { Link } from "react-router-dom";
import ProjectFavIcon from "../../commonComponents/project_fav_icon";
import { ExternalMark } from "./dash_icons";
import { whenLabel } from "../dashboard_data";

/* Which project this is, and when it was last true.

   The meta line is built from what the payload actually has. An empty region or
   a project that has never run drops its chip instead of rendering a separator
   with nothing after it -- the header used to print "Invalid Date" for exactly
   that case, because it trusted the timestamp and formatted it unconditionally. */

/* Some projects store their domain without a scheme ("datablue.dev"), and a
   bare host in href= is a relative URL -- the link navigates to /datablue.dev
   inside the portal instead of leaving it. */
const externalHref = (domain) =>
   !domain ? "" : /^https?:\/\//i.test(domain) ? domain : "https://" + domain;

/* The host, or nothing. widget/components/common.js does the same parse but
   answers "Domain not available" when it fails, which is a sentence, not a
   host -- putting it in an <h1> or a link label reads as the project's name. */
const hostLabel = (domain) => {
   const href = externalHref(domain);
   if (!href) return "";
   try {
      return new URL(href).hostname.replace(/^www\./, "");
   } catch (error) {
      return "";
   }
};

export default function DashHeader({ project, projectList, showRunMeta }) {
   const href = externalHref(project.domain);
   const host = hostLabel(project.domain);
   const checked = whenLabel(project.lastChecked);
   const next = whenLabel(project.nextRun);

   const chips = [];
   if (project.region && project.language) chips.push(project.region + "/" + project.language);
   else if (project.region) chips.push(project.region);
   else if (project.language) chips.push(project.language);
   if (project.device) chips.push(project.device);
   /* Only claim a run history once a payload has answered. While the request is
      in flight the header is built from the project list, which does not carry
      the timestamps -- printing a never-run chip from that would be a statement
      the page has no evidence for, and it flips a second later.

      "Ranks", not a bare "Checked". Both timestamps are the RANKING run and
      only the ranking run: `last_checked` is the newest `lastranked_date` over
      the keywords and `next_run` is `project_automation_time`
      (backend/serp/dashboard_overview.py, `_project_block`). Neither says
      anything about when the AI answers below were collected, and the header
      sits above both sections -- unqualified, it reads as covering the page. */
   if (showRunMeta) {
      chips.push(checked ? "Ranks checked " + checked : "No ranking run yet");
      if (next) chips.push("Next rank run " + next);
   }

   return (
      <header>
         <div className="dashHead">
            <div className="dashHead__id">
               <ProjectFavIcon projectList={projectList} />
               <div className="dashHead__name">
                  <h1 className="wd-title">{project.name || host || "Dashboard"}</h1>
                  <div className="dashHead__meta">
                     {href && host ? (
                        <a className="dashHead__domain" href={href} target="_blank" rel="noreferrer">
                           {host}
                           <ExternalMark />
                        </a>
                     ) : null}
                     {chips.map((chip, i) => (
                        <span key={i} className="dashHead__chip">
                           {chip}
                        </span>
                     ))}
                  </div>
               </div>
            </div>
            <div className="dashHead__actions">
               <Link className="btn btn-secondary" to="/keywords">
                  Keywords
               </Link>
            </div>
         </div>
      </header>
   );
}
