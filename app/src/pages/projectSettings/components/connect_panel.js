import React, { useEffect, useState } from "react";
import Cookies from "universal-cookie";
import axios from "axios";
import { Tsk } from "../../commonComponents/parts";
import { Google } from "../../commonComponents/icons";
import { useCapability } from "../../commonComponents/capability_notice";

/* The "Connect your data" status strip for Settings -> Connected apps.

   It was the top strip of the dashboard, above every widget, and on a default
   install both of its cards report the integration unavailable -- so the most
   prominent element of the product's main screen was a permanent "not
   available". It now sits directly above the controls it describes, where a
   status line is what the reader wants and the OAuth flow is one panel below.

   Google Search Console and Google Analytics share the browser OAuth client,
   but their backend token refreshes use separate configured credentials. Each
   card therefore uses its own capability instead of claiming that GSC setup
   also makes Analytics available. When either capability is missing, the card
   says which credentials to set instead of offering an action that cannot work.

   Status is read live from the exact verify calls Connected Apps uses
   (/connectgsc and /connectga with type:"verify"), scoped to the active
   project. There are no Connect / Manage actions here: the full OAuth and
   property-selection flow is the next thing on the page, so a button that
   scrolled the reader to where they already are would be noise. Verify errors
   are swallowed rather than toasted -- Settings must not throw error toasts
   because a self-hosted instance has not wired Google up yet. */

function useConnection(endpoint, unavailable) {
   // undefined while unknown, then true / false; property is GSC's site url.
   const [conn, setConn] = useState({ status: undefined, property: "" });

   useEffect(() => {
      // No Google client on this instance: nothing to verify against.
      if (unavailable) {
         setConn({ status: false, property: "" });
         return;
      }

      const cookies = new Cookies();
      const userid = cookies.get("session_userid");
      const grpid = cookies.get("activegrp");
      const usertoken = cookies.get("session_token");

      // Verify is per-project. With no active project, there is nothing to
      // check -- report "not connected" and let Connect route on.
      if (!userid || !grpid || !usertoken) {
         setConn({ status: false, property: "" });
         return;
      }

      let alive = true;
      axios
         .post(
            global.apiurl + endpoint,
            { userid: userid, grpid: grpid, gcode: "", type: "verify" },
            { headers: { Authorization: "Token " + usertoken } }
         )
         .then((r) => r.data)
         .then((res) => {
            if (!alive) return;
            setConn({
               status: !!(res && res.status),
               property: (res && res.gsc_property) || "",
            });
         })
         .catch(() => {
            if (alive) setConn({ status: false, property: "" });
         });

      return () => {
         alive = false;
      };
   }, [endpoint, unavailable]);

   return conn;
}

function ProviderCard({ name, endpoint, cap }) {
   const unavailable = !!(cap && cap.available === false);
   const conn = useConnection(endpoint, unavailable);

   return (
      <div className="connCard">
         <div className="connCardHead">
            <span className="connCardIcon">
               <Google />
            </span>
            <span className="connCardName">{name}</span>
         </div>

         {unavailable ? (
            /* The capability system already carries the operator-facing copy:
               what is needed and how to set it. Reuse it verbatim rather than
               writing a second, driftable version of the same sentence. */
            <div className="connCardBody">
               <span className="connState connStateNeeds">Needs {cap.needs}</span>
               <span className="connCardFix">{cap.fix}</span>
            </div>
         ) : conn.status === undefined ? (
            <div className="connCardBody">
               <Tsk width={120} height={14} />
            </div>
         ) : conn.status ? (
            <div className="connCardBody">
               <span className="connState connStateOn">
                  <span className="connDot" aria-hidden="true" />
                  Connected
               </span>
               {conn.property ? (
                  <span className="connCardProp" title={conn.property}>
                     {conn.property}
                  </span>
               ) : null}
            </div>
         ) : (
            <div className="connCardBody">
               <span className="connState connStateOff">
                  <span className="connDot" aria-hidden="true" />
                  Not connected
               </span>
            </div>
         )}
      </div>
   );
}

function ConnectPanel() {
   const gscCap = useCapability("search_console");
   const gaCap = useCapability("google_analytics");

   return (
      <section className="connPanel" aria-label="Connection status">
         <div className="connPanelHead">
            <span className="connPanelSub">
               Linking Google enriches rankings with clicks, impressions and traffic.
            </span>
         </div>
         <div className="connPanelGrid">
            <ProviderCard
               name="Google Search Console"
               endpoint="/connectgsc"
               cap={gscCap}
            />
            <ProviderCard
               name="Google Analytics"
               endpoint="/connectga"
               cap={gaCap}
            />
         </div>
      </section>
   );
}

export default ConnectPanel;
