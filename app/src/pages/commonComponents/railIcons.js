import React from "react";

/*
 * Rail icon family — docs/DESIGN.md, "Non-negotiable" #2.
 *
 * One geometry for every mark in the left rail and its footer menu: a 24-unit
 * grid drawn at 18px, 1.5px stroke, round caps and joins, `currentColor`, no
 * fills. Colour is inherited from the menu item, so the active and hover states
 * are a single `color` change instead of a second image swapped in on top.
 *
 * This replaces the previous set, which mixed filled 18x18 exports, a 100x100
 * stroke-10 magnifier and a 60-unit robot head, each with its own baked-in hex.
 */

function Icon({ children, className, ...rest }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      className={className ? `railIcon ${className}` : "railIcon"}
      {...rest}
    >
      {children}
    </svg>
  );
}

// All Projects — stacked plates
export const NavProjects = (props) => (
  <Icon {...props}>
    <path d="M12 3 3 7.5l9 4.5 9-4.5L12 3Z" />
    <path d="M3 16.5 12 21l9-4.5" />
    <path d="M3 12 12 16.5 21 12" />
  </Icon>
);

// Dashboard — four panes
export const NavDashboard = (props) => (
  <Icon {...props}>
    <rect x="3" y="3" width="7.5" height="7.5" rx="1.5" />
    <rect x="13.5" y="3" width="7.5" height="7.5" rx="1.5" />
    <rect x="3" y="13.5" width="7.5" height="7.5" rx="1.5" />
    <rect x="13.5" y="13.5" width="7.5" height="7.5" rx="1.5" />
  </Icon>
);

// Keywords — ranked bars
export const NavKeywords = (props) => (
  <Icon {...props}>
    <path d="M3.5 20.5h17" />
    <path d="M7 20.5v-6" />
    <path d="M12 20.5V8" />
    <path d="M17 20.5v-9" />
  </Icon>
);

// Content Audit — document with a check
export const NavAudit = (props) => (
  <Icon {...props}>
    <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z" />
    <path d="M14 3v5h5" />
    <path d="m9 14.5 2 2 4-4" />
  </Icon>
);

// Content Gap — two columns with the gap between them
export const NavGap = (props) => (
  <Icon {...props}>
    <rect x="3" y="4" width="6.5" height="16" rx="1.5" />
    <rect x="14.5" y="4" width="6.5" height="16" rx="1.5" />
    <path d="M12 9v6" />
  </Icon>
);

// Content Planner — calendar
export const NavPlanner = (props) => (
  <Icon {...props}>
    <rect x="3" y="5" width="18" height="16" rx="2" />
    <path d="M3 10h18" />
    <path d="M8 3v4" />
    <path d="M16 3v4" />
  </Icon>
);

// Geo Citations — globe
export const NavGlobe = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="M3 12h18" />
    <path d="M12 3a13.5 13.5 0 0 1 0 18 13.5 13.5 0 0 1 0-18Z" />
  </Icon>
);

// Competitor AI — spark (replaces the robot head)
export const NavSpark = (props) => (
  <Icon {...props}>
    <path d="M11 3.5 12.7 8 17 9.75 12.7 11.5 11 16 9.3 11.5 5 9.75 9.3 8 11 3.5Z" />
    <path d="M17.5 15 18.4 17.1 20.5 18 18.4 18.9 17.5 21 16.6 18.9 14.5 18 16.6 17.1 17.5 15Z" />
  </Icon>
);

// Keyword Research — magnifier
export const NavSearch = (props) => (
  <Icon {...props}>
    <circle cx="10.5" cy="10.5" r="6.5" />
    <path d="m15.5 15.5 4.5 4.5" />
  </Icon>
);

// Enterprise Keyword Navigator — compass
export const NavCompass = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="m15.5 8.5-2 5-5 2 2-5 5-2Z" />
  </Icon>
);

// Reports — document with a chart
export const NavReports = (props) => (
  <Icon {...props}>
    <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z" />
    <path d="M14 3v5h5" />
    <path d="M9 17.5v-3" />
    <path d="M12 17.5v-5.5" />
    <path d="M15 17.5v-2" />
  </Icon>
);

// Settings — gear
export const NavSettings = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="3" />
    <path d="M19.1 14.6a1.6 1.6 0 0 0 .3 1.8l.1.1a1.9 1.9 0 1 1-2.7 2.7l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5v.2a1.9 1.9 0 1 1-3.8 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.8.3l-.1.1a1.9 1.9 0 1 1-2.7-2.7l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3.9a1.9 1.9 0 1 1 0-3.8H4a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.8l-.1-.1a1.9 1.9 0 1 1 2.7-2.7l.1.1a1.6 1.6 0 0 0 1.8.3H9.8a1.6 1.6 0 0 0 1-1.5V3.9a1.9 1.9 0 1 1 3.8 0V4a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a1.9 1.9 0 1 1 2.7 2.7l-.1.1a1.6 1.6 0 0 0-.3 1.8v.1a1.6 1.6 0 0 0 1.5 1h.2a1.9 1.9 0 1 1 0 3.8H20a1.6 1.6 0 0 0-1.5 1Z" />
  </Icon>
);

