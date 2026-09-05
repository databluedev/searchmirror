import React from "react";
import { Link } from "react-router-dom";

/* MENTION RATE -- one strip, not a card.

   How often the models name this domain when they answer the project's prompts.
   It is one figure, one fact about it and a way through, so it is a single
   full-width line: a card with a header, a body and its own border around that
   is more furniture than content.

   THE COUNT IS THE FIGURE, THE PERCENT IS AN ASIDE
   ------------------------------------------------
   The headline is "2 of 8 answers", not "25%". "2 of 8" and "200 of 800" are
   the same rate and nothing like the same evidence, and a bare percentage hides
   which one you are looking at. So the count leads at 15px, the percent follows
   at 12px in muted ink, and the percent never appears without the pair it came
   from. It is rounded to a whole number on purpose -- "25.0%" claims a tenth of
   a point of resolution that eight answers cannot carry.

   The name is "Mention rate" rather than "AI visibility" because it says what
   was counted. It is also where the category has landed -- Profound, Peec,
   Otterly and Wix's LLM Pulse all describe this number as mentions or coverage
   rather than as visibility.

   WHY THIS STRIP DRAWS NO TREND
   -----------------------------
   This project's stored series is 0.50, 0.25, 0.25, 0.25 over four days, and
   drawn as a line that is a decline. It is not one. The counts behind it are
   2 of 4, then 2 of 8, 2 of 8, 2 of 8: the numerator never moved. The brand was
   named in exactly two answers on every one of those days, and the rate halved
   because four prompts were added and nothing named the brand in them. The 95%
   Newcombe interval for that difference is [-64.3, +23.8] percentage points --
   it contains zero, so the fall is not distinguishable from no change at all.

   The prompts are also written by the user, and a published study measured a
   6.6x swing in mention rate from wording alone, so a user can move this number
   without anything changing in the world. Someone who read "AI visibility down
   25%" and rewrote their content would be doing work for no reason.

   So the server decides whether a change is bigger than its interval, and this
   component renders one of three things and never a fourth:
     significant   -- "down from 2 of 4", both n shown, no colour.
     not           -- no delta, and a sentence saying the difference is within
                      the margin of error, because a number that silently
                      vanishes reads as a bug rather than as a finding.
     unknowable    -- "not enough data yet". Never "no change".
   The maths is not repeated here and must not be: two implementations of one
   threshold is how the number in a strip comes to disagree with the number on
   the page it links to.

   No --up/--down anywhere on this strip. Those two tokens mean "rank improved"
   and "rank declined"; a mention rate is not a rank, and borrowing the colour
   would assert a precision this measurement does not have. The strip is ink and
   one link, like the table beside it.

   TWO FACTS WERE WITHDRAWN FROM THIS STRIP, both for claiming more than their
   field could support, and both are recorded in dashboard_data.js rather than
   merely deleted -- a fact that disappears without a reason gets added back.
     "Cited instead"  -- matched domain-shaped substrings in prose, so it named
                         one rival out of roughly fifteen and pointed the reader
                         at the wrong one. Now off the payload entirely.
     "Sentiment"      -- whole-document sentiment presented as sentiment about
                         the brand, an optimistic tie-break, and a sample of two
                         with no interval.
   Read those notes before putting either back.

   The strip keeps its slot on every project. A project with no AI answers says
   so here rather than dropping the section, because a section that disappears
   changes the shape of the page from one project to the next. */

const plural = (n, word) => (n === 1 ? word : word + "s");

/* The percentage, derived from the two integers printed beside it.

   `ai.coverage` carries the same figure and is deliberately not used: taking the
   percentage from the exact pair on screen is the only way the two can never
   disagree, and that is a property of this component rather than a promise from
   the service. Confirmed with the API owner, who keeps `coverage` for the Geo
   page and treats it as unused here.

   Whole numbers on purpose -- "25.0%" claims a tenth of a point of resolution
   that eight answers cannot carry. `total` is checked by the caller before this
   runs, so there is no divide by zero. */
const rate = (ai) => Math.round((100 * ai.mentioning) / ai.total) + "%";

/* What the denominator is made of, and therefore what to do about it. Rendered
   only inside a suppression sentence, where it is the argument for adding
   prompts rather than a fourth fact competing with the other two. Returns ""
   when the API sent neither count, and the sentence then stops after its own
   verdict rather than trailing an empty bracket.

   Named for the sample, not "coverage": the API uses `coverage` for the RATE,
   and one word meaning both the percentage and the thing it was measured over
   is a trap in a file that prints both. */
const sampleDetail = (ai) => {
   const parts = [];
   if (ai.promptsTotal > 0) parts.push(ai.promptsTotal + " " + plural(ai.promptsTotal, "prompt"));
   if (ai.modelsTotal > 0) parts.push(ai.modelsTotal + " " + plural(ai.modelsTotal, "model"));
   return parts.join(", ");
};

/* The one sentence this strip is allowed to say about change.

   The `false` and `null` branches say different things on purpose. `false` is a
   result -- it was compared and the difference is inside the interval, so
   "within the margin of error" is a finding. `null` is the absence of one, and
   may only say that there is not enough data yet. The distinction is the whole
   point: "we measured and it did not move" and "we could not measure" are
   different sentences, and a reader who is given the wrong one is misled either
   way round. Neither branch may render a direction. */
