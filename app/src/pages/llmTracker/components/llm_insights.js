import React, { useEffect, useState } from "react";
import Cookies from "universal-cookie";
import axios from "axios";
import ReactApexChart from "react-apexcharts";
import { Tooltip } from "@mui/material";
import { TextLg, Para, SmallText } from "../../commonComponents/parts";
import { Card } from "@/components/ui/card";
import CHART from "../../commonComponents/chart_palette";
import { Bone } from "../../commonComponents/page_skeleton";

// Snapshot dates arrive as plain "YYYY-MM-DD" strings. new Date() on one of
// those parses as UTC and can render the previous day in a western timezone,
// which is the one thing a date on a trend must not do, so the parts are read
// straight off the string.
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const shortDate = (iso) => {
   const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso || ""));
   if (!m) return String(iso || "");
   return Number(m[3]) + " " + (MONTHS[Number(m[2]) - 1] || m[2]);
};

/**
 * A compact, read-only insights strip that sits above the prompt table:
 *   - Mention Summary: how many of the measured answers named the brand, the
 *     tone of the answers that did, and the domains those answers name.
 *   - Mention trend: the same rate over time as an understated sparkline.
 *
 * The headline is answer coverage -- mentioning answers / answers measured --
 * because it is the one number a reader can check against the counts printed
 * directly beneath it. It replaced a "share of voice" that divided a mention
 * tally by that tally plus a count of cited domains: two different units, so
 * the percentage meant nothing and contradicted the counts on its own card.
 *
 * Both cards are secondary to the table, so a failed fetch is swallowed rather
 * than toasted -- the card simply shows its empty state. The heavy, credit-
 * spending work stays with Run analysis; this only reads what was recorded.
 */

