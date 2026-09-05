import React, { useEffect, useRef, useState } from "react";
import Cookies from "universal-cookie";
import axios from "axios";
import { toast } from "react-toastify";

import { ConfirmDialog, ModalBox } from "./Modals";

/* Re-check the keywords a run could not measure.

   THIS SPENDS THE ACCOUNT HOLDER'S MONEY. Every keyword it re-checks is a
   billed provider request against their own DataBlue key, so:

     - the cost is stated before anything happens, in searches, priced by the
       server (only it knows each keyword's own depth)
     - nothing is requested until the user confirms
     - the control disables itself while a run is in flight, so a double click
       cannot buy the same data twice

   It drives the SAME path Refresh already uses -- POST /usercrawl with a list
   of keyword ids -- and polls /refreshstatus the way RefreshBar does, with a
   cap so it reports honestly and stops instead of spinning on an instance
   where nothing drains the queue. No new endpoint exists for this.

   The point of the control is that the alert it sits in can then GO AWAY by
   ceasing to be true, rather than by being dismissed while still true. */

const POLL_MS = 5000;
// 36 polls x 5s = 3 minutes, well past a re-check of a handful of keywords.
const MAX_POLLS = 36;

export default function RecheckAction({ action, grpid, onDone, className }) {
   const [confirming, setConfirming] = useState(false);
   const [running, setRunning] = useState(false);

   const pollRef = useRef(null);
   const attemptsRef = useRef(0);
   const abortRef = useRef(null);
   if (abortRef.current === null) {
      abortRef.current = new AbortController();
   }

   useEffect(() => () => {
      clearInterval(pollRef.current);
      abortRef.current.abort();
   }, []);

   if (!action || !action.keyword_ids || action.keyword_ids.length === 0) {
      return null;
   }

   const cookies = new Cookies();
   const usertoken = cookies.get("session_token");
   const userid = cookies.get("session_userid");
   const projectid = grpid || cookies.get("activegrp");

   const finish = (ok, message) => {
      clearInterval(pollRef.current);
      setRunning(false);
      if (message) {
         ok ? toast.success(message) : toast.info(message);
      }
      if (onDone) onDone(ok);
   };

   const poll = () => {
      attemptsRef.current = 0;
      pollRef.current = setInterval(() => {
         attemptsRef.current += 1;
         if (attemptsRef.current > MAX_POLLS) {
            finish(false, "The re-check is taking longer than expected. Reload to see where it got to.");
            return;
         }
         axios.post(global.apiurl + "/refreshstatus",
            { userid: userid, grpid: projectid, cntid: "onload" },
            { headers: { Authorization: "Token " + usertoken }, signal: abortRef.current.signal }
         ).then((response) => response.data).then((res) => {
            if (res.status !== "true") return;
            if (res.errc) {
               // Terminal. The engine writes `err` with counts this side
               // cannot reconstruct, so it is rendered verbatim.
               finish(false, res.err || "The re-check could not be completed.");
            } else if (parseInt(res.runkeyword) === 0 && res.rst === "done") {
               finish(true, "Re-check finished.");
            }
         }).catch((error) => {
            if (axios.isCancel(error)) return;
            finish(false, "Lost contact while re-checking. Reload to see where it got to.");
         });
      }, POLL_MS);
   };

   const spend = () => {
      setConfirming(false);
      setRunning(true);
      axios.post(global.apiurl + "/usercrawl",
         { userid: userid, grpid: projectid, ids: action.keyword_ids },
         { headers: { Authorization: "Token " + usertoken } }
      ).then((response) => response.data).then((res) => {
         if (res.status === "true") {
            poll();
         } else {
            finish(false, res.message || "The re-check could not be started.");
         }
      }).catch(() => {
         finish(false, "The re-check could not be started. Please try again.");
      });
   };

   return (
      <>
         <button
            type="button"
            className={className || "dashAlert__action"}
            onClick={() => setConfirming(true)}
            disabled={running}
         >
            {running ? "Re-checking…" : action.label}
         </button>

         <ModalBox title={action.label} open={confirming} onClose={() => setConfirming(false)}>
            <ConfirmDialog
               modalClose={() => setConfirming(false)}
               cancelTitle="Cancel"
               confirmTitle="Re-check now"
               modalCancel={() => setConfirming(false)}
               modalConfirm={spend}
               content={
                  (action.cost_note || "This spends DataBlue searches, billed to your own API key.")
                  + " Nothing is requested until you confirm. If the provider fails again the alert stays, showing the new attempt."
               }
            />
         </ModalBox>
      </>
   );
}
