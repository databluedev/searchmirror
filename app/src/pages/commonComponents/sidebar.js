import React, { useEffect, useLayoutEffect, useState, } from "react";
import { DOCS_URL, REPO_URL } from "../landing/lib/site";
import { Link, useHistory, useLocation } from "react-router-dom";
import {
   ProSidebar,
   Menu,
   MenuItem,
   SidebarHeader,
   SidebarFooter,
   SidebarContent,
} from "react-pro-sidebar";

import "react-pro-sidebar/dist/css/styles.css";
import LogoSymbol from "../../assets/images/logo-dark.png";
import MenuIcon from "../../assets/images/menu-icon.svg";
import CloseIcon from "../../assets/images/close-1.svg";
import { Text, SmallText, Title, AppIconButton } from "./parts";

import { cookiesremove } from "../common_fun";
import Cookies from 'universal-cookie';
import axios from 'axios';
import ProjectSwitcher from "./project_switcher";

// import profileImg from "../../assets/images/test.jpg";
import { Button, Box, Drawer } from "@mui/material";
import Popover from "@mui/material/Popover";
import MenuList from "@mui/material/MenuList";
// MUI's MenuItem, deliberately aliased. `MenuItem` in this file is
// react-pro-sidebar's, which powers the rail and takes `onClick` but has no
// `component`/`href`. The two links below sit inside a MUI <MenuList> and were
// written with MUI's API, so those props were dropped on the floor and both
// rows rendered inert -- the project's source and documentation were
// unreachable from inside the app, which is the exact thing the comment below
// says this menu exists to fix.
import MuiMenuItem from "@mui/material/MenuItem";
// import WallLogo from "../../assets/images/Walmart_Spark.png";

import ClickAwayListener from '@mui/material/ClickAwayListener';

// Rail icons -- one family, 18px / 1.5px stroke / currentColor. See railIcons.js.
import {
   NavProjects, NavDashboard, NavKeywords,
   NavPlanner, NavGlobe, NavSpark,
   NavReports, NavSettings, NavLogout, NavChevron,
} from "./railIcons";

// --- the signed-in user's name -------------------------------------------
// One normalisation for every place the shell prints the user: the avatar
// initials, the account row and the greeting. They read the same prop, so
// they must not disagree about what it says.
//
// `uname` is the session_username cookie, read through universal-cookie,
// whose `cookie` dependency runs decodeURIComponent on every value it parses.
// It therefore arrives decoded -- "Local%20Client" is already "Local Client"
// by the time it reaches this file, and decoding it a second time would
// corrupt any name that legitimately contains a per-cent sign. The guarded
// decode below fires only when the string still holds a valid escape, which
// means only when something upstream encoded it twice.
function displayName(raw) {
   let name = String(raw == null ? "" : raw).trim();

   if (/%[0-9A-Fa-f]{2}/.test(name)) {
      try {
         name = decodeURIComponent(name).trim();
      } catch (e) {
         // Malformed escape. The raw value is the better of the two.
      }
   }

   // An account with no display name set carries its email address instead.
   // Greeting someone by their full address reads as a database row, so keep
   // what is in front of the @ and let the rest go.
   const at = name.indexOf("@");
   if (at > 0) name = name.slice(0, at);

   return name.replace(/\s+/g, " ").trim();
}

