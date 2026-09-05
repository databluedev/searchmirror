import React, { useState } from "react";
import Tooltip from "@mui/material/Tooltip";
import Cookies from "universal-cookie";
import axios from "axios";
import { toast } from "react-toastify";

import { Button } from "@/components/ui/button";
import { useCapability } from "../../commonComponents/capability_notice";

/**
 * Runs every Geo Citations prompt in the active project.
 *
 * Nothing else in the product triggers this. Prompts are created with status
 * INIT and, without a scheduler configured, sit there indefinitely -- so this
 * button is the only way a self-hoster sees a result at all.
 *
 * It is deliberately its own control rather than folded into the existing
 * refresh icon: refresh re-reads the list and costs nothing, while this asks
 * every configured AI provider and spends the account's own credits.
 */
function LLMRunAnalysis({ onDone }) {
   const [running, setRunning] = useState(false);
   const [progress, setProgress] = useState("");
   const cap = useCapability("geo_citations");

   // undefined while the capability is still unknown -- treat as usable so a
   // slow lookup never disables a button that would have worked.
   const usable = !cap || cap.available !== false;

   const run = async () => {
      if (running || !usable) return;
      setRunning(true);
      setProgress("");

      const cookies = new Cookies();
      const groupid = cookies.get("activegrp");
      let firstRequest = true;
      let completed = 0;
      let total = 0;
      let remaining = 1;

      try {
         while (remaining > 0) {
            const response = await axios.post(
               global.apiurl + "/llmtracker/trigger-processing",
               { groupid, rerun: firstRequest },
               { headers: { Authorization: "Token " + cookies.get("session_token") } }
            );
            const res = response.data;
            const data = res && res.data ? res.data : {};
            if (data.status === "no_prompts") {
               if (completed === 0) toast.info("No prompts in this project. Add one first.");
               break;
            }
            if (data.status === "skipped") {
               toast.info("One of your prompts is already running.");
               break;
            }
            if (!res || res.status !== "true" || data.status !== "success") {
               throw new Error((res && res.message) || "Could not run the analysis.");
            }

            completed += 1;
            total = firstRequest ? data.total_queued : total;
            remaining = data.remaining || 0;
            setProgress(`Running ${completed}/${total}`);
            if (onDone) onDone();
            firstRequest = false;
         }

         if (completed > 0) {
            toast.success(`Analysis complete for ${completed} prompt${completed === 1 ? "" : "s"}.`);
         }
      } catch (error) {
         const status = error && error.response && error.response.status;
         if (status === 401) {
            toast.warning("Session timeout! Log in again");
         } else if (status === 403) {
            toast.error("Not authorised to run this project.");
         } else {
            toast.error(error.message || "Could not reach SearchMirror. Please try again.");
         }
      } finally {
         if (onDone) onDone();
         setRunning(false);
         setProgress("");
      }
   };

   const hint = !usable
      ? (cap && cap.fix) || "Add an AI provider key first."
      : "Re-runs every prompt in this project with each configured AI provider and spends your own provider credits.";

   return (
      <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={hint}>
         {/* Tooltip needs a real element to attach to, and a disabled control
             fires no events -- so the span carries the listener target. */}
         <span className="d-inline-flex">
            <Button
               variant="primary"
               disabled={running || !usable}
               onClick={run}
            >
               {running ? (progress || "Starting…") : "Run analysis"}
            </Button>
         </span>
      </Tooltip>
   );
}

export default LLMRunAnalysis;
