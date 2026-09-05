import React, { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import Popover from "@mui/material/Popover";
import Cookies from "universal-cookie";
import axios from "axios";
import SiteMark, { siteHost } from "./site_mark";

// --- global project switcher --------------------------------------------------
// Under the brand at the top of the rail so the active project can be changed
// from any page, not only the pages that happen to carry a per-page dropdown.
//
// The project list is not available where <Sidebar> is mounted (private_route.js
// fetches it inside CommonRoutes, a *child* of the rail), so the switcher fetches
// /baseauth itself -- the same call shape app_home.js and private_route.js use --
// and caches the result. The active project is the `activegrp` cookie, which the
// per-page toggles read too, so the two stay in sync.
//
// Selecting a different project rewrites the cookie and reloads the current
// route: the URL does not change, only the data context does, so every page
// re-reads the cookie and refetches. That is the equivalent of "stay on the same
// page in the new project".

// A tick beside the active project. Its own mark, not a rail icon -- it means
// "current selection", which none of the NAV icons say.
function Check(props) {
   return (
      <svg
         xmlns="http://www.w3.org/2000/svg"
         width="16"
         height="16"
         viewBox="0 0 24 24"
         fill="none"
         stroke="currentColor"
         strokeWidth="2"
         strokeLinecap="round"
         strokeLinejoin="round"
         aria-hidden="true"
         focusable="false"
         {...props}
      >
         <path d="m5 12.5 4.5 4.5L19 7" />
      </svg>
   );
}

// Up/down double chevron -- the standard "this is a switcher you can open"
// affordance (as in the reference tool), distinct from a one-way disclosure.
function ChevronsUpDown(props) {
   return (
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
         fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
         strokeLinejoin="round" aria-hidden="true" focusable="false" {...props}>
         <path d="m7 15 5 5 5-5" />
         <path d="m7 9 5-5 5 5" />
      </svg>
   );
}

function activeProject(projects, grpid) {
   if (!projects.length) return null;
   const id = parseInt(grpid, 10);
   const hit = projects.find((p) => p.GY === id);
   return hit || projects[0];
}

function ProjectSwitcher() {
   const [projects, setProjects] = useState([]);
   const [loading, setLoading] = useState(true);
   const [grpid, setGrpid] = useState(() => {
      try {
         return new Cookies().get("activegrp");
      } catch (e) {
         return undefined;
      }
   });
   const [anchorEl, setAnchorEl] = useState(null);
   const buttonRef = useRef(null);

   // One /baseauth read, aborted if the rail unmounts before it lands so its
   // .then never sets state on a gone component.
   useEffect(() => {
      const controller = new AbortController();
      const cookies = new Cookies();
      const usertoken = cookies.get("session_token");
      const userid = cookies.get("session_userid");
      if (!usertoken || !userid) {
         setLoading(false);
         return () => controller.abort();
      }

      axios
         .post(
            global.apiurl + "/baseauth",
            { userid },
            {
               headers: { Authorization: "Token " + usertoken },
               signal: controller.signal,
            }
         )
         .then((response) => response.data)
         .then((res) => {
            if (res.status === "true" && res.data && Array.isArray(res.data.slt)) {
               setProjects(res.data.slt);
            }
            setLoading(false);
         })
         .catch(() => {
            // A failed fetch leaves the switcher in its empty state rather than
            // blocking the rail; the per-page toggles still carry their own data.
            setLoading(false);
         });

      return () => controller.abort();
   }, []);

   const active = useMemo(() => activeProject(projects, grpid), [projects, grpid]);
   const open = Boolean(anchorEl);

   const openMenu = () => setAnchorEl(buttonRef.current);
   const closeMenu = () => setAnchorEl(null);

   const selectProject = (project) => {
      const cookies = new Cookies();
      const current = cookies.get("activegrp");
      if (String(project.GY) === String(current)) {
         closeMenu();
         return;
      }
      cookies.set("activegrp", project.GY.toString(), {
         path: "/",
         maxAge: global.cookiesexpire,
      });
      // The checked-keyword selection is scoped to a project; carrying it into a
      // different project would restore rows that are not there.
      cookies.remove("checkedListAll", { path: "/" });
      setGrpid(project.GY);
      // Same route, new data context -- every page re-reads the cookie on load.
      window.location.reload();
   };

   // Nothing to switch between yet. While the first fetch is in flight show a
   // quiet placeholder; once it is known to be empty, offer the one action that
   // makes sense -- create the first project.
   if (loading && !projects.length) {
      return (
         <div className="railSwitcher railSwitcher--loading" aria-hidden="true">
            <span className="railSwitcher__mark railSwitcher__mark--skeleton" />
            <span className="railSwitcher__skeleton" />
         </div>
      );
   }

   if (!active) {
      return (
         <div className="railSwitcher">
            <Link
               to="/addproject"
               className="railSwitcher__btn railSwitcher__btn--add"
               title="New project"
               aria-label="New project"
            >
               <span className="railSwitcher__addMark" aria-hidden="true">+</span>
               <span className="railSwitcher__meta">
                  <span className="railSwitcher__name">New project</span>
               </span>
            </Link>
         </div>
      );
   }

   const activeHost = siteHost(active.DN);

   return (
      <div className="railSwitcher">
         <button
            type="button"
            ref={buttonRef}
            className="railSwitcher__box"
            onClick={openMenu}
            title={active.NM || activeHost || "Switch project"}
            aria-label={`Active project: ${active.NM || activeHost || ""}. Switch project`}
            aria-haspopup="menu"
            aria-expanded={open}
         >
            <SiteMark domain={active.DN} width={20} height={20} className="railSwitcher__mark" />
            <span className="railSwitcher__name">{active.NM || activeHost}</span>
            <ChevronsUpDown className="railSwitcher__chevron" />
         </button>

         <Popover
            className="railSwitcherMenu"
            open={open}
            anchorEl={anchorEl}
            onClose={closeMenu}
            anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
            transformOrigin={{ vertical: "top", horizontal: "left" }}
         >
               <div className="railSwitcherMenu__list" role="menu">
                  {projects.map((project) => {
                     const isActive = active && project.GY === active.GY;
                     const host = siteHost(project.DN);
                     return (
                        <button
                           type="button"
                           role="menuitem"
                           key={project.GY}
                           className={isActive ? "railSwitcherMenu__item is-active" : "railSwitcherMenu__item"}
                           onClick={() => selectProject(project)}
                           aria-current={isActive ? "true" : undefined}
                        >
                           <SiteMark domain={project.DN} width={24} height={24} className="railSwitcherMenu__mark" />
                           <span className="railSwitcherMenu__name text-truncate">{project.NM || host}</span>
                           {isActive ? <Check className="railSwitcherMenu__check" /> : null}
                        </button>
                     );
                  })}
               </div>
               <div className="railSwitcherMenu__footer">
                  <Link to="/addproject" className="railSwitcherMenu__action" onClick={closeMenu}>
                     <span className="railSwitcherMenu__actionMark" aria-hidden="true">+</span>
                     New project
                  </Link>
                  <Link to="/projects" className="railSwitcherMenu__action" onClick={closeMenu}>
                     Manage projects
                  </Link>
               </div>
         </Popover>
      </div>
   );
}

export default ProjectSwitcher;