function MentionSummary({ data, loading }) {
   const sources = (data && Array.isArray(data.top_sources) ? data.top_sources : []).slice(0, 8);
   const counts = (data && data.sentiment_counts) ? data.sentiment_counts : null;
   const mentioning = data ? (data.mentioning_answers || 0) : 0;

   // The single "Positive" pill came from a tie-break that resolves a 1-1 split
   // upward -- the opposite of the brand-safety rule stated eleven lines above
   // it in the same function. Printing the counts makes the tie-break invisible
   // here: the reader sees the split itself. And the label says what the score
   // is of -- the whole answer, scored by a general-purpose lexicon -- because
   // it is not a reading of how the brand was described.
   const toneParts = counts
      ? [["positive", counts.positive || 0], ["neutral", counts.neutral || 0], ["negative", counts.negative || 0]]
         .filter(([, n]) => n > 0)
         .map(([name, n]) => n + " " + name)
      : [];

   return (
      <Card className="p-4">
         <TextLg class="fB m-b5">Mention Summary</TextLg>
         {loading ? (
            /* Bones in the shape of the panel below, not the word "Loading" --
               a string is a third loading idiom and it collapses the card to two
               lines, so the page jumps when the figures land. */
            <div className="d-flex flex-column gap-2" aria-hidden="true">
               <Bone width="120px" height="14px" />
               <Bone width="180px" height="30px" />
               <Bone width="100%" height="14px" />
               <Bone width="70%" height="14px" />
               <Bone width="100%" height="14px" />
               <Bone width="55%" height="14px" />
            </div>
         ) : !data ? (
            <SmallText class="secondaryClr m-b0">
               Run analysis to see how the AI models mention you.
            </SmallText>
         ) : (
            <>
               <SmallText class="secondaryClr m-b10">
                  {data.brand || "Your brand"}
               </SmallText>

               <div className="d-flex align-items-baseline gap-3 m-b10">
                  <span style={{ fontSize: "30px", fontWeight: 600, color: "var(--ink)", lineHeight: 1 }}>
                     {Math.round(data.answer_coverage || 0)}%
                  </span>
                  <span style={{ fontSize: "13px", color: "var(--ink-3)" }}>
                     of AI answers named you
                  </span>
               </div>

               {/* "N of M models" counts models that ANSWERED, not models
                   configured -- a provider that errored is excluded from both
                   sides, so the fraction can never report less than complete.
                   Say which denominator it is. */}
               <SmallText class="secondaryClr m-b15">
                  {data.mentioning_answers || 0} of {data.answers_total || 0} answers
                  {" · "}{data.models_covering || 0} of {data.models_total || 0} {(data.models_total === 1) ? "model" : "models"} that answered
                  {" · "}{data.your_mentions || 0} {(data.your_mentions === 1) ? "mention" : "mentions"} in total
               </SmallText>

               <Tooltip
                  classes={{ tooltip: "Tltpsmall text-center" }}
                  placement="top-start"
                  title="Tone of each whole answer, scored by a general-purpose lexicon. It is not a reading of how your brand was described."
               >
                  <span className="fieldLabel d-inline-block m-b5">Tone of the answers that named you</span>
               </Tooltip>
               <SmallText class="secondaryClr m-b15">
                  {mentioning === 0
                     ? "No answer has named you yet."
                     : toneParts.length > 0
                        ? toneParts.join(" · ")
                        : "Not scored."}
               </SmallText>

               {/* These are domain-shaped strings matched in the answers'
                   prose, not sources any model linked -- the models return no
                   URLs at all. "Top cited sources" claimed both. The count is
                   the number of answers a domain appears in, which is checkable
                   against the answers themselves. */}
               <Tooltip
                  classes={{ tooltip: "Tltpsmall text-center" }}
                  placement="top-start"
                  title="Names with a domain in them, matched in the answers' wording. Not links — the models provided none. Brands written without a domain (Bright Data, Apify) are not detected."
               >
                  <span className="fieldLabel d-inline-block m-b5">Domains named in answers</span>
               </Tooltip>
               {sources.length > 0 ? (
                  <div className="d-flex flex-column gap-2">
                     {sources.map((s, i) => (
                        <div
                           key={s.domain + i}
                           className="d-flex align-items-center justify-content-between"
                           style={{ fontSize: "13px" }}
                        >
                           <span style={{ color: "var(--ink-2)", overflowWrap: "anywhere" }}>
                              {s.domain}
                           </span>
                           <span
                              title={s.count + (s.count === 1 ? " answer" : " answers")}
                              style={{
                                 color: "var(--ink-3)",
                                 fontVariantNumeric: "tabular-nums",
                                 flex: "0 0 auto",
                                 marginLeft: "8px",
                              }}
                           >
                              {s.count}
                           </span>
                        </div>
                     ))}
                  </div>
               ) : (
                  <SmallText class="secondaryClr m-b0">No domain names appeared in the answers.</SmallText>
               )}
            </>
         )}
      </Card>
   );
}

/* Did the rate's DENOMINATOR move enough to explain the line moving?

   The same rule, the same 0.2 and the same reasoning as the dashboard's
   `answerShift` (pages/widget/dashboard_data.js:625-648), deliberately: the two
   captions describe one defect on two surfaces and must not drift apart. The
   rate divides by every answer collected, so adding four prompts drops it
   without a mention being lost. This project is exactly that case -- its stored
   series is 2-of-4 then 2-of-8, 2-of-8, 2-of-8, and THE NUMERATOR IS 2 AT EVERY
   POINT. The "fall from 50% to 25%" is four answers entering the denominator.

   There is a threshold rather than a note on every change because the answer
   count moves on any run that added a prompt, and a caption that fires on the
   common case trains people to skip the one that matters. 4/8 = 0.50 here,
   well clear of 0.2. */
const ANSWER_CHANGE_SHARE = 0.2;