const changeFact = (ai) => {
   const c = ai.change;
   const detail = sampleDetail(ai);

   /* Nothing was compared. This branch is first so that no later one can fall
      into it. */
   if (c.significant === null) {
      return "not enough data yet to compare" + (detail ? " (" + detail + ")" : "");
   }

   /* A direction, and the only branch allowed to name one. `delta` is truthy
      here, so a verdict that arrived without a usable difference falls through
      to the measured-but-not-distinguishable wording below rather than
      inventing a direction out of a null. */
   if (c.significant === true && c.available && c.delta) {
      return (c.delta > 0 ? "up" : "down") + " from " + c.fromMentioning + " of " + c.fromTotal;
   }

   return "within the margin of error" + (detail ? " (" + detail + ")" : "");
};

/* The way out doubles as the remedy. Whenever the strip could not state a
   movement, the thing that would let it is more answers, and the link says so;
   it is the same destination in every case, so this costs no navigation and
   points the reader at the one action that makes this number mean something.

   Never "Run analysis": this is a link, and a link labelled with an action that
   spends the account's provider credits would be lying about what clicking it
   does. Running is a deliberate act on the page it leads to. */
const goLabel = (ai) => {
   if (ai.total === 0) return ai.promptsTotal === 0 ? "Add prompts" : "Geo citations";
   return ai.change.significant === true ? "Geo citations" : "Add prompts";
};

const Fact = ({ label, children }) => (
   <span className="dashStrip__fact">
      <span className="dashStrip__key">{label}</span> {children}
   </span>
);

/* Why the rate may have moved without a mention moving.

   The second reason this strip does not draw a decline, and it is independent
   of the first. The margin-of-error sentence above says the change cannot be
   distinguished from chance; this says that even if it could, the movement is
   in the denominator. Project 4 is exactly that -- 2 of 4 became 2 of 8 because
   four prompts were added, and the numerator never moved off 2.

   Deliberately the same sentence shape as ListChange in trend_panel.js, because
   it is deliberately the same correction: the visibility score divides by every
   tracked keyword and this divides by every answer, so both fall when the
   denominator grows and neither fall is a loss. A reader who has learned to
   read one should not have to learn the other.

   The only element on the strip allowed a second line, and it takes one only
   when `material` says the composition moved enough to explain the rate. Set in
   --ink-2 like its counterpart: it is a statement a reader must not skim on the
   one project where it applies, and it is not --warn, because nothing has gone
   wrong -- prompts being added is the product working. */
function AnswerShift({ shift }) {
   const added = shift.delta > 0;
   const n = Math.abs(shift.delta);

   return (
      <p className="dashStrip__note">
         <span className="dashStrip__noteFig">
            {n} {plural(n, "answer")} {added ? "added" : "removed"}
         </span>{" "}
         in this window. The rate divides by every answer collected, so {added ? "a fall" : "a rise"} here need not be
         {added ? " lost mentions" : " gained mentions"}.
      </p>
   );
}

/* Two empty states, not one, because they need different sentences and have
   different ways out. `prompts_total` is the only field that tells them apart:
   a project with no prompts has never had Geo set up, and a project with
   prompts and no answers is set up and has not run.

   docs/DESIGN.md, "Empty state": one sentence, no art. The never-set-up case
   gets a second clause because projects 1 and 2 land here and the sidebar tab
   alone has never told anyone what Geo citations is for -- it is the product's
   one real differentiator and this is the most-visited screen it appears on. */
const EmptyBody = ({ ai }) =>
   ai.promptsTotal === 0 ? (
      <p className="dashStrip__body dashStrip__body--empty">
         No AI answer has been collected for this project yet. Geo citations asks the models your buyers&rsquo;
         questions and counts how often they name you.
      </p>
   ) : (
      <p className="dashStrip__body dashStrip__body--empty">
         {ai.promptsTotal} {plural(ai.promptsTotal, "prompt")} {ai.promptsTotal === 1 ? "is" : "are"} set up for this
         project, but no analysis has run yet.
      </p>
   );

export default function AiPanel({ ai, shift }) {
   const measured = ai.total > 0;

   return (
      <section className="dashStrip">
         {/* <h3> for the same reason panel.js uses one: the AI ANSWERS band
             above this strip carries the section's <h2>. */}
         <h3 className="dashStrip__label">Mention rate</h3>
         {/* The figure and the note that corrects it are ONE flex item, not two.
             As siblings of the link they were separated by it at any width where
             the link wrapped but the row had not yet stacked -- the way out sat
             between the rate and the sentence explaining the rate, which reads
             as the note belonging to whatever follows. Wrapping them means no
             breakpoint can come between them. */}
         <div className="dashStrip__content">
            {!measured ? (
               <EmptyBody ai={ai} />
            ) : (
               <p className="dashStrip__body">
                  <span className="dashStrip__lead">
                     <span className="dashStrip__count">
                        {ai.mentioning} of {ai.total}
                     </span>{" "}
                     {plural(ai.total, "answer")}
                     <span className="dashStrip__rate">{rate(ai)}</span>
                  </span>
                  <Fact label="Change">{changeFact(ai)}</Fact>
               </p>
            )}
            {measured && shift && shift.material ? <AnswerShift shift={shift} /> : null}
         </div>
         <Link className="dashLink dashStrip__go" to="/llmtracker">
            {goLabel(ai)}
         </Link>
      </section>
   );
}
