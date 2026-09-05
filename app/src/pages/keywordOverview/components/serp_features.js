import React, { useState } from "react";
import { Link } from "react-router-dom";

import { Tsk } from "../../commonComponents/parts";
import { plainText, safeHref } from "../../../utils/provider_text";

/* Keyword.serp_features, written by the engine's extract_serp_features and
   carried as `sf`, with `sfm` saying whether it was ever written.

   Three facts that all used to render as the same "0" are kept apart here:
   measured-and-none, not-requested-at-this-depth, and never-measured. Only the
   first is ever a number, and only it gets a word; the other two say in as many
   words that nothing was measured. */

const BLOCKS = [
   { key: "featured_snippet", label: "Featured snippet" },
   { key: "ads", label: "Ads" },
   { key: "people_also_ask", label: "People also ask" },
   { key: "local_results", label: "Local pack" },
   { key: "knowledge_panel", label: "Knowledge panel" },
   { key: "videos", label: "Videos" },
   { key: "related_searches", label: "Related searches" },
];

const readBlock = (block) => {
   if (!block || typeof block !== "object" || !block.state) {
      return { value: "—", tone: "unknown", note: "Not recorded", title: "" };
   }

   if (block.state === "present") {
      return {
         value: typeof block.count === "number" ? String(block.count) : "Present",
         tone: "present",
         note: "",
         title: "",
      };
   }

   if (block.state === "absent") {
      // reported:false means the provider omitted the key rather than sending
      // it empty. Both are the same answer -- no such block on this SERP -- so
      // the difference is provenance and rides on the title, not on the row.
      return {
         value: "None",
         tone: "absent",
         note: "",
         title: block.reported === false
            ? "The provider omitted this block rather than sending it empty. Both mean the SERP had none."
            : "",
      };
   }

   if (block.state === "unavailable") {
      return { value: "Not checked", tone: "unknown", note: "", title: "" };
   }

   return { value: "—", tone: "unknown", note: "Not recorded", title: "" };
};

/* The AI Overview's state, as a phrase rather than a figure.

   `reported` is deliberately not read. For this block the engine sets it from
   `"ai_overview" in bsoup`, and DataBlue omits the key whenever Google showed
   no AI answer -- the 3 Sep run returned the block for 4 keywords and omitted
   it for 26 in the same batch at the same depth. So on an Advanced run an
   absence is a measurement, and the old "the provider did not send the field"
   reading told 26 of 30 keywords a story that was not true. */
const readAiOverview = (ai, mode) => {
   if (!ai || typeof ai !== "object" || !ai.state) {
      return { tone: "unknown", label: "Not recorded", aside: "none" };
   }

   if (ai.state === "present") {
      // The answer text below already proves an AI Overview ran, so the chip
      // spends its width on the fact the reader came for: are they in it.
      return ai.owned === true
         ? { tone: "owned", label: "You are cited", aside: "" }
         : { tone: "shown", label: "Not cited", aside: "" };
   }

   if (ai.state === "absent") {
      return { tone: "absent", label: "No AI Overview", aside: "absent" };
   }

   if (ai.state === "unavailable") {
      // Set whenever the run was not Advanced, which is either Lite or a depth
      // the provider never echoed. Neither looked, so neither is a "no".
      return { tone: "unknown", label: "Not measured", aside: mode === "lite" ? "lite" : "depth" };
   }

   return { tone: "unknown", label: "Not recorded", aside: "none" };
};

// Cited sites, normalised. `owned` repeats the comparison the engine makes when
// it sets ai_overview.owned, because sources[] does not carry the flag.
const readSources = (ai, target) => {
   const raw = ai && Array.isArray(ai.sources) ? ai.sources : [];
   return raw
      .map((source) => {
         if (!source || typeof source !== "object") {
            return null;
         }
         const domain = plainText(source.domain);
         const href = safeHref(source.link);
         if (!domain && !href) {
            return null;
         }
         return {
            domain: domain || href,
            title: plainText(source.title),
            href: href,
            owned: Boolean(domain) && Boolean(target) && domain === target,
         };
      })
      .filter(Boolean);
};

const adPlacement = (block) => {
   if (!block || block.state !== "present") {
      return "";
   }
   const parts = [];
   if (block.top_count) {
      parts.push(block.top_count + " above results");
   }
   if (block.bottom_count) {
      parts.push(block.bottom_count + " below results");
   }
   // Never folded into top_count: an unplaced ad is reported as unplaced.
   if (block.unknown_slot_count) {
      parts.push(block.unknown_slot_count + " placement not reported");
   }
   return parts.join(" · ");
};

/* One recorded entry out of a feature block, normalised for display.

   `title` is what the block showed. Rows written before the extraction was
   widened have it empty -- related searches kept only a google.<tld> redirect
   URL -- so the label falls back to the domain and then to the link. An entry
   with none of the three is not worth a row and is dropped. */
