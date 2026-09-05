import React from "react";

/* "know more" and similar outbound links.

   The addresses these render live in src/index.js and default to empty: there
   is no SearchMirror marketing site, and the ones that used to be hardcoded all
   pointed at tracker.example, which does not resolve. An <a> with an empty href
   is worse than no link -- it reloads the page the reader is already on -- so
   the link is only rendered when an operator has actually configured somewhere
   to send people.

   Call sites keep their own copy and classes; this only decides whether the
   anchor exists. */
export function KnowMore({ href, className, children }) {
   if (!href) return null;

   return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
         {children || "know more"}
      </a>
   );
}

export default KnowMore;
