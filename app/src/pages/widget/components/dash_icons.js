import React from "react";

/* The dashboard's marks. SVG, 1.5px stroke, currentColor, so a mark takes its
   meaning from the token on the element that holds it and never carries a
   colour of its own (docs/DESIGN.md, "Non-negotiable" #2).

   aria-hidden on all of them: every one sits beside text that already says the
   same thing, so announcing it twice is noise. */

const base = {
   width: 16,
   height: 16,
   viewBox: "0 0 16 16",
   fill: "none",
   stroke: "currentColor",
   strokeWidth: 1.5,
   strokeLinecap: "round",
   strokeLinejoin: "round",
   "aria-hidden": "true",
   focusable: "false",
};

export const DownMark = () => (
   <svg {...base}>
      <path d="M8 3v10" />
      <path d="M4 9.5 8 13.5l4-4" />
   </svg>
);

export const UpMark = () => (
   <svg {...base}>
      <path d="M8 13V3" />
      <path d="M4 6.5 8 2.5l4 4" />
   </svg>
);

export const FlatMark = () => (
   <svg {...base}>
      <path d="M3 8h10" />
   </svg>
);

/* Cannibalisation: two of your own pages competing for one query. */
export const FlagMark = () => (
   <svg {...base}>
      <path d="M4 14V2.5" />
      <path d="M4 3h7.5l-1.5 2.5L11.5 8H4" />
   </svg>
);

/* Never ranked: an outline, because there is nothing in it. */
export const HollowMark = () => (
   <svg {...base}>
      <circle cx="8" cy="8" r="4.75" />
   </svg>
);

export const WarnMark = () => (
   <svg {...base}>
      <path d="M8 2.75 14.25 13.25H1.75Z" />
      <path d="M8 6.75v3" />
      <path d="M8 11.5h.01" />
   </svg>
);

export const InfoMark = () => (
   <svg {...base}>
      <circle cx="8" cy="8" r="5.75" />
      <path d="M8 7.25v3.5" />
      <path d="M8 5.25h.01" />
   </svg>
);

export const ExternalMark = () => (
   <svg {...base} width="12" height="12">
      <path d="M9.5 2.5H13.5V6.5" />
      <path d="M13.5 2.5 7.5 8.5" />
      <path d="M12 9.5v3a1 1 0 0 1-1 1H3.5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h3" />
   </svg>
);
