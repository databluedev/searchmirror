import React from "react";
import { Link } from "react-router-dom";
import { Panel, PanelEmpty } from "./panel";
import { DownMark, FlagMark, HollowMark } from "./dash_icons";

/* NEEDS ATTENTION -- the things a person can do something about today.

   Three kinds of entry, and the difference between them is the whole panel.

   A GROUP is a reason counted rather than listed. The API filters `attention`
   by reason, so never-ranked keywords never arrive as rows at any count: a
   never-ranked row is the keyword's name and two zeros, which is why
   twenty-eight of them rendered as twenty-eight identical lines. One line with
   the real total and a couple of examples says more in a fortieth of the space.

   A ROW is a keyword with something specific: it fell from 5 to 6, or it has
   two of your own pages competing for it. Those never collapse, because the
   positions are the information.

   A GAP row is a keyword nobody here holds and the rival who does. This is
   where the coverage gap lives now -- it used to be half a screen arguing from
   three facts, and the same three facts read better as three lines under the
   count they belong to. Each part gets its own column: keyword, domain,
   position, hairline-separated. They were previously set as three adjacent
   inline spans and ran together as "scraper apiscraperapi.com#1", which reads
   as a mistyped domain rather than as three fields.

   Nothing appears twice: attentionView drops any group whose rows are already
   on screen. */

const MARKS = {
   dropped_top10: DownMark,
   declined: DownMark,
   cannibal: FlagMark,
   never_ranked: HollowMark,
};

/* Only the two rank-movement reasons are a direction, so only they take
   --down. Cannibalisation and "never ranked" are states, not directions, and
   colouring them red would spend the rank-direction colour on something that
   has no direction (docs/DESIGN.md, "Charts"). */
const TONE = {
   dropped_top10: "down",
   declined: "down",
   cannibal: "note",
   never_ranked: "note",
};

/* The cannibalisation note carries `pages`, so it states the actual number of
   the site's own pages competing for the query rather than "more than one".
   The field is on every row, but it is only rendered on this one: the API
   already picked the most urgent reason for the keyword, and re-surfacing the
   one it set aside would argue with that choice in the reader's face. */
const noteFor = (row) => {
   if (row.reason === "cannibal") {
      return row.pages > 1 ? row.pages + " pages competing" : "more than one page competing";
   }
   if (row.reason === "dropped_top10") return "was top 10";
   return "";
};

/* 0 is "not in the results", not position zero. */
const rank = (n) => (n > 0 ? n : "—");

/* `delta` is read, never re-derived from `from`/`to`.

   Deriving it looks safe and is not: a keyword that fell out of the results
   entirely arrives as `from: 4, to: 0`, and `4 - 0` renders a total loss as a
   +4 improvement. The API returns 0 there precisely because no single number is
   honest about it, and `reason` plus the two positions carry the case instead.

   The sign is already the reader's convention -- positive is good, the same
   convention `visibility.delta` follows even though its unit is a score and
   this one's is positions. The two look like opposing conventions and are not.
   Do not "correct" either to match the other's arithmetic; this one was flipped
   earlier today after it was caught painting rank declines green. */
const movement = (row) => (row.delta === null ? 0 : row.delta);

const keywordPath = (row) => {
   const id = parseInt(row.kwid, 10);
   if (!Number.isFinite(id)) return "";
   const slug = row.kw.split(" ").join("_").toLowerCase();
   return "/keywords/" + (global.keywordsecret + id) + "/" + encodeURIComponent(slug);
};

function KeywordName({ row, className }) {
   const path = keywordPath(row);
   /* A row with no usable id still has to render -- it is a real problem on a
      real keyword; it just cannot be navigated to. */
   return path ? (
      <Link className={className} to={path}>
         {row.kw}
      </Link>
   ) : (
      <span className={className + " isPlain"}>{row.kw}</span>
   );
}

function AttentionGroup({ group }) {
   const Mark = MARKS[group.reason] || DownMark;

   return (
      <li className={"dashAttn__row dashAttn__row--group is-" + (TONE[group.reason] || "note")}>
         <span className="dashAttn__mark">
            <Mark />
         </span>
         <span className="dashAttn__count">{group.count}</span>
         <span className="dashAttn__say">
            {group.label}
            {group.sample ? (
               <span className="dashAttn__sample">
                  {group.sampleIsAll ? "" : "e.g. "}
                  {group.sample}
               </span>
            ) : null}
         </span>
         <Link className="dashLink" to="/keywords">
            View
         </Link>
      </li>
   );
}

function AttentionRow({ row }) {
   const Mark = MARKS[row.reason] || DownMark;
   const note = noteFor(row);
   const moved = row.reason === "dropped_top10" || row.reason === "declined";
   const moves = movement(row);

   return (
      <li className={"dashAttn__row is-" + TONE[row.reason]}>
         <span className="dashAttn__mark">
            <Mark />
         </span>
         <KeywordName row={row} className="dashAttn__kw" />
         <span className="dashAttn__facts">
            {moved ? (
               <span className="dashAttn__move" aria-label={"from position " + rank(row.from) + " to " + rank(row.to)}>
                  {rank(row.from)}
                  <span className="dashAttn__arrow" aria-hidden="true">
                     &rarr;
                  </span>
                  {rank(row.to)}
               </span>
            ) : null}
            {note ? <span className="dashAttn__note">{note}</span> : null}
         </span>
         {moved && moves !== 0 ? (
            <span
               className={"dashAttn__delta " + (moves > 0 ? "isUp" : "isDown")}
               aria-label={Math.abs(moves) + (moves > 0 ? " positions gained" : " positions lost")}
            >
               {moves > 0 ? "+" : "−"}
               {Math.abs(moves)}
            </span>
         ) : (
            <span className="dashAttn__delta" />
         )}
      </li>
   );
}

/* Keyword, the domain holding it, the position they hold it at -- three
   columns, hairline-separated, never three spans run together. */
function GapRow({ row }) {
   return (
      <li className="dashAttn__row dashAttn__row--gap is-note">
         {/* No mark. These are examples of the line above them, not four
             separate findings, and a fourth identical circle down the left edge
             would be the repetition this panel exists to have stopped. */}
         <span className="dashAttn__mark" aria-hidden="true" />
         <KeywordName row={row} className="dashAttn__kw" />
         <span className="dashAttn__facts">
            <span className="dashAttn__holder">{row.competitor}</span>
         </span>
         <span className="dashAttn__delta dashAttn__pos">{row.position > 0 ? "#" + row.position : "—"}</span>
      </li>
   );
}

export default function AttentionList({ groups, rows, gaps }) {
   const empty = groups.length === 0 && rows.length === 0 && gaps.length === 0;

   return (
      <Panel
         label="Needs attention"
         action={
            <Link className="dashLink" to="/keywords">
               All keywords
            </Link>
         }
      >
         {empty ? (
            <PanelEmpty>
               Nothing dropped out of the top ten, lost a position or started competing with itself since the last
               run.
            </PanelEmpty>
         ) : (
            <ul className="dashAttn">
               {rows.map((row, i) => (
                  <AttentionRow key={row.kwid || row.kw + "-" + i} row={row} />
               ))}
               {groups.map((group) => (
                  <AttentionGroup key={group.reason} group={group} />
               ))}
               {/* Under the count they belong to: these are three of the
                   keywords the never-ranked line just counted, named, with the
                   rival who holds each one. */}
               {gaps.slice(0, 3).map((row, i) => (
                  <GapRow key={row.kwid || row.kw + "-gap-" + i} row={row} />
               ))}
            </ul>
         )}
      </Panel>
   );
}
