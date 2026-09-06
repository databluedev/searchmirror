import React from "react";
import { WarnMark, InfoMark } from "./dash_icons";

/* The alert bar -- what is wrong right now, above everything else.

   THIS COMPONENT DECIDES NOTHING. The API sends the exact list of rows to
   render, in order, and this draws them.

   That is the fix, not a simplification. The rule used to live on both sides
   and the halves did not meet: `dashboard_overview.py` withheld the
   `failed_keywords` alert whenever a run had failed, on the grounds that the
   run row already said it -- and this component then appended the standing
   count back, because it only suppressed its own row when it saw the alert the
   API had deliberately not sent. Every failed run therefore rendered TWO rows
   about the same one keyword. Both sides were individually reasonable and the
   pair was wrong.

   Deciding whether the standing count is already explained by the run needs
   the failed keyword set, which only the server has. So it decides, here we
   draw, and there is one place to change when the wording changes.

   The machine code is NOT rendered. `serp_failed` printed beside the sentence
   told the reader nothing the sentence had not already said, and read as an
   error dump. It still travels in the payload as `row.code`, where it keys the
   list and is useful to anyone reading the response.

   An alert may carry an `action`: something the user can do that CLEARS the
   condition, rather than a dead statement they can only read. An alert is
   never dismissed or faded while it is still true -- the way it goes away is
   by ceasing to be true.

   Nothing wrong, nothing rendered. An always-present bar saying "no alerts"
   would be the largest thing on the screen and would say nothing; the header's
   "checked N hours ago" already answers "did it run". */

export default function AlertBar({ alerts, run, renderAction }) {
   const rows = Array.isArray(alerts) ? alerts : [];

   if (rows.length === 0) return null;

   const hasWarn = rows.some((row) => row.severity === "warn");

   return (
      <div className={"dashAlerts" + (hasWarn ? " dashAlerts--warn" : "")} role="status">
         {rows.map((row, i) => (
            <div key={row.code || "alert-" + i} className={"dashAlert dashAlert--" + (row.severity || "info")}>
               <span className="dashAlert__mark">{row.severity === "warn" ? <WarnMark /> : <InfoMark />}</span>
               <p className="dashAlert__text">{row.text}</p>
               {row.action && renderAction ? renderAction(row.action) : null}
            </div>
         ))}
      </div>
   );
}