function MentionTrend({ series, coverage, loading }) {
   const points = Array.isArray(series) ? series : [];
   const hasData = points.length > 0;

   /* Exact per-point numerator and denominator, joined by date from
      /llmtracker/share-of-voice's `coverage_history`. The trend payload carries
      only `prompts_measured`, and deriving the numerator as round(rate x
      measured) would be inventing a count from a rounded rate. Where a date has
      no counts the tooltip gives the denominator and stays silent about the
      numerator. */
   const countsByDate = {};
   (Array.isArray(coverage) ? coverage : []).forEach((c) => {
      if (c && c.date) countsByDate[c.date] = c;
   });

   /* ONLY `mention_rate` is plotted, and that is a decision, not an oversight.
      The same payload carries `avg_position`, which on this project reads
      0.0 -> 0.999 -> 1.0 -> 0.999. That opening zero is not a measurement: the
      08-30 snapshot predates `position_score`, and `LLMMetricSnapshot`
      (models.py:160) declares `avg_position = FloatField(default=0.0)` with no
      null, so a value that was never recorded is stored as, and is
      indistinguishable from, a real zero. Charting it would draw a climb from
      nothing to perfect that no run ever measured. It is also not a position --
      it is the mean of `position_score`, the inverted first-mention offset --
      so the axis label would be wrong on top of the data. Do not add it until
      the field can be null and the pre-existing rows are backfilled to null. */
   const chartSeries = [
      {
         name: "Answer coverage",
         data: points.map((p) => Math.round((p.mention_rate || 0) * 100)),
      },
   ];

   const options = {
      chart: {
         type: "area",
         sparkline: { enabled: true },
         animations: { enabled: false },
      },
      stroke: { curve: "smooth", width: 2 },
      // ApexCharts shades the string it is handed, so it cannot take a CSS
      // variable; chart_palette holds the one concrete copy of the accent.
      colors: [CHART.series[0]],
      fill: {
         type: "gradient",
         gradient: { opacityFrom: 0.35, opacityTo: 0.05 },
      },
      tooltip: {
         x: { show: false },
         y: {
            /* Counts first, rate second. The tooltip is where the misreading
               forms: "50%" then "25%" on a falling line says visibility halved,
               while "2 of 4" then "2 of 8" says the numerator never moved and
               the denominator did. Both numbers come from the API; neither is
               computed here. */
            formatter: (val, opts) => {
               const idx = opts && opts.dataPointIndex;
               const p = points[idx];
               if (!p) return val + "%";
               const date = p.date ? " · " + p.date : "";
               const c = countsByDate[p.date];
               /* The counts and the plotted rate come from two endpoints. They
                  derive from the same snapshot rows today, but if they ever
                  disagree the tooltip would print its own contradiction --
                  "2 of 4 answers (29%)". Only print counts that reproduce the
                  point being hovered; otherwise fall through to the denominator
                  the charted payload itself carries. */
               if (c && typeof c.mentioning === "number" && typeof c.answers === "number"
                   && c.answers > 0 && Math.round((c.mentioning / c.answers) * 100) === val) {
                  return c.mentioning + " of " + c.answers + (c.answers === 1 ? " answer" : " answers")
                     + " (" + val + "%)" + date;
               }
               const measured = p.prompts_measured;
               return val + "%"
                  + (measured ? " of " + measured + (measured === 1 ? " answer" : " answers") : "")
                  + date;
            },
            title: { formatter: () => "" },
         },
      },
   };

   const latest = hasData ? Math.round((points[points.length - 1].mention_rate || 0) * 100) : 0;
   // A sparkline needs at least two points; a single point renders as a lone
   // vertical stub, which reads as broken. Show the number until there is a
   // second day to draw a line between.
   const canChart = points.length >= 2;

   // "N days measured" counted snapshots. A snapshot is only written on a day a
   // run succeeded, and the sparkline has no date axis, so four runs across
   // four consecutive days and four across four months drew identically. Name
   // the runs and print the span they cover.
   const spanFrom = hasData ? shortDate(points[0].date) : "";
   const spanTo = hasData ? shortDate(points[points.length - 1].date) : "";

   const firstMeasured = hasData ? points[0].prompts_measured : null;
   const lastMeasured = hasData ? points[points.length - 1].prompts_measured : null;
   // See ANSWER_CHANGE_SHARE. Null is "not measured" and 0 is "the answer set
   // held"; neither is a finding, and they are not each other either.
   const answersDelta = (firstMeasured && lastMeasured) ? lastMeasured - firstMeasured : 0;
   const shiftShare = lastMeasured > 0 ? Math.abs(answersDelta) / lastMeasured : 0;
   const shiftMaterial = answersDelta !== 0 && shiftShare >= ANSWER_CHANGE_SHARE;
   const answersAdded = answersDelta > 0;
   const answersMoved = Math.abs(answersDelta);

   return (
      <Card className="p-4">
         <TextLg class="fB m-b5">Answer coverage over time</TextLg>
         {loading ? (
            /* One caption line over the 90px chart area, which is what replaces
               it whichever branch below wins. */
            <div className="d-flex flex-column gap-2" aria-hidden="true">
               <Bone width="240px" height="14px" />
               <Bone width="100%" height="90px" />
            </div>
         ) : !hasData ? (
            <SmallText class="secondaryClr m-b0">
               Run analysis to start tracking over time.
            </SmallText>
         ) : canChart ? (
            <>
               <SmallText class="secondaryClr m-b10">
                  Latest {latest}%
                  {lastMeasured ? " of " + lastMeasured + (lastMeasured === 1 ? " answer" : " answers") : ""}
                  {" · "}{points.length} {points.length === 1 ? "run" : "runs"}, {spanFrom} – {spanTo}
               </SmallText>
               <ReactApexChart
                  options={options}
                  series={chartSeries}
                  type="area"
                  height={90}
               />
               {/* Wording mirrors the dashboard's AnswerShift verbatim -- "answers",
                   never "prompts", because answers = prompts x models and the rate
                   genuinely divides by answers. --ink-2, not --warn: nothing has gone
                   wrong, prompts being added is the product working. */}
               {shiftMaterial ? (
                  <p className="geoTrendNote">
                     <span className="geoTrendNoteFig">
                        {answersMoved} {answersMoved === 1 ? "answer" : "answers"} {answersAdded ? "added" : "removed"}
                     </span>{" "}
                     in this window. The rate divides by every answer collected, so {answersAdded ? "a fall" : "a rise"} here
                     need not be {answersAdded ? "lost mentions" : "gained mentions"}.
                  </p>
               ) : null}
            </>
         ) : (
            <div className="d-flex flex-column" style={{ minHeight: "90px", justifyContent: "center" }}>
               <span style={{ fontSize: "28px", fontWeight: 600, color: "var(--ink)", lineHeight: 1.1 }}>
                  {latest}%
               </span>
               <SmallText class="secondaryClr m-b0 m-t5">
                  of answers named you on {spanTo} · run analysis on another day to see the trend line
               </SmallText>
            </div>
         )}
      </Card>
   );
}