// Account Settings — person
export const NavUser = (props) => (
  <Icon {...props}>
    <path d="M20 21v-1.5a4.5 4.5 0 0 0-4.5-4.5h-7A4.5 4.5 0 0 0 4 19.5V21" />
    <circle cx="12" cy="7.5" r="4" />
  </Icon>
);

// Profile Settings — sliders
export const NavSliders = (props) => (
  <Icon {...props}>
    <path d="M4 21v-6" />
    <path d="M4 11V3" />
    <path d="M12 21v-9" />
    <path d="M12 8V3" />
    <path d="M20 21v-5" />
    <path d="M20 12V3" />
    <path d="M2 15h4" />
    <path d="M10 8h4" />
    <path d="M18 16h4" />
  </Icon>
);

// API Key — key
export const NavKey = (props) => (
  <Icon {...props}>
    <circle cx="8" cy="16" r="4" />
    <path d="m10.8 13.2 8.2-8.2" />
    <path d="m16.5 7.5 2.5 2.5" />
    <path d="m19 5 2 2" />
  </Icon>
);

// Member Settings — people
export const NavUsers = (props) => (
  <Icon {...props}>
    <path d="M16 21v-1.5a4.5 4.5 0 0 0-4.5-4.5h-5A4.5 4.5 0 0 0 2 19.5V21" />
    <circle cx="9" cy="7.5" r="4" />
    <path d="M22 21v-1.5a4.5 4.5 0 0 0-3.5-4.4" />
    <path d="M15.5 3.8a4 4 0 0 1 0 7.5" />
  </Icon>
);

// Billing / Subscription — card
export const NavCard = (props) => (
  <Icon {...props}>
    <rect x="2.5" y="5" width="19" height="14" rx="2" />
    <path d="M2.5 10h19" />
    <path d="M6 14.5h3.5" />
  </Icon>
);

/* ---------------------------------------------------------------------------
 * The six marks below back menu entries that are parked, not dead: Rate Us,
 * Redeem, Affiliate, Feature Request, Report Bug and Roadmap are commented out
 * in sidebar.js against a future paid tier, and those blocks are the record of
 * how each was wired into the rail.
 *
 * A linter will report them as unused exports and a dead-code sweep will want
 * to prune them. Do not — restoring an entry then costs redrawing its icon, and
 * the set would no longer be one family. Kept deliberately; see the shell
 * handover notes. Everything above this line is live.
 * ------------------------------------------------------------------------- */

// Rate Us — star
export const NavStar = (props) => (
  <Icon {...props}>
    <path d="m12 3.5 2.7 5.6 6 .9-4.3 4.3 1 6.2-5.4-2.9-5.4 2.9 1-6.2L3.3 10l6-.9L12 3.5Z" />
  </Icon>
);

// Redeem — gift
export const NavGift = (props) => (
  <Icon {...props}>
    <rect x="3" y="9" width="18" height="12" rx="2" />
    <path d="M3 13.5h18" />
    <path d="M12 9v12" />
    <path d="M12 9S10.5 3.5 8 4.5 9.5 9 12 9Z" />
    <path d="M12 9s1.5-5.5 4-4.5S14.5 9 12 9Z" />
  </Icon>
);

// Affiliate — share
export const NavShare = (props) => (
  <Icon {...props}>
    <circle cx="18" cy="5.5" r="2.5" />
    <circle cx="6" cy="12" r="2.5" />
    <circle cx="18" cy="18.5" r="2.5" />
    <path d="m8.2 10.8 7.6-4.1" />
    <path d="m8.2 13.2 7.6 4.1" />
  </Icon>
);

// Feature Request — send
export const NavSend = (props) => (
  <Icon {...props}>
    <path d="M21 3 10.5 13.5" />
    <path d="M21 3 14.5 21l-4-7.5L3 9.5 21 3Z" />
  </Icon>
);

// Report Bug — alert
export const NavAlert = (props) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7.5v5" />
    <path d="M12 16.2h.01" />
  </Icon>
);

// Roadmap — route
export const NavRoute = (props) => (
  <Icon {...props}>
    <circle cx="6" cy="18" r="2.5" />
    <circle cx="18" cy="6" r="2.5" />
    <path d="M8.5 18h4.5a3.5 3.5 0 0 0 0-7h-2a3.5 3.5 0 0 1 0-7h6.5" />
  </Icon>
);

// Logout
export const NavLogout = (props) => (
  <Icon {...props}>
    <path d="M9.5 21H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3.5" />
    <path d="m16 16.5 4.5-4.5L16 7.5" />
    <path d="M20.5 12H9.5" />
  </Icon>
);

// Submenu / disclosure chevron
export const NavChevron = (props) => (
  <Icon {...props}>
    <path d="m9 5 7 7-7 7" />
  </Icon>
);