// Avatar -- docs/DESIGN.md, "Avatar": the user's own initials, drawn locally.
// Nothing here reaches an avatar service and no illustration is imported.
function initials(name) {
   const parts = displayName(name).split(" ").filter(Boolean);
   if (parts.length === 0) return "?";
   if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
   return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

// --- rail state ----------------------------------------------------------
// The rail used to be permanently collapsed and expand on :hover, which meant
// it opened whenever the pointer crossed it on the way somewhere else and gave
// no sense of place. It is now a persistent panel the user opens or closes
// deliberately, and that choice is remembered.
const RAIL_PREF = "tracker.rail.collapsed";

function readRailPref(fallback) {
   try {
      const stored = window.localStorage.getItem(RAIL_PREF);
      if (stored === "1") return true;
      if (stored === "0") return false;
   } catch (e) {
      // Safari private mode throws on localStorage; fall through to the default.
   }
   return fallback;
}

// Below 1200px an expanded 248px rail leaves too little for a keyword table, so
// that is where the rail starts collapsed for anyone who has not chosen.
function narrowViewport() {
   try {
      return window.matchMedia("(max-width:1199px)").matches;
   } catch (e) {
      return false;
   }
}

function writeRailPref(collapsed) {
   try {
      window.localStorage.setItem(RAIL_PREF, collapsed ? "1" : "0");
   } catch (e) {
      // Preference is a convenience, not a requirement.
   }
}

// A group heading in the mobile drawer, where there is always room to show
// every section at once. The text is aria-hidden because each group's <Menu>
// carries the same name as its accessible label, and announcing it twice helps
// nobody.
function RailGroup({ label, first }) {
   return (
      <div className={first ? "railGroup railGroup--first" : "railGroup"} aria-hidden="true">
         <span>{label}</span>
      </div>
   );
}

// --- rail sections -------------------------------------------------------
// The retired modules reduced this navigation to a short list. Keep every
// section open by default so destinations are immediately visible; each
// heading remains an independent disclosure for users who prefer less chrome.
//
// Route keys are the first path segment, the same value the items already
// match `active` against, so the map cannot drift from the links below it.
const NAV_GROUPS = [
   { id: "tracking", label: "Tracking", routes: ["dashboard", "keywords", "llmtracker"] },
   { id: "content", label: "Content", routes: ["contentplanner"] },
   { id: "insights", label: "Insights", routes: ["competitors", "reports"] },
];

// The links themselves. The rail and the drawer used to carry a copy each and
// had already drifted apart -- the drawer was missing every "new" dot, gave Geo
// Citations a different item class, and spelled two labels differently -- so a
// menu change had to be made twice and was made once. They are one list now,
// rendered by <NavLinks> into both shells; only the shells differ.
//
// `match` is compared against the first path segment (`activeMenu`) and `sub`,
// where present, against the second, so the highlight cannot drift from `to`.
const NAV_ITEMS = {
   // All Projects lists and switches between projects, so it is global chrome --
   // it belongs beside the project switcher, not inside Tracking. It renders as a
   // standalone, always-visible entry above the first group heading in both the
   // rail and the drawer, not as a member of any collapsible section.
   projects: [
      { to: "/projects", match: "projects", module: "Prjcts", cls: "projectMenu", Icon: NavProjects, label: " All Projects " },
   ],
   tracking: [
      { to: "/dashboard", match: "dashboard", module: "Widgets", cls: "dashboardMenu", Icon: NavDashboard, label: " Dashboard " },
      { to: "/keywords", match: "keywords", module: "Keyword", cls: "rankMenu", Icon: NavKeywords, label: " Keywords " },
      { to: "/llmtracker", match: "llmtracker", module: "LLMTracker", cls: "reportMenu", Icon: NavGlobe, label: " Geo Citations ", isNew: true },
   ],
   content: [
      { to: "/contentplanner", match: "contentplanner", module: "ContentPlanner", cls: "reportMenu", Icon: NavPlanner, label: " Content Planner ", isNew: true },
   ],
   insights: [
      { to: "/competitors", match: "competitors", module: "CompAi", cls: "aiMenu", Icon: NavSpark, label: " Competitors " },
   ],
   // Reports is client-visible, so on the rail it cannot live inside the gated
   // Insights <Menu> -- hiding that group took Reports with it.
   reports: [
      { to: "/reports", match: "reports", module: "Reports", cls: "reportMenu", Icon: NavReports, label: "Reports" },
   ],
   account: [
      { to: "/settings", match: "settings", module: "Settings", cls: "settingMenu", Icon: NavSettings, label: "Settings" },
   ],
};

const GROUP_PREF = "tracker.rail.groups.v2";

function groupForRoute(route) {
   const hit = NAV_GROUPS.find((g) => g.routes.indexOf(route) !== -1);
   return hit ? hit.id : null;
}

// Stored state wins over the default, but the section holding the current
// route is always open on top of it -- a rail that hides the page you are on
// is worse than one that ignores a preference for a moment.
function readGroupPref(activeId) {
   const state = {};
   NAV_GROUPS.forEach((g) => { state[g.id] = true; });

   try {
      const stored = JSON.parse(window.localStorage.getItem(GROUP_PREF));
      if (stored && typeof stored === "object") {
         NAV_GROUPS.forEach((g) => {
            if (typeof stored[g.id] === "boolean") state[g.id] = stored[g.id];
         });
      }
   } catch (e) {
      // Private mode throws, and a hand-edited value throws in JSON.parse.
      // Either way the computed default stands.
   }

   if (activeId) state[activeId] = true;
   return state;
}

function writeGroupPref(state) {
   try {
      window.localStorage.setItem(GROUP_PREF, JSON.stringify(state));
   } catch (e) {
      // Preference is a convenience, not a requirement.
   }
}

// The heading is the control. Collapsed to 68px there is no room for the word,
// so `.railGroup--btn` in _shell.scss turns it into the hairline that already
// separated the sections -- same element, same place in the flow, and the
// section name survives in the tooltip and the accessible name.
function RailGroupToggle({ group, open, first, onToggle }) {
   return (
      <button
         type="button"
         className={first ? "railGroup railGroup--btn railGroup--first" : "railGroup railGroup--btn"}
         aria-controls={`railSection-${group.id}`}
         aria-expanded={open}
         onClick={() => onToggle(group.id)}
         title={open ? `Collapse ${group.label}` : `Expand ${group.label}`}
      >
         <span>{group.label}</span>
         <NavChevron className="submenuChevron railGroup__chevron" />
      </button>
   );
}

// One section's worth of links, drawn identically in the rail and the drawer.
// The <Menu> around it supplies the section; everything inside the row -- icon,
// label, "new" dot, Beta tag -- comes from NAV_ITEMS. An array rather than a
// fragment: react-pro-sidebar's <Menu> clones each of its children to pass
// `firstchild`, and a fragment cannot take props.
function visibleNavItems(items, teamModules) {
   return items.filter((item) => (
      !teamModules || !item.module || Object.prototype.hasOwnProperty.call(teamModules, item.module)
   ));
}

function NavLinks({ items, activeMenu, teamModules }) {
   /* The rail does NOT mark what the account cannot use yet. It was tried and
      removed: on a new account nothing is usable, so every row carried the same
      "Set up" chip -- and a marker that applies to every item carries no
      information. It read as six faults rather than one next step, and fought
      the "new" dots for the same 8px.

      "+ New project" already sits at the top of this rail, and each page
      explains what it needs when you open it. The explanation belongs at the
      point of intent, not smeared across the navigation. */
   return visibleNavItems(items, teamModules).map(({ to, match, cls, Icon, label, isNew, tag }) => {
      const name = label.trim();
      const active = activeMenu === match;

      return (
         <Link className="" to={to} key={to} style={{ textDecoration: 'none' }} title={name} aria-label={name}>
            <MenuItem active={active} className={cls}>
               <Icon />
               <span className="item">{label}</span>
               {isNew ? <span className="railNew" aria-hidden="true" /> : null}
               {tag ? <span className="complable m-l10">{tag}</span> : null}
            </MenuItem>
         </Link>
      );
   });
}

// --- greeting ------------------------------------------------------------
// The app bar's one line of copy. The name comes from the session_username
// cookie, which private_route.js already reads and passes down as `uname`;
// nothing here asks the API for something the shell was handed.
//
// It greets by the WHOLE name, not the first word. "Local Client" is not
// "Local": the cookie holds the name the user chose, cutting it at the first
// space throws half of it away, and the avatar beside the greeting already
// spells out both initials -- "LC" next to "Local" is the shell contradicting
// itself. A one-word name greets as that one word, and an empty one drops the
// name rather than greeting a blank.
function greetingFor(name, now) {
   const hour = now.getHours();
   const part = hour < 12 ? "Good morning" : hour < 17 ? "Good afternoon" : "Good evening";
   const who = displayName(name);
   return { part: who ? part : "Welcome back", name: who };
}

// SCROLL BAR OPTIONS - STARTS

// SCROLL BAR OPTIONS - ENDS



// DESKTOP SIDEBAR OPTIONS - STARTS
export function Sidebar({ children, ...props }) {
   // Open unless the user has said otherwise, or unless there is not much room
   // to open into. Read once, during the first render, so the rail paints at
   // its final width instead of opening and then snapping shut.
   const [menuCollapse, setMenuCollapse] = useState(() => readRailPref(narrowViewport()));
   const [isActive, setActive] = useState(false);
   const [openSide, setOpenSide] = useState(false);

   const location = useLocation();
   var { pathname } = location;
   var splitLocation = pathname.split("/");
   var activeMenu = splitLocation.length > 1 ? splitLocation[1] : "";

   const activeGroup = groupForRoute(activeMenu);
   const [openGroups, setOpenGroups] = useState(() => readGroupPref(activeGroup));

   // Arriving in a shut section from somewhere else -- a card link, a redirect,
   // the browser's back button -- opens it, and that counts as a choice, so it
   // is stored like one.
   useEffect(() => {
      if (!activeGroup) return;
      setOpenGroups((prev) => {
         if (prev[activeGroup]) return prev;
         const next = { ...prev, [activeGroup]: true };
         writeGroupPref(next);
         return next;
      });
   }, [activeGroup]);

   // Groups are independent. With this shorter open-source menu, opening one
   // destination area must not hide another.
   const toggleGroup = (id) => {
      setOpenGroups((prev) => {
         const next = { ...prev, [id]: !prev[id] };
         writeGroupPref(next);
         return next;
      });
   };

   const greeting = greetingFor(props.uname, new Date());

   useEffect(() => {
   }, [isActive, location]);


   // The rail is `position: fixed`, so the page cannot see its width through
   // the DOM. One class on <body> drives `--rail-w`, and `.layout` and the
   // toggle both read it -- see the "shell metrics" block in _shell.scss.
   // Layout effect, not effect: the canvas transitions its margin, so a class
   // applied after the first paint would animate the page in from the wrong
   // gutter on every load.
   useLayoutEffect(() => {
      document.body.classList.toggle("railCollapsed", menuCollapse);
      return () => document.body.classList.remove("railCollapsed");
   }, [menuCollapse]);

   const toggleRail = () => {
      const next = !menuCollapse;
      writeRailPref(next);
      setMenuCollapse(next);
   };

   const [anchorEl, setAnchorEl] = React.useState(false);

   const handleClickAway = (event) => {
      if (openSide === true) {
         const div = document.querySelector('.pro-sidebar');
         setOpenSide(false);
         div.classList.remove('active');
         setAnchorEl(false);
         setActive(false);
      }
   }

   const handleClick = (event) => {
      const div = document.querySelector('.pro-sidebar');
      // div.classList.add('active');
      // setAnchorEl(event.currentTarget);
      // setActive(true);
      if (openSide === false) {
         setOpenSide(true);
         div.classList.add('active');
         setAnchorEl(event.currentTarget);
         setActive(false);
      } else {
         setOpenSide(false);
         div.classList.remove('active');
         setAnchorEl(false);
         setActive(false);
      }
   };
   const history = useHistory();

   const logout = () => {
      const cookies = new Cookies();
      const userid = cookies.get('session_userid');
      // const usertoken = cookies.get('session_token');

      const data = {
         'userid': userid,
      };

      axios.post(global.apiurl + '/last_logout', data, {
         headers: { 'Authorization': global.token }
      }).then(response => {
         return response.data;
      }).then(res => {
         if (res.status !== "true") {
            // console.log(res.message);
         } else {
            cookiesremove();
            history.push("/login")
         }
      }).catch((error) => {
         history.push("/")
      });
   }

   const open = Boolean(anchorEl);
   const id = open ? "simple-popover" : undefined;

   const cookies = new Cookies();
   const userid = cookies.get('session_userid')

   return (
      <>
         <ProSidebar
            className={isActive ? "active" : null}
            collapsed={menuCollapse}
            width={248}
            collapsedWidth={68}
         >
            <SidebarHeader>
               <Link to="/" title="SearchMirror" aria-label="SearchMirror — home">
                  <div className="logotext">
                     <div className="imgLayer">
                        <img src={LogoSymbol} alt="" width={32} height={32} style={{ margin: 'auto' }} />
                     </div>
                     <Title class="mb-0 brandWord"><span className="brandWord__s">Search</span>Mirror</Title>
                  </div>
               </Link>
            </SidebarHeader>

            {/* Global project switcher -- the active project, changeable from any
                page. It sits under the brand and above the nav, and it degrades
                to just the project mark when the rail is collapsed. */}
            <ProjectSwitcher />

            <section id="my-scrollbar">
               <SidebarContent>
                  {/* All Projects is global -- it lists and switches projects --
                      so it sits directly under the switcher as a standalone,
                      always-visible entry rather than inside a collapsible
                      section. */}
                  <Menu iconShape="square" aria-label="Projects">
                     <NavLinks items={NAV_ITEMS.projects} activeMenu={activeMenu} teamModules={props.teamModules} />
                  </Menu>

                  {/* Thirteen flat entries were unscannable, so the rail is
                      sectioned. Each group is its own <Menu>, which renders a
                      <nav><ul>; a heading cannot live inside the <ul> without
                      producing invalid markup, so it sits between them and the
                      <nav> carries the same name as its accessible label.
                      The heading is also the disclosure that opens the group --
                      see NAV_GROUPS -- so the whole rail fits a laptop without
                      a scrollbar. */}
                  {visibleNavItems(NAV_ITEMS.tracking, props.teamModules).length ? <>
                     <RailGroupToggle group={NAV_GROUPS[0]} open={openGroups.tracking} first onToggle={toggleGroup} />
                     <Menu
                        iconShape="square"
                        aria-label="Tracking"
                        id="railSection-tracking"
                        className={openGroups.tracking ? "railSection is-open" : "railSection"}
                     >
                        <NavLinks items={NAV_ITEMS.tracking} activeMenu={activeMenu} teamModules={props.teamModules} />
                     </Menu>
                  </> : null}

                  {visibleNavItems(NAV_ITEMS.content, props.teamModules).length ? <>
                     <RailGroupToggle group={NAV_GROUPS[1]} open={openGroups.content} onToggle={toggleGroup} />
                     <Menu
                        iconShape="square"
                        aria-label="Content"
                        id="railSection-content"
                        className={openGroups.content ? "railSection is-open" : "railSection"}
                     >
                        <NavLinks items={NAV_ITEMS.content} activeMenu={activeMenu} teamModules={props.teamModules} />
                     </Menu>
                  </> : null}

                  {visibleNavItems(NAV_ITEMS.insights, props.teamModules).length ? <>
                     <RailGroupToggle group={NAV_GROUPS[2]} open={openGroups.insights} onToggle={toggleGroup} />
                     <Menu
                        iconShape="square"
                        aria-label="Insights"
                        id="railSection-insights"
                        className={openGroups.insights ? "railSection is-open" : "railSection"}
                     >
                        <NavLinks items={NAV_ITEMS.insights} activeMenu={activeMenu} teamModules={props.teamModules} />
                     </Menu>
                  </> : null}

                  {/* Reports is client-visible, so it cannot live inside the gated
                      Insights <Menu> -- hiding that group took Reports with it. */}
                  {visibleNavItems(NAV_ITEMS.reports, props.teamModules).length ? <Menu iconShape="square" aria-label="Reports">
                     <NavLinks items={NAV_ITEMS.reports} activeMenu={activeMenu} teamModules={props.teamModules} />
                  </Menu> : null}

                  {/* Settings is the only entry the old "Account" section held,
                      and a disclosure over one item is a control that earns
                      nothing. It is a pinned tail instead, hairlined off the
                      sections above it and reading as part of the account row
                      it sits on top of. */}
                  {visibleNavItems(NAV_ITEMS.account, props.teamModules).length ? <Menu iconShape="square" aria-label="Account" className="railTail">
                     <NavLinks items={NAV_ITEMS.account} activeMenu={activeMenu} teamModules={props.teamModules} />
                  </Menu> : null}
               </SidebarContent>
            </section>

            <ClickAwayListener
               mouseEvent="onMouseDown"
               touchEvent="onTouchStart"
               onClickAway={handleClickAway}
            >
               <SidebarFooter className={open ? "active" : ""}>
                  <Popover
                     className="profiltInfoBox"
                     id={id}
                     open={open}
                     anchorEl={anchorEl}
                     onClose={handleClick}
                     anchorOrigin={{
                        vertical: "bottom",
                        horizontal: "right",
                     }}
                     transformOrigin={{
                        vertical: "bottom",
                        horizontal: "left",
                     }}
                  >
                     <>
                        <div>
                           <div className="header">
                              <div className="profileImage">
                                 <div className="img f26x" aria-hidden="true">{initials(props.uname)}</div>
                              </div>
                              <div className="w-75">
                                 <Text class="m-t5 mb-0 profileName fM text-truncate text-capital">{props.uname}</Text>
                                 <SmallText class="m-t5 m-b0 text-truncate">{props.uemail}</SmallText>
                                 {/*<span className="primaryTag">UPGRADE 1</span>*/}
                              </div>

                           </div>
                           <div className="bottom"></div>
                           <MenuList className="serpMenu p-t5">
                              {/* Account, Profile, API Key, AI Keys and Members
                                  are all reachable from the rail's "Settings"
                                  tab, so this menu carries only Logout -- the one
                                  action that has no other home -- plus the way
                                  OUT of the application. Signing in used to be a
                                  one-way door: "/" redirects a signed-in user
                                  straight back into the app, so the project's
                                  own site, source and documentation were
                                  unreachable from inside it. */}
                              <MuiMenuItem
                                 className="p-r0 p-l0 submenuIcon"
                                 component="a"
                                 href={REPO_URL}
                                 target="_blank"
                                 rel="noopener noreferrer"
                              >
                                 <span className="item">Source on GitHub</span>
                              </MuiMenuItem>
                              <MuiMenuItem
                                 className="p-r0 p-l0 submenuIcon"
                                 component="a"
                                 href={DOCS_URL}
                                 target="_blank"
                                 rel="noopener noreferrer"
                              >
                                 <span className="item">Documentation</span>
                              </MuiMenuItem>
                              <MenuItem className="logOutMenu p-r0 p-l0 submenuIcon" onClick={logout}>
                                 <NavLogout />
                                 <span className="item"> Logout</span>
                              </MenuItem>
                           </MenuList>
                        </div>
                     </>
                  </Popover>

                  <Button
                     disableRipple={true}
                     className="profileButton p-0"
                     title={`${props.uname} — account menu`}
                     aria-label={`${props.uname} — account menu`}
                     aria-haspopup="menu"
                     aria-expanded={open}
                     aria-describedby={id}
                     variant="transparent"
                     onClick={handleClick}
                  >
                     {/*Working development start */}
                     <div className="d-flex align-items-center w-100">
                        <div className="profileImage m-l10 m-r10">
                           <div className="img" aria-hidden="true">{initials(props.uname)}</div>
                        </div>

                        <div className="d-flex align-items-center justify-content-between">
                           <div className="overflow-hidden profile">
                              <div className="d-flex align-items-center gap-2 ">
                                 <Text class="mb-0 profileName text-truncate text-capital">
                                    {props.uname}
                                 </Text>
                              </div>
                              <div className="d-flex align-items-center">
                                 <SmallText class="mb-0">View my profile</SmallText>
                              </div>

                           </div>

                           <span className="mx-2 d-flex">
                              <NavChevron className="submenuChevron" />
                           </span>
                        </div>
                     </div>
                     {/*Working development End */}
                  </Button>
               </SidebarFooter>
            </ClickAwayListener>
         </ProSidebar>

         {/* The collapse control. A sibling of the rail rather than a child of
             it: `position: fixed` off `--rail-w` means it tracks the rail's
             edge without depending on react-pro-sidebar's overflow handling,
             and it is reachable in both states. */}
         <button
            type="button"
            className="railToggle"
            onClick={toggleRail}
            title={menuCollapse ? "Expand sidebar" : "Collapse sidebar"}
            aria-label={menuCollapse ? "Expand sidebar" : "Collapse sidebar"}
            aria-expanded={!menuCollapse}
         >
            <NavChevron />
         </button>

         {/* The top bar. It exists to close the shell's grid: the rail's logo
             block and this bar are the same height and both end on the same
             hairline, so the seam runs unbroken across the top of the app
             instead of the rail's header stopping at an arbitrary edge.
             Its content shares --page-max and the canvas gutter, so the
             greeting starts on the same left axis as every page title.

             The name is the session_username cookie, handed down by
             private_route.js as `uname` -- the same value the account row
             below already renders. Nothing here calls the API. */}
         <header className="appBar">
            <div className="appBar__inner">
               <p className="appBar__hello">
                  {greeting.part}
                  {greeting.name ? <>, <span className="appBar__name">{greeting.name}</span></> : null}
               </p>
               <p className="appBar__date">
                  {new Date().toLocaleDateString(undefined, {
                     weekday: "long", month: "long", day: "numeric",
                  })}
               </p>
            </div>
         </header>

         {children}
      </>
   );
}
// DESKTOP SIDEBAR OPTIONS - ENDS

// MOBILE OR RESPONSIVE SIDEBAR - STARTS
export function MobSidebar({ children, ...props }) {
   const [open, setOpen] = React.useState(false);
   const [accountAnchor, setAccountAnchor] = React.useState(null);
   const location = useLocation();
   var { pathname } = location;
   var splitLocation = pathname.split("/");
   var activeMenu = splitLocation.length > 1 ? splitLocation[1] : "";

   useEffect(() => {
      setOpen(false);
   }, [location])

   const toggleDrawer = (event) => {
      if (
         event.type === "keydown" &&
         (event.key === "Tab" || event.key === "Shift")
      ) {
         return;
      }

      setOpen(!open);
   };

   const history = useHistory();

   const openAccountMenu = (event) => {
      setAccountAnchor(event.currentTarget);
   };

   const closeAccountMenu = () => {
      setAccountAnchor(null);
   };

   const viewProfile = () => {
      closeAccountMenu();
      setOpen(false);
      history.push("/settings/profile");
   };

   const logout = () => {
      closeAccountMenu();
      const cookies = new Cookies();
      const userid = cookies.get('session_userid');
      // const usertoken = cookies.get('session_token');

      const data = {
         'userid': userid,
      };

      axios.post(global.apiurl + '/last_logout', data, {
         headers: { 'Authorization': global.token }
      }).then(response => {
         return response.data;
      }).then(res => {
         if (res.status !== "true") {
            // console.log(res.message);
         } else {
            cookiesremove();
            history.push("/login")
         }
      }).catch((error) => {
         history.push("/")
      });
   }

   const accountMenuOpen = Boolean(accountAnchor);
   const accountMenuId = accountMenuOpen ? "mobile-account-menu" : undefined;

   const accountButton = () => (
      <Button
         className="mobileProfileButton"
         title={`${displayName(props.uname)} account menu`}
         aria-label={`${displayName(props.uname)} account menu`}
         aria-controls={accountMenuId}
         aria-haspopup="menu"
         aria-expanded={accountMenuOpen}
         onClick={openAccountMenu}
      >
         <span className="profileImage" aria-hidden="true">
            <span className="img">{initials(props.uname)}</span>
         </span>
      </Button>
   );

   return (
      <>
         <Box className="mobileHeader">
            <Link className="mobileBrand" to="/dashboard" aria-label="SearchMirror home">
               <img src={LogoSymbol} alt="" width={28} height={28} />
               <span className="mobileBrand__word">SearchMirror</span>
            </Link>
            <div className="mobileHeader__actions">
               <AppIconButton
                  class="onlyIcon"
                  color="inherit"
                  aria-label="Open menu"
                  edge="start"
                  onclick={toggleDrawer}
                  Icon={<img src={MenuIcon} alt="" />}
               />
               {accountButton()}
            </div>
         </Box>

         <Drawer
            className="customDrawer"
            anchor="left"
            open={open}
            onClose={toggleDrawer}
         >

            <Box className="mobileDrawerHeader">
               <Link className="mobileBrand" to="/dashboard" aria-label="SearchMirror home">
                  <img src={LogoSymbol} alt="" width={28} height={28} />
                  <span className="mobileBrand__word">SearchMirror</span>
               </Link>

               <div className="mobileHeader__actions">
                  {accountButton()}
                  <AppIconButton
                     class="onlyIcon"
                     color="inherit"
                     aria-label="Close menu"
                     edge="start"
                     onclick={toggleDrawer}
                     Icon={<img src={CloseIcon} alt="" width={15} />}
                  />
               </div>
            </Box>

            <div className="mobSidebar">
               <ProjectSwitcher />
               <SidebarContent>
                  {/* All Projects is global, so it leads the drawer as a
                      standalone entry above the first section -- the same place
                      it holds in the rail. */}
                  <Menu iconShape="square" aria-label="Projects">
                     <NavLinks items={NAV_ITEMS.projects} activeMenu={activeMenu} teamModules={props.teamModules} />
                  </Menu>

                  {/* Same five sections as the desktop rail, in the same order,
                      so the two navigations are one map rather than two. */}
                  {visibleNavItems(NAV_ITEMS.tracking, props.teamModules).length ? <>
                     <RailGroup label="Tracking" first />
                     <Menu iconShape="square" aria-label="Tracking">
                        <NavLinks items={NAV_ITEMS.tracking} activeMenu={activeMenu} teamModules={props.teamModules} />
                     </Menu>
                  </> : null}

                  {visibleNavItems(NAV_ITEMS.content, props.teamModules).length ? <>
                     <RailGroup label="Content" />
                     <Menu iconShape="square" aria-label="Content">
                        <NavLinks items={NAV_ITEMS.content} activeMenu={activeMenu} teamModules={props.teamModules} />
                     </Menu>
                  </> : null}

                  {(visibleNavItems(NAV_ITEMS.insights, props.teamModules).length || visibleNavItems(NAV_ITEMS.reports, props.teamModules).length) ? <>
                     <RailGroup label="Insights" />
                     <Menu iconShape="square" aria-label="Insights">
                        <NavLinks items={NAV_ITEMS.insights} activeMenu={activeMenu} teamModules={props.teamModules} />
                        <NavLinks items={NAV_ITEMS.reports} activeMenu={activeMenu} teamModules={props.teamModules} />
                     </Menu>
                  </> : null}

                  {visibleNavItems(NAV_ITEMS.account, props.teamModules).length ? <>
                     <RailGroup label="Account" />
                     <Menu iconShape="square" aria-label="Account">
                        <NavLinks items={NAV_ITEMS.account} activeMenu={activeMenu} teamModules={props.teamModules} />
                     </Menu>
                  </> : null}
               </SidebarContent>
            </div>
         </Drawer>

         <Popover
            className="profiltInfoBox mobileAccountPopover"
            id={accountMenuId}
            open={accountMenuOpen}
            anchorEl={accountAnchor}
            onClose={closeAccountMenu}
            anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
            transformOrigin={{ vertical: "top", horizontal: "right" }}
         >
            <div className="mobileAccountMenu">
               <div className="header">
                  <div className="profileImage">
                     <div className="img f26x" aria-hidden="true">{initials(props.uname)}</div>
                  </div>
                  <div className="mobileAccountMenu__identity">
                     <Text class="mb-0 profileName text-truncate text-capital">{props.uname}</Text>
                     <SmallText class="mb-0 text-truncate">{props.uemail}</SmallText>
                  </div>
               </div>
               <MenuList aria-label="Account actions">
                  <MenuItem onClick={viewProfile}>
                     <NavSettings />
                     <span className="item">View profile</span>
                  </MenuItem>
                  <MenuItem className="logOutMenu" onClick={logout}>
                     <NavLogout />
                     <span className="item">Log out</span>
                  </MenuItem>
               </MenuList>
            </div>
         </Popover>
         {children}
      </>
   );
}
// MOBILE OR RESPONSIVE SIDEBAR - ENDS
