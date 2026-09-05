import React from "react";
import { Link } from "react-router-dom";

/* The three screens that are not the dashboard.

   docs/DESIGN.md, "Empty state": micro-label, one sentence, one action, no art.
   Each of these is a state a real account lands in, not a fallback nobody sees,
   so each says what happened and where to go next. */

/* No project at all. A dashboard reports on one project's keywords, so there is
   nothing for the page to be about. `loading` used to be set in one place that
   returned early on an empty list, and the screen sat on its spinner for ever. */
export function NoProjects({ canAddProject }) {
   return (
      <div className="emptyState">
         <p className="emptyState__label">No projects</p>
         <p className="emptyState__body">
            A dashboard reports on one project&rsquo;s keywords. Add the site you want to track and this page fills
            in after the first ranking refresh.
         </p>
         {canAddProject ? (
            <div className="emptyState__action">
               <Link className="btn btn-primary" to="/addproject">
                  Add project
               </Link>
            </div>
         ) : null}
         {/* Ranking needs a DataBlue key, and the key lives in Settings. Naming
             it here is the difference between a new account that can get started
             and one that adds a project, refreshes, and is told nothing about why
             no ranks arrive. Only the owner sees it: a team member has no API Key
             tab to open. */}
         {canAddProject ? (
            <p className="emptyState__body">
               Ranking runs on your own DataBlue SERP key &mdash; add it under{" "}
               <Link to="/settings/apikey">Settings &rsaquo; API Key</Link> before the first refresh.
            </p>
         ) : null}
      </div>
   );
}

/* The request failed. The message is whatever the API or the transport said,
   rendered as it came: "could not be loaded" on its own is the failure the
   audit called out, because it leaves nothing to act on and no way to retry. */
export function LoadError({ message, onRetry }) {
   return (
      <div className="emptyState">
         <p className="emptyState__label">Dashboard unavailable</p>
         <p className="emptyState__body">{message}</p>
         <div className="emptyState__action">
            <button type="button" className="btn btn-primary" onClick={onRetry}>
               Try again
            </button>
         </div>
      </div>
   );
}

/* The project exists and no ranking run has finished. Every panel would be a
   row of zeros, and a row of zeros is indistinguishable from a project that is
   doing badly -- so the page says which one this is instead. */
export function FirstRun({ nextRun }) {
   return (
      <div className="emptyState">
         <p className="emptyState__label">No rankings yet</p>
         <p className="emptyState__body">
            Nothing has been measured for this project, so there is no score, no movement and nothing to act on.
            {nextRun ? " The next ranking run is " + nextRun + "." : ""}
         </p>
         <div className="emptyState__action">
            <Link className="btn btn-primary" to="/keywords">
               Keywords
            </Link>
         </div>
      </div>
   );
}