const readEntry = (item, target) => {
   if (!item || typeof item !== "object") return null;
   const title = plainText(item.title);
   const domain = plainText(item.domain);
   const href = safeHref(item.link);
   const label = title || domain || href;
   if (!label) return null;
   return {
      label: label,
      // Only a second line when it says something the label does not.
      sub: title && domain && title !== domain ? domain : "",
      desc: plainText(item.desc),
      href: href,
      owned: item.owned === true || (Boolean(domain) && Boolean(target) && domain === target),
   };
};

const FeatureRow = ({ label, block, extra, target }) => {
   const [open, setOpen] = useState(false);
   const read = readBlock(block);
   const owned = block && block.owned === true;

   const entries = (block && Array.isArray(block.items) ? block.items : [])
      .map((item) => readEntry(item, target))
      .filter(Boolean);

   /* Expandable only when there is something behind it. A block can be
      measured as present and still carry no retained entries -- the record is
      a daily summary, not an archive -- and an expander that opens on nothing
      is worse than no expander. */
   const expandable = read.tone === "present" && entries.length > 0;
   const found = block && typeof block.count === "number" ? block.count : entries.length;
   const capped = found > entries.length;

   return (
      <div className={"sfRow" + (expandable ? " sfRow--expandable" : "")}>
         <div className="sfRowHead">
            {expandable ? (
               <button
                  type="button"
                  className="sfRowToggle"
                  aria-expanded={open}
                  onClick={() => setOpen(!open)}
               >
                  <span className="sfRowCaret" aria-hidden="true">{open ? "−" : "+"}</span>
                  <span className="sfRowLabel">{label}</span>
               </button>
            ) : (
               <div className="sfRowLabel">{label}</div>
            )}
            <div className={"sfRowValue sfTone-" + read.tone} title={read.title || undefined}>
               <span className="sfRowFigure">{read.value}</span>
               {owned ? <span className="sfRowOwned">yours</span> : null}
               {read.note ? <span className="sfRowNote">{read.note}</span> : null}
               {extra ? <span className="sfRowNote">{extra}</span> : null}
               {read.tone === "present" && entries.length === 0 ? (
                  <span className="sfRowNote">no detail retained</span>
               ) : null}
            </div>
         </div>

         {expandable && open ? (
            <div className="sfRowDetail">
               <ul className="sfEntryList">
                  {entries.map((entry, index) => (
                     <li className={"sfEntry" + (entry.owned ? " sfEntry--owned" : "")} key={index.toString()}>
                        <div className="sfEntryHead">
                           {entry.href ? (
                              <a className="sfEntryLink" href={entry.href} target="_blank" rel="noopener noreferrer nofollow">
                                 {entry.label}
                              </a>
                           ) : (
                              <span className="sfEntryLink">{entry.label}</span>
                           )}
                           {entry.owned ? <span className="sfRowOwned">yours</span> : null}
                        </div>
                        {entry.sub ? <div className="sfEntrySub">{entry.sub}</div> : null}
                        {entry.desc ? <p className="sfEntryDesc">{entry.desc}</p> : null}
                     </li>
                  ))}
               </ul>
               {capped ? (
                  <p className="sfEntryCap">
                     {"Showing " + entries.length + " of " + found + " — the daily record keeps the first ten."}
                  </p>
               ) : null}
            </div>
         ) : null}
      </div>
   );
};

/* The GEO half of the product in one block: what Google's AI answer says, and
   which sites it credits for saying it. The answer runs past a thousand
   characters, so it is clamped until asked for -- it must not push the ladder
   of feature counts off the panel. */