function LLMInsights({ refreshKey }) {
   const [sov, setSov] = useState(null);
   const [sovLoading, setSovLoading] = useState(true);
   const [trend, setTrend] = useState(null);
   const [trendLoading, setTrendLoading] = useState(true);

   useEffect(() => {
      const controller = new AbortController();
      const cookies = new Cookies();
      const usertoken = cookies.get("session_token");
      const userid = cookies.get("session_userid");
      const groupid = cookies.get("activegrp");

      if (!usertoken || !userid) return;

      const body = { userid: userid, groupid: groupid };
      const headers = { Authorization: "Token " + usertoken };

      axios
         .post(global.apiurl + "/llmtracker/share-of-voice", body, {
            headers,
            signal: controller.signal,
         })
         .then((r) => r.data)
         .then((res) => {
            if (res && res.status !== "false" && res.data) setSov(res.data);
            setSovLoading(false);
         })
         .catch((error) => {
            if (!axios.isCancel(error)) setSovLoading(false);
         });

      axios
         .post(global.apiurl + "/llmtracker/trend", body, {
            headers,
            signal: controller.signal,
         })
         .then((r) => r.data)
         .then((res) => {
            if (res && res.status !== "false" && res.data) setTrend(res.data.series || []);
            setTrendLoading(false);
         })
         .catch((error) => {
            if (!axios.isCancel(error)) setTrendLoading(false);
         });

      return () => controller.abort();
      // Re-read the aggregates whenever the page signals a data change
      // (Run analysis, Add prompt, Delete) via a bumped refreshKey.
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [refreshKey]);

   return (
      <div className="llmInsightsStrip">
         <MentionSummary data={sov} loading={sovLoading} />
         <MentionTrend series={trend} coverage={sov ? sov.coverage_history : null} loading={trendLoading} />
      </div>
   );
}

export default LLMInsights;
