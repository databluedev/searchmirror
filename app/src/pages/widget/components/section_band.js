import React from "react";
import { NavGlobe, NavSearch } from "../../commonComponents/railIcons";

/* WHICH MEASUREMENT SYSTEM A FIGURE BELONGS TO.

   This screen reports two of them, and until this band existed it reported
   them as one undifferentiated stack of panels:

     SEO -- organic positions on Google, fetched by the DataBlue SERP API on
            the daily ranking run, billed per page per keyword against the
            account's SERP key.
     GEO -- whether AI assistants name this domain when they answer the
            project's prompts, collected by Geo Citations against the account's
            AI provider keys.

   Different source, different cost, different refresh path, different meaning.
   A reader who takes one for the other draws a wrong conclusion from a correct
   number, and the words collide at exactly the wrong place: "visibility" is the
   name of the rank-derived score on this page AND the category's usual name for
   the AI figure. Nothing on the screen said which was which. That is issue F1.

   WHY A BAND AND NOT A TINT
   -------------------------
   docs/DESIGN.md gives every colour a job already -- --up/--down are rank
   direction, --accent is "act on this", --nav-accent is "you are here" -- and
   none of them means "this came from a different source". Inventing a system
   colour would either steal one of those meanings or add a fourth palette to a
   monochrome product. It would also fail on its own for anyone with a colour
   vision deficiency, which is the case the rule exists for.

   So the distinction is carried by four things, none of which is colour:
     the mark      -- a magnifier for search results, a globe for Geo Citations
     the name      -- "Search rankings" / "AI answers", in ink at card-title
                      size, one step above the panel micro-labels beneath it
     the tag       -- the literal "SEO" / "GEO", because that is the vocabulary
                      the question was asked in
     the sentence  -- what was measured and what measured it

   THE MARKS ARE THE RAIL'S, ON PURPOSE
   ------------------------------------
   Both come from commonComponents/railIcons.js rather than dash_icons.js, and
   that is the meaning rather than a shortcut: the globe here is the same glyph
   the rail draws beside "Geo Citations", which is where this section's figure
   is produced and where its link goes. The reader who wonders where the number
   came from has the answer in their peripheral vision. The magnifier is the
   rail family's search mark, unused elsewhere in the shell today (Keyword
   Research is unrouted), so it carries no second meaning to collide with.

   One family, one geometry: 24-unit grid drawn at 18px, 1.5px stroke,
   currentColor, no fill -- docs/DESIGN.md "Non-negotiable" #2. Do not mix in a
   16px dash_icons mark here; they are a different grid and would read as a
   different weight at this size.

   Nothing here spends the account's credits and nothing here is a control. The
   band is a label. */

const SYSTEMS = {
   /* "on the daily ranking run" and not "daily": the run is what refreshes
      these figures, and the header above already prints when it last happened
      and when it is next due. Naming the SERP API is what separates the cost
      of this section from the section below it. */
   seo: {
      Mark: NavSearch,
      name: "Search rankings",
      tag: "SEO",
      source:
         "Positions in Google's organic results, collected by the DataBlue SERP API on the daily ranking run.",
   },
   /* No refresh cadence stated, because there is not one to state: Geo answers
      are collected both by the scheduler picking up queued prompts and by a
      person running an analysis, so any single word here would be wrong on half
      the installs. What IS stated is the pair that actually distinguishes this
      section -- the models answer, and the account's own AI keys pay. */
   geo: {
      Mark: NavGlobe,
      name: "AI answers",
      tag: "GEO",
      source:
         "Mentions in the answers AI assistants give, collected by Geo Citations on your AI provider keys.",
   },
};

/* One section of the page: the band, then whatever the section reports.

   `aria-labelledby` rather than `aria-label` so the heading and the accessible
   name cannot drift apart, and so the band's <h2> is what a screen reader lands
   on when it walks the page's headings -- panel labels inside are <h3>, which
   is what makes the nesting audible as well as visible. */
export default function Section({ system, children }) {
   const { Mark, name, tag, source } = SYSTEMS[system];
   const headingId = "dashSystem-" + system;

   return (
      <section className="dashSection" aria-labelledby={headingId}>
         <div className="dashSystem">
            <span className="dashSystem__mark">
               <Mark />
            </span>
            <h2 className="dashSystem__name" id={headingId}>
               {name}
               {/* Inside the heading, so the acronym is part of the accessible
                   name: "Search rankings SEO" is how the question was asked. */}
               <span className="dashSystem__tag">{tag}</span>
            </h2>
            <p className="dashSystem__source">{source}</p>
         </div>
         {children}
      </section>
   );
}