const AiOverview = ({ ai, mode, target }) => {
   const [answerOpen, setAnswerOpen] = useState(false);
   const [sourcesOpen, setSourcesOpen] = useState(false);

   const read = readAiOverview(ai, mode);
   const answer = plainText(ai && ai.raw ? ai.raw.content : "");
   const sources = readSources(ai, target);
   /* TWO controls, because there are two things to reveal.

      One button used to do both jobs, and it sat BELOW the sources list --
      three or four rows from the paragraph it expanded. With a long answer and
      extra sources it read "Show the full answer" while expanding both, so the
      reader could not predict what it would do or find it where they were
      looking. Each control now sits with the thing it changes and moves only
      that. */
   const SOURCES_SHOWN = 3;
   const shown = sourcesOpen ? sources : sources.slice(0, SOURCES_SHOWN);
   // Below the clamp there is nothing to reveal, so the control would lie.
   const clampable = answer.length > 300;
   const moreSources = sources.length > SOURCES_SHOWN;

   return (
      <section className="sfAi">
         <div className="sfAiHead">
            <h3 className="sfAiTitle">AI Overview</h3>
            <span className={"sfAiState sfAiState--" + read.tone}>{read.label}</span>
         </div>

         {answer ? (
            <p className={"sfAiAnswer" + (clampable && !answerOpen ? " sfAiAnswer--clamp" : "")}>{answer}</p>
         ) : null}

         {/* Immediately after the paragraph, with nothing between them. */}
         {answer && clampable ? (
            <button
               type="button"
               className="sfAiToggle"
               aria-expanded={answerOpen}
               onClick={() => setAnswerOpen(!answerOpen)}
            >
               {answerOpen ? "Show less of the answer" : "Show the full answer"}
            </button>
         ) : null}

         {sources.length > 0 ? (
            <div className="sfAiSources">
               <p className="sfAiSourcesLabel">
                  {"Cited " + (sources.length === 1 ? "source" : "sources") + " (" + sources.length + ")"}
               </p>
               <ul className="sfAiSourceList">
                  {shown.map((source, index) => (
                     <li className={"sfAiSource" + (source.owned ? " sfAiSource--owned" : "")} key={index.toString()}>
                        {source.href ? (
                           <a className="sfAiSourceLink" href={source.href} target="_blank" rel="noopener noreferrer nofollow">
                              {source.domain}
                           </a>
                        ) : (
                           <span className="sfAiSourceLink">{source.domain}</span>
                        )}
                        {source.owned ? <span className="sfRowOwned">yours</span> : null}
                        {source.title ? <span className="sfAiSourceTitle">{source.title}</span> : null}
                     </li>
                  ))}
               </ul>

               {/* Its own control, inside the sources block. */}
               {moreSources ? (
                  <button
                     type="button"
                     className="sfAiToggle"
                     aria-expanded={sourcesOpen}
                     onClick={() => setSourcesOpen(!sourcesOpen)}
                  >
                     {sourcesOpen
                        ? "Show fewer sources"
                        : "Show all " + sources.length + " sources"}
                  </button>
               ) : null}
            </div>
         ) : null}

         {read.aside === "absent" ? (
            <p className="sfAside">
               Google returned no AI Overview for this search, so there is nothing to be cited
               in. This is a measured result, not a gap in the data.
            </p>
         ) : null}

         {read.aside === "lite" ? (
            <p className="sfAside">
               This run did not ask for the AI Overview — only Advanced depth does. It was
               never looked for, so this is not a "no".{" "}
               <Link className="sfLink" to="/settings/apikey">Set the depth</Link>.
            </p>
         ) : null}

         {read.aside === "depth" ? (
            <p className="sfAside">
               The provider did not report which depth ran, so it cannot be said whether the
               AI Overview was looked for. It is not counted either way.
            </p>
         ) : null}

         {read.aside === "none" ? (
            <p className="sfAside">
               This keyword's record carries no AI Overview state we recognise. Nothing can be
               said about it either way until the keyword is ranked again.
            </p>
         ) : null}
      </section>
   );
};

export default function SerpFeatures({ kwdata }) {
   const loaded = Boolean(kwdata && kwdata.KW);

   if (!loaded) {
      return (
         <div className="sfList">
            {[1, 2, 3, 4].map((i) => (
               <Tsk width={"100%"} height={20} key={i.toString()} />
            ))}
         </div>
      );
   }

   const sf = kwdata.sf;

   // An absent field is not an unmeasured keyword: one says the record is
   // empty, the other says nobody sent the record.
   if (sf === undefined || sf === null) {
      return (
         <p className="kwEmpty">
            No feature record came back for this keyword, so nothing can be said about its
            SERP features either way. Reload the page to try again.
         </p>
      );
   }

   const blocks = (sf && sf.blocks) || {};
   const measured = kwdata.sfm === true || Object.keys(sf).length > 0;

   if (!measured) {
      return (
         <p className="kwEmpty">
            Not measured yet. SERP features are recorded the next time this keyword is ranked
            — this is not the same as the SERP having none.
         </p>
      );
   }

   const mode = sf.mode === "advanced" ? "Advanced" : sf.mode === "lite" ? "Lite" : "";
   const measuredAt = plainText(sf.measured_at).slice(0, 16);

   return (
      <>
         <AiOverview ai={sf.ai_overview} mode={sf.mode} target={plainText(sf.target)} />

         <div className="sfList">
            {BLOCKS.map((b) => (
               <FeatureRow
                  key={b.key}
                  label={b.label}
                  block={blocks[b.key]}
                  target={plainText(sf.target)}
                  extra={b.key === "ads" ? adPlacement(blocks[b.key]) : ""}
               />
            ))}
         </div>

         <p className="sfFoot">
            Feature blocks are counted apart from the organic ladder — an ad is an ad and is
            never a rank.
            {mode ? " Measured at " + mode + " depth." : ""}
            {measuredAt ? " Last measured " + measuredAt + "." : ""}
         </p>
      </>
   );
}
