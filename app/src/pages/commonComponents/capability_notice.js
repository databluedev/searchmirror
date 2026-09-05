import React, { useEffect, useState } from "react";
import Cookies from "universal-cookie";
import axios from "axios";

// The capability map is per-account but changes only when a key is added or
// removed, so every page mounting its own request would be pure noise. One
// in-flight promise is shared across mounts and the answer is cached for the
// session; adding or removing a key calls clearCapabilities() to drop it.
let cache = null;
let inflight = null;
const CAPABILITY_LOOKUP_FAILED = Object.freeze({
   available: false,
   needs: "capability status",
   blocks: "SearchMirror could not verify whether this feature is configured.",
   fix: "Retry after checking the backend connection.",
});

export function clearCapabilities() {
   cache = null;
   inflight = null;
}

function loadCapabilities() {
   if (cache) return Promise.resolve(cache);
   if (inflight) return inflight;

   const cookies = new Cookies();
   inflight = axios
      .get(global.apiurl + "/api/account/capabilities/", {
         headers: { Authorization: "Token " + cookies.get("session_token") },
      })
      .then((r) => r.data)
      .then((res) => {
         cache = res && res.status === "true" ? res.capabilities || {} : {};
         inflight = null;
         return cache;
      })
      .catch(() => {
         // Unknown is not evidence that a provider is configured. Keep the
         // feature unavailable until the backend can measure its capability.
         cache = {};
         inflight = null;
         return cache;
      });
   return inflight;
}

export function useCapability(name) {
   const [cap, setCap] = useState(
      cache ? cache[name] || CAPABILITY_LOOKUP_FAILED : undefined
   );

   useEffect(() => {
      let alive = true;
      loadCapabilities().then((all) => {
         if (alive) setCap(all[name] || CAPABILITY_LOOKUP_FAILED);
      });
      return () => {
         alive = false;
      };
   }, [name]);

   return cap;
}

/**
 * Explains why a feature has no data, instead of leaving an empty table that
 * reads identically to a genuine zero.
 *
 * Renders nothing while the answer is unknown and nothing once the feature is
 * available, so it is safe to drop above any page body.
 */
export function CapabilityNotice({ name }) {
   const cap = useCapability(name);

   if (!cap || cap.available !== false) return null;

   return (
      <div className="capNotice" role="status">
         <div className="capNoticeBody">
            <span className="capNoticeTitle">Needs {cap.needs}</span>
            <span className="capNoticeText">{cap.blocks}</span>
            <span className="capNoticeFix">{cap.fix}</span>
         </div>
      </div>
   );
}

export default CapabilityNotice;
