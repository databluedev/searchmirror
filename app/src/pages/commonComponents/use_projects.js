import { useEffect, useState } from "react";
import Cookies from "universal-cookie";
import axios from "axios";

/* Does this account have a project yet?

   The rail needs to know, and the project list is not available where <Sidebar>
   mounts: private_route.js fetches it inside CommonRoutes, a *child* of the
   rail. project_switcher.js hit the same wall and answered it by calling
   /baseauth itself.

   Rather than a third fetch, this follows the shape capability_notice.js
   established: a module-level cache with one shared in-flight promise, so every
   mount that asks gets the same answer and only one request goes out.

   Why the rail cares: with no project, four features cannot do anything. They
   stay listed -- somebody evaluating SearchMirror should be able to see its
   scope -- but they are marked, and the page they lead to explains what is
   missing instead of failing. */

let cache = null;
let inflight = null;

export function clearProjects() {
   cache = null;
   inflight = null;
}

function loadProjects() {
   if (cache !== null) return Promise.resolve(cache);
   if (inflight) return inflight;

   const cookies = new Cookies();
   const userid = cookies.get("session_userid");
   const token = cookies.get("session_token");

   if (!userid || !token) {
      cache = [];
      return Promise.resolve(cache);
   }

   inflight = axios
      .post(
         global.apiurl + "/baseauth",
         { userid: userid },
         { headers: { Authorization: "Token " + token } }
      )
      .then((r) => r.data)
      .then((res) => {
         cache = res && res.status === "true" && res.data ? res.data.slt || [] : [];
         inflight = null;
         return cache;
      })
      .catch(() => {
         /* A failed lookup is not evidence that the account has no project.
            Returning [] here would mark every feature as unavailable because
            the network blipped, so an unknown answer is treated as "has a
            project" and the page's own guard still refuses to call without a
            grpid. Marking is a hint; the guard is the correctness. */
         inflight = null;
         return null;
      });
   return inflight;
}

/** `true` once a project is known to exist, `false` once it is known not to.
    Starts optimistic so the rail never flashes "unavailable" on load. */
export function useHasProject() {
   const [hasProject, setHasProject] = useState(
      cache === null ? true : cache.length > 0
   );

   useEffect(() => {
      let alive = true;
      loadProjects().then((list) => {
         if (alive && list !== null) setHasProject(list.length > 0);
      });
      return () => {
         alive = false;
      };
   }, []);

   return hasProject;
}
