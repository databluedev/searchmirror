import React from "react";

/* A feature that is planned but cannot be connected yet.

   There were two different treatments for the same fact. Add Project hid the
   Google section entirely when no OAuth client id was configured, so a user
   never learned it was coming. Project Settings showed a card telling THE USER
   to "register a Google OAuth client of your own, then set VITE_GSC_CLIENT_ID
   and VITE_GSC_SECRET and rebuild" -- an operator's job, in an end user's
   screen, naming environment variables at somebody who has no shell.

   One treatment, used in both places: visible so people know it is coming,
   inert so nothing can be clicked into a half-working flow, and silent about
   configuration. How to enable it belongs in docs/DEPLOYMENT.md, where the
   person who can do it is reading.

   Google Search Console and Analytics are parked for a real reason, not an
   arbitrary one: the OAuth exchange needs a server-side flow, and doing it in
   browser code would put the client secret in the bundle. */

export default function ComingSoon({ title, children, className }) {
   return (
      <section className={"comingSoon" + (className ? " " + className : "")}>
         <div className="comingSoon__head">
            <h2 className="comingSoon__title">{title}</h2>
            <span className="comingSoon__badge">Coming soon</span>
         </div>
         {children ? <p className="comingSoon__body">{children}</p> : null}
      </section>
   );
}
