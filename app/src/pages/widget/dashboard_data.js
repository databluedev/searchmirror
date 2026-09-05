import axios from "axios";
import Cookies from "universal-cookie";
import { getfulldate } from "../common_fun";

/* The dashboard's one request, and the one place its payload is made safe.

   Every panel on this screen reads from the shape normalizeOverview returns,
   never from the raw response. That is deliberate: a missing field read
   straight into JSX renders as `undefined`, a count divided by a missing total
   renders as `NaN`, and an object arriving where a component expected an array
   renders as `[object Object]`. Coercing once, here, means no panel can do any
   of those three whatever the API returns.

   The contract is fixed. Field names on the way in are the API's and are not
   renamed; the camelCase on the way out is this app's. */

const OVERVIEW_URL = "/dashboard_overview";

const obj = (v) => (v && typeof v === "object" && !Array.isArray(v) ? v : {});
const list = (v) => (Array.isArray(v) ? v : []);

const text = (v) => {
   if (typeof v === "string") return v.trim();
   if (typeof v === "number" && Number.isFinite(v)) return String(v);
   return "";
};

/* null, never NaN. A panel decides what "not measured" looks like; it must
   never be handed a number that prints as NaN. */
const num = (v) => {
   if (v === null || v === undefined || v === "") return null;
   const n = Number(v);
   return Number.isFinite(n) ? n : null;
};

/* Counts are always a number, because they get summed and compared. */
const count = (v, fallback = 0) => {
   const n = num(v);
   return n === null ? fallback : Math.trunc(n);
};

const ATTENTION_REASONS = ["dropped_top10", "declined", "cannibal", "never_ranked"];
const TRENDS = ["up", "down", "flat"];

const normalizeAlert = (raw) => {
   const a = obj(raw);
   return {
      code: text(a.code),
      severity: text(a.severity) === "info" ? "info" : "warn",
      text: text(a.text),
   };
};

const normalizeAttention = (raw) => {
   const a = obj(raw);
   const reason = text(a.reason);
   return {
      kwid: text(a.kwid),
      kw: text(a.kw),
      from: count(a.from),
      to: count(a.to),
      /* Positions moved, signed the way a reader expects: negative is worse.
         0 when either end is unranked, because there is no honest number for
         "was 4, now nowhere" -- `from`/`to` and `reason` carry that case. */
      delta: num(a.delta),
      /* The site's own pages competing for this keyword. Present on every row,
         not just cannibalised ones. 0 or 1 is normal; 2 or more is the
         conflict. */
      pages: count(a.pages),
      reason: ATTENTION_REASONS.indexOf(reason) >= 0 ? reason : "declined",
   };
};

const normalizeCompetitor = (raw) => {
   const c = obj(raw);
   const trend = text(c.trend);
   return {
      domain: text(c.domain),
      avgPosition: num(c.avg_position),
      /* How many keywords the average is taken over. 0 means the domain ranks
         for nothing here, and `avg_position` then arrives as 0.0 -- which in a
         column where lower is better would sort a dead competitor to the top
         and read as the best score on the panel. Every use of avgPosition is
         gated on this. */
      keywords: count(c.keywords),
      /* Whether `trend` was computed against a real second reading. False means
         "holding" is the absence of a comparison, not the result of one. */
      trendComparable: c.trend_comparable === undefined || c.trend_comparable === null
         ? null
         : Boolean(c.trend_comparable),
      trend: TRENDS.indexOf(trend) >= 0 ? trend : "flat",
   };
};

/* The gap block: which domains hold the keywords this project does not.

   `holders` is a magnitude series -- keywords owned per domain -- so it is
   sorted here rather than trusted to arrive sorted. A chart whose bars are not
   ordered by length asks the reader to do the ranking themselves. */
const normalizeHolder = (raw) => {
   const h = obj(raw);
   return {
      domain: text(h.domain),
      keywords: count(h.keywords),
      avgPosition: num(h.avg_position),
   };
};

const normalizeWorst = (raw) => {
   const w = obj(raw);
   return {
      kwid: text(w.kwid),
      kw: text(w.kw),
      competitor: text(w.best_competitor),
      position: count(w.their_position),
   };
};

/* One attention group: a reason, how many keywords hold it, and the phrase to
   print after the count. `label` is whatever the API called it; when it is
   missing the reason table below supplies the wording, so a group never
   renders as a bare number with nothing after it. */
const normalizeGroup = (raw) => {
   const g = obj(raw);
   const reason = text(g.reason);
   return {
      reason: ATTENTION_REASONS.indexOf(reason) >= 0 ? reason : "",
      count: count(g.count),
      label: text(g.label),
      /* An array of example keywords, not one string. Joined here rather than
         in the component so a panel can never render "[object Object]" or a
         bare comma-run out of whatever this field turns into next. Two is the
         most a single line can carry beside a count and a link. */
      /* Two names at most, and whether they are the whole set. A line reading
         "2 have never ranked / local rank tracking, datablue" names both of
         them; the same line under a count of 28 needs "e.g." or it claims the
         28 are those two. */
      sample: list(g.sample).map(text).filter(Boolean).slice(0, 2).join(", "),
      sampleIsAll: list(g.sample).filter(Boolean).length >= count(g.count),
   };
};

/* One comparison of the mention rate against an earlier reading.

   `significant` IS THREE-VALUED AND THE THIRD VALUE IS THE POINT OF IT.
   The server owns the verdict -- it holds the Wilson intervals and the Newcombe
   interval for the difference -- and this app never recomputes it, never infers
   it from two numbers being unequal, and never collapses the missing case:
     true   -- the interval for the difference excludes 0. A movement may be
               stated, with the counts at both ends.
     false  -- measured, compared, and the interval contains 0. The change is
               not distinguishable from chance, so NO delta, arrow or direction
               word may be rendered. The strip says there is no measurable
               change instead.
     null   -- there was nothing to compare against, or one end measured no
               answers. Not "no change" -- no knowledge. The strip says only
               that there is not enough data yet.
   Same discipline as `movement.comparable` above, and for the same reason:
   folding null into false would tell a user their movement had been tested and
   found small when it was never tested at all.

   `answersDelta` is the confound, and the exact analogue of
   `movement.keywordsDelta` on the rank side. It is the only field that
   separates the two ways this rate can fall -- the brand losing answers, or the
   denominator growing under a numerator that never moved. On this project it is
   +4 against a numerator that held at 2, which is a bigger prompt set and not a
   lost brand, and the strip is only able to say so because of this field. */
const normalizeAiChange = (raw) => {
   const c = obj(raw);
   const available = Boolean(c.available);
   return {
      available,
      /* Gated on `available`: every other field is null when it is false, and a
         baseline of "null of null" must never reach a sentence. */
      fromMentioning: available ? count(c.from_mentioning) : null,
      fromTotal: available ? count(c.from_answers) : null,
      significant: c.significant === undefined || c.significant === null ? null : Boolean(c.significant),
      /* Percentage points, signed. Only ever read for its SIGN, to choose the
         word "up" or "down", and only when `significant` is true. */
      delta: available ? num(c.delta) : null,
      answersDelta: available ? num(c.answers_delta) : null,
   };
};

export function normalizeOverview(raw) {
   const src = obj(raw);
   const p = obj(src.project);
   const v = obj(src.visibility);
   const m = obj(src.movement);
   const s = obj(src.spread);
   const ai = obj(src.ai);
   const run = obj(src.run);
   const g = obj(src.gap);

   return {
      project: {
         name: text(p.name),
         domain: text(p.domain),
         region: text(p.region),
         language: text(p.language),
         device: text(p.device),
         lastChecked: text(p.last_checked),
         nextRun: text(p.next_run),
      },
      /* An alert with no text is nothing a user can act on, so it is not an
         alert. Dropping it here keeps the bar from rendering an empty row. */
      alerts: list(src.alerts).map(normalizeAlert).filter((a) => a.text),
      attention: list(src.attention).map(normalizeAttention).filter((a) => a.kw),
      visibility: {
         score: num(v.score),
         best: num(v.best),
         delta: num(v.delta),
         spark: list(v.spark).map(num).filter((n) => n !== null),
         first: count(v.first),
         top3: count(v.top3),
         top10: count(v.top10),
         unranked: count(v.unranked),
         /* The mean current position across the keywords that hold one. null
            until the API sends it, and null is rendered as an em dash -- never
            derived from the band counts, which cannot produce a mean. */
         avgPosition: num(v.avg_position),
         ranked: num(v.ranked),
      },
      movement: {
         improved: count(m.improved),
         declined: count(m.declined),
         unchanged: count(m.unchanged),
         windowDays: count(m.window_days, 7),
         /* Three-valued on purpose. `true` and `false` are the API's answer to
            "is there a second reading to compare against"; `null` means it did
            not say, which is not the same as "no". A panel that collapsed the
            missing case into `false` would tell a project with a year of
            history that its first comparison has not happened yet. */
         comparable: m.comparable === undefined || m.comparable === null ? null : Boolean(m.comparable),
         snapshots: num(m.snapshots),
         firstComparisonAt: text(m.first_comparison_at),
         /* Keywords with no position at either end of the window. They are not
            "unchanged" -- there was nothing to change -- and folding them in
            would put the project's whole keyword count behind a sentence about
            two keywords holding station. */
         absent: count(m.absent),
         /* Signed change in the number of TRACKED KEYWORDS across this same
            window. Not a ranking movement -- it is the reason a score can fall
            with no ranking having moved, which is otherwise invisible on this
            screen.

            num(), so it is null when the API omits it, and null is rendered as
            nothing at all. It must never be coerced to 0: "the list did not
            change" and "there is no window to measure a change over" are
            different states, and a project with one snapshot is the second. */
         keywordsDelta: num(m.keywords_delta),
         /* The number of days the comparison ACTUALLY spans, which is not
            always `window_days`. See movementWindow() below. */
         windowActual: num(m.window_actual),
         /* The SHORTEST span any keyword contributes. Only ever rendered
            alongside windowActual, and only when windowMixed says the spread
            reached a keyword that moved. */
         windowMin: num(m.window_min),
         /* Did a keyword measured over a shorter span than `window_actual`
            land in `improved` or `declined`?

            Three-valued, and false is a real answer -- "checked, and no mover
            was short-measured" -- so it must not double as "could not check".
            null is the second thing, and it renders as the plain figure. */
         windowMixed: m.window_mixed === undefined || m.window_mixed === null
            ? null
            : Boolean(m.window_mixed),
      },
      /* Present, not merely empty. A project whose competitors hold nothing and
         a payload from a server that does not send this block yet are different
         states, and only the first one may be rendered as a finding. */
      gap: src.gap && typeof src.gap === "object" && !Array.isArray(src.gap)
         ? {
              present: true,
              unrankedTotal: count(g.unranked_total),
              covered: count(g.covered),
              holders: list(g.holders)
                 .map(normalizeHolder)
                 .filter((h) => h.domain)
                 .sort((a, b) => b.keywords - a.keywords),
              worst: list(g.worst).map(normalizeWorst).filter((w) => w.kw),
           }
         : { present: false, unrankedTotal: 0, covered: 0, holders: [], worst: [] },
      attentionGroups: list(src.attention_groups)
         .map(normalizeGroup)
         .filter((row) => row.reason && row.count > 0),
      spread: {
         p1: count(s.p1),
         p2_3: count(s.p2_3),
         p4_10: count(s.p4_10),
         p11_30: count(s.p11_30),
         beyond: count(s.beyond),
      },
      competitors: list(src.competitors).map(normalizeCompetitor).filter((c) => c.domain),
      /* MENTION RATE. A count and its denominator, never a rate on its own:
         2-of-8 and 200-of-800 are the same percentage and are not the same
         evidence, so the strip is given both integers and derives the percent
         from them at the point of display. `ai.coverage` is on the payload and
         is deliberately NOT read: it is the same figure under a second name,
         kept for the Geo page, which renders it as `answer_coverage`. Deriving
         the percent from the two integers printed beside it is the only way the
         count and the percentage on this strip cannot contradict each other --
         a property of this file rather than a promise from another service.

         `cited_instead` WAS WITHDRAWN AS FALSE, not merely dropped, and this
         note is here so nobody wires it back in. It never held citations. The
         extractor matched domain-shaped substrings in PROSE, and the stored
         answers contain no URLs at all: the single value it ever produced here,
         "searchapi.io", surfaced only because that brand name ends in ".io". It
         could not represent a rival whose name has no dot in it, so Bright Data
         -- which wins six of the six answers that do not mention the brand --
         could never appear, alongside roughly fourteen others. Rendered as "who
         is winning the answers you lose", it understated the real competitive
         position by about fifteen times.

         The field is gone from this endpoint as of 2026-09-02, so there is
         nothing left to normalise; it is still returned by
         /llmtracker/share-of-voice, which the Geo Citations page renders, and
         that surface is being handled separately. An honest replacement is in
         progress (`geo-brands`): multi-word Title Case phrases, acronyms and
         cited hosts scored against the answers already stored, at no credit
         cost. Take a competitor fact from that when it lands -- never from a
         regex over prose. See scratchpad ai-strip-api.md 5.1. */
      ai: {
         mentioning: count(ai.mentioning_answers),
         total: count(ai.answers_total),
         /* The two empty states are told apart by `prompts_total`, not by the
            answer count: "Geo was never set up" and "prompts exist but nothing
            has run" need different sentences and different ways out, and only
            this field separates them. */
         promptsTotal: count(ai.prompts_total),
         modelsTotal: count(ai.models_total),
         /* `sentiment` is on the payload and is deliberately NOT normalised.
            Withdrawn 2026-09-02 on the same principle as `cited_instead` above:
            it is wrong on three independent counts, and showing its `n` would
            have fixed only the third.
              scope   -- it is TextBlob's polarity over the WHOLE answer, not
                         over the sentences that name the brand, so favourable
                         prose about a competitor scores as favourable about
                         you. On this project's own data the effect is not
                         subtle and it is backwards: the most favourable answer
                         about the brand scores -0.003 ("neutral") while five
                         answers that never mention it score 0.23 to 0.37
                         ("positive").
              tie-break -- 1 positive against 1 neutral resolves to "positive".
                         An optimistic rule on a brand-safety signal is the one
                         direction it must not fail in.
              sample  -- two mentioning answers, no interval, no n on screen.
            A strip whose whole purpose is to stop claiming more than the
            evidence supports cannot carry a three-way overclaim because it is
            a small one. It earns its place back when it is brand-scoped --
            restricted to the sentences that actually name the brand, which is
            being fixed on the detail page -- and it returns with its `n`.
            See scratchpad geo-audit.md F5 and F6. */
         /* The change across the WHOLE retained series, not since the last run.
            `change.since_previous` is also on the payload and is not read here:
            on this data it compares 2-of-8 with 2-of-8 and reports nothing
            happening, while `since_first` covers the 2-of-4 -> 2-of-8 span that
            a chart of this project would appear to show falling. The claim
            worth suppressing is the one the reader would otherwise make. */
         change: normalizeAiChange(obj(ai.change).since_first),
      },
      run: {
         errc: text(run.errc),
         err: text(run.err),
         fkw: count(run.fkw),
      },
   };
}

/* Has this project ever been ranked?

   The spark series, and only the spark series. It holds one point per reading,
   so it is empty exactly when no keyword has a single rank observation -- the
   API owner's answer, and the only field on the payload that answers it.

   The three obvious alternatives are all wrong, and two of them were wrong here
   first:
     score          -- always an int, never null, and 0 is a real measured
                       reading (project 4 genuinely scores 4 with every keyword
                       past 40). It cannot distinguish "bad" from "never ran".
     spread total   -- the five buckets sum to the KEYWORD count, and `beyond`
                       absorbs the unranked ones. A project that has never run
                       has all thirty keywords in `beyond`, so the total is 30,
                       not 0.
     band counts    -- same trap: `visibility.unranked` counts keywords that
                       have never ranked, so a brand-new project reports all
                       thirty there.
   Both of those would have reported a never-run project as measured and shown
   it a dashboard of zeros. `project.last_checked === ""` corroborates. */
export function hasRankHistory(data) {
   return data.visibility.spark.length > 0;
}

export const spreadTotal = (s) => s.p1 + s.p2_3 + s.p4_10 + s.p11_30 + s.beyond;

/* A timestamp a person can read, from whatever the API sent.

   Never a raw ISO string. An empty or unparseable value returns "", and every
   call site renders an em dash for that rather than "Invalid Date" -- which is
   what `new Date(undefined)` stringifies to, and what a header that trusts the
   payload puts on screen for a project that has never run. */
export function whenLabel(value) {
   if (!value) return "";
   const then = new Date(value);
   const ms = then.getTime();
   if (!Number.isFinite(ms)) return "";

   const diff = Date.now() - ms;
   const ahead = diff < 0;
   const mins = Math.round(Math.abs(diff) / 60000);

   if (mins < 1) return "just now";
   if (mins < 60) return ahead ? "in " + mins + " min" : mins + " min ago";

   const hours = Math.round(mins / 60);
   if (hours < 24) {
      const unit = hours === 1 ? " hour" : " hours";
      return ahead ? "in " + hours + unit : hours + unit + " ago";
   }

   const days = Math.round(hours / 24);
   if (days === 1) return ahead ? "tomorrow" : "yesterday";
   if (days < 7) return ahead ? "in " + days + " days" : days + " days ago";

   return getfulldate(then);
}

/* Whatever the server said, in the reader's words.

   The view answers failures as `message`, but an unauthenticated request never
   reaches it: DRF rejects that itself and uses `detail`. Reading only `message`
   would swallow "Authentication credentials were not provided." -- the one
   failure with an obvious fix -- and show the generic sentence instead. */
const apiMessage = (payload) =>
   text(payload.message) ||
   text(payload.detail) ||
   "This dashboard could not be loaded. Check your connection and try again.";

/* One request, one shape, one error string. The caller renders `error` verbatim
   when it is set -- a message from the API says more than "something failed",
   and this screen used to sit on a spinner instead of saying either. */
export async function fetchOverview(signal) {
   const cookies = new Cookies();
   const userid = cookies.get("session_userid");
   const grpid = cookies.get("activegrp");
   const usertoken = cookies.get("session_token");

   if (!userid || !usertoken) {
      return { ok: false, data: null, error: "Your session has expired. Sign in again to load this dashboard." };
   }
   if (!grpid) {
      return { ok: false, data: null, error: "No project is selected." };
   }

   try {
      const response = await axios.post(
         global.apiurl + OVERVIEW_URL,
         { userid: userid, grpid: grpid },
         /* axios has no default timeout, so a request that never answers leaves
            the screen on its skeleton for ever -- the exact failure the audit
            found here. Thirty seconds, then it fails with something to read. */
         { headers: { Authorization: "Token " + usertoken }, signal: signal, timeout: 30000 },
      );
      const res = obj(response.data);
      if (text(res.status) !== "true") {
         return { ok: false, data: null, error: apiMessage(res) };
      }
      return { ok: true, data: normalizeOverview(res), error: "" };
   } catch (error) {
      if (axios.isCancel(error) || (error && error.name === "CanceledError")) {
         return { ok: false, data: null, error: "", cancelled: true };
      }
      return { ok: false, data: null, error: apiMessage(obj(error && error.response && error.response.data)) };
   }
}

/* ---------------------------------------------------------------------------
   Views: what the page shows, decided from what the payload can support.

   The panels below used to render a fixed skeleton whatever arrived, which is
   how a project with one snapshot got a MOVEMENT panel reading 0 / 0 / 30 and
   a NEEDS ATTENTION list that printed "never ranked" eight times. These three
   functions are where that decision is made instead, once, in front of the
   components rather than inside each of them.
   --------------------------------------------------------------------------- */

/* Every keyword in the project. The five spread buckets sum to the keyword
   count -- `beyond` absorbs the unranked ones -- so this is the total even for
   a project that has never ranked for anything. */
export const keywordTotal = (data) => spreadTotal(data.spread);

/* How a group's count is read out. The count is rendered as its own numeral, so
   these are the phrase that follows it and never contain the number. */
const GROUP_PHRASE = {
   never_ranked: ["keyword has never ranked", "keywords have never ranked"],
   dropped_top10: ["keyword dropped out of the top ten", "keywords dropped out of the top ten"],
   declined: ["keyword lost position", "keywords lost positions"],
   cannibal: ["keyword has more than one page competing", "keywords have more than one page competing"],
};

const phraseFor = (reason, n) => {
   const pair = GROUP_PHRASE[reason];
   if (!pair) return n === 1 ? "keyword needs attention" : "keywords need attention";
   return n === 1 ? pair[0] : pair[1];
};

/* NEEDS ATTENTION, resolved: which reasons show as one counted line, and which
   keywords still deserve a row of their own.

   The API decides the split, not this function. `attention` carries only the
   reasons whose rows say something a count cannot -- a decline states "5 -> 6,
   -1", a cannibalisation states "2 pages competing" -- and never_ranked rows
   are filtered out server-side at any count, because a never-ranked keyword's
   row is its name and nothing else, which is why twenty-eight of them rendered
   as twenty-eight identical lines. So `attention` is rendered verbatim.

   The one thing decided here is the overlap. `attention_groups` always carries
   all four reasons, so on a project with one decline the payload holds both a
   "1 lost positions" group AND the row that decline is. Printing both states it
   twice. The row wins, because it has the positions in it.

   Deliberately NOT a threshold on count. An earlier cut dropped groups under
   four keywords, which would have swallowed a legitimate group on a project
   with four declines; presence of the rows is the only test. */
export function attentionView(data) {
   const rows = data.attention;

   const listed = {};
   rows.forEach((row) => {
      listed[row.reason] = true;
   });

   const groups = data.attentionGroups
      .filter((group) => group.count > 0 && !listed[group.reason])
      .map((group) => ({
         reason: group.reason,
         count: group.count,
         label: group.label || phraseFor(group.reason, group.count),
         sample: group.sample,
         sampleIsAll: group.sampleIsAll,
      }));

   return { groups: groups, rows: rows };
}

/* THE COVERAGE GAP, as the few rows that carry it.

   It no longer has a section. A panel built on `covered: 3` was half a screen
   arguing from three facts, and the same three facts read better as three lines
   under the never-ranked count they belong to: the keyword nobody here holds,
   the domain that does, and the position they hold it at.

   `worst` is the API's own list and is never derived. There is no way to work
   out which absence costs most from the rest of the payload, and a panel must
   not guess at that. */
export function gapRows(data) {
   return data.gap.worst;
}

/* A change in the KEYWORD LIST big enough to explain what the trend line is
   doing, which is a different question from whether the list changed at all.

   Why this exists. The visibility score divides by every tracked keyword, so
   adding keywords lowers it with no ranking having moved. Project 4 is the
   case: its score reads 17.5, 17.5, 0.0, 4.0, 4.0 while its keyword count reads
   4, 4, 30, 30, 30 -- twenty-six keywords were added on one day and the same two
   ranked keywords went from being divided by four to being divided by thirty.
   Nothing about its rankings changed. The chart draws a cliff, a reader
   concludes their rankings collapsed, and they go looking for a fault that is
   not there. The score is right and the chart is right; only a third number
   stops the wrong conclusion being drawn from them.

   THE THRESHOLD, and why it is this one.

   `|delta| / total` is not an arbitrary ratio. Because the score divides by the
   keyword count, it IS the fraction by which the list change alone moved the
   score. Adding 26 to reach a total of 30 grows the denominator by 26/30, so
   the score falls about 87% before a single ranking is considered; adding 1 to
   reach 7 moves it about 14%. At 0.2 the note appears exactly when the list
   change on its own moved the score by a fifth or more -- the point at which it
   is a plausible principal explanation for a fall rather than a footnote to it.

   So project 4 is captioned and project 1, at +1 on seven keywords, is not, and
   that restraint is the point: a note on every non-zero delta trains people to
   skip the note on the one project where it matters.

   The rejected alternative was to model the score movement the change would
   cause and compare it against the observed one. More precise, and it would
   couple this file to `shared/scoring.py` -- if that formula ever changes, a
   note computed from a stale copy of it does not fail loudly, it quietly starts
   making false claims. This rule needs only the one property the design
   guarantees: that the score divides by the keyword count. */
const LIST_CHANGE_SHARE = 0.2;

export function keywordShift(data) {
   const m = data.movement;
   /* Strictly true. `comparable` is three-valued and null is not permission to
      attribute a change to a window we cannot confirm exists. */
   if (m.comparable !== true) return null;
   /* null is "no measurable change", 0 is "the list held". Neither is a
      finding, and they are not each other either. */
   if (m.keywordsDelta === null || m.keywordsDelta === 0) return null;

   const total = keywordTotal(data);
   if (total <= 0) return null;

   const share = Math.abs(m.keywordsDelta) / total;
   return { delta: m.keywordsDelta, share: share, material: share >= LIST_CHANGE_SHARE };
}

/* Did the mention rate's DENOMINATOR move enough to explain the rate moving?

   The exact analogue of keywordShift() above, for the second feature with the
   same defect. The visibility score divides by every tracked keyword, so adding
   26 of them drops the score without a ranking having moved; the mention rate
   divides by every answer collected, so adding four prompts drops the rate
   without a mention having been lost. Project 4 is the second case: its stored
   series runs 2-of-4 then 2-of-8, 2-of-8, 2-of-8, and the numerator is 2 at
   every point. The "fall from 50% to 25%" is four prompts being added.

   THRESHOLD, AND WHY THERE IS ONE. `answers_delta` is non-zero on any run that
   added or lost a prompt, and a caption that fires on the common case trains
   people to skip the one that matters -- which would cost exactly the reader
   this note exists for. Same share rule and same 0.2 as the keyword list, and
   for the same reason: it needs only the property the design guarantees, that
   the rate divides by the answer count. Project 4 is 4/8 = 0.50, well clear.

   Independent of `significant`. The statistical verdict and the compositional
   one are two different objections to drawing a decline: a change can be inside
   the interval AND be denominator movement, and a change outside the interval
   can still be denominator movement. Neither subsumes the other, so this note
   is not gated on the flag. */
const ANSWER_CHANGE_SHARE = 0.2;

export function answerShift(ai) {
   const c = ai.change;
   /* `available` false means every other field on the comparison is null; a
      share computed from a null denominator is not a finding. */
   if (!c.available) return null;
   /* null is "not compared", 0 is "the answer set held". Neither is a finding,
      and they are not each other either. */
   if (c.answersDelta === null || c.answersDelta === 0) return null;
   if (ai.total <= 0) return null;

   const share = Math.abs(c.answersDelta) / ai.total;
   return { delta: c.answersDelta, share: share, material: share >= ANSWER_CHANGE_SHARE };
}

/* The window this comparison actually covers, in days.

   `window_days` is what was ASKED FOR; on a project younger than it, the
   comparison silently shortens to the history available and `window_days` keeps
   reporting 7 regardless. Project 4 is five days old, so its counters and its
   keyword delta span four days while the payload still says seven -- and the
   panel printed "in the last 7 days" over a measurement that covered four.
   Project 2 is worse: two days reported as seven.

   That is the same fault as a zero for a reading nobody took, one level up --
   the number is real and the window it is attributed to is not. `window_actual`
   is the API's answer; until it arrives this falls back to `window_days`, which
   is what the page said before and no worse. */
export const movementWindow = (movement) => {
   if (movement.windowActual !== null && movement.windowActual > 0) return movement.windowActual;
   return movement.windowDays > 0 ? movement.windowDays : 7;
};

/* The window, as the reader sees it: a figure and its unit, or a range.

   `movementWindow()` above stays the number everything non-copy reads; this is
   only the phrase, and the flag gates the phrase rather than the data.

   Why a range at all. Spans are per keyword, so `window_actual` is a ceiling
   rather than one shared window. A ceiling is still true of a NEGATIVE claim --
   a keyword cannot have moved in days it did not exist -- so on a project where
   the short-measured keywords are absent or merely held, the single figure is
   honest and the range would be noise. Project 1 is exactly that: its spans are
   6 and 7 and it has two movers, but both movers are full-span, so "in the last
   6-7 days" there would be precision about nothing.

   It stops being merely a ceiling when a keyword that MOVED was measured over a
   shorter span, because then a real change is being dated to a window it never
   had. `window_mixed` is the API's answer to that one question, and it is the
   only thing that opens the range.

   So the extra words are spent only where they change what the reader
   concludes -- the same test as the coverage-gap caption threshold. Range or
   figure, never both: two numbers and an explanation is how the panel this
   replaced got bloated. */
export function windowPhrase(movement) {
   const days = movementWindow(movement);
   const low = movement.windowMin;

   /* Every one of these falls back to the figure rather than inventing a
      range: no flag, no low bound, a low bound that is not lower, or a
      degenerate one. A range needs two real numbers. */
   if (movement.windowMixed === true && low !== null && low > 0 && low < days) {
      return low + "\u2013" + days + " days";
   }
   return days + (days === 1 ? " day" : " days");
}

/* MOVEMENT, resolved to one of three states rather than three numbers.

   "measured"    -- something moved, and the counts mean what they say.
   "unmeasured"  -- the API says there is no second reading to compare against.
   "still"       -- there is a comparison and nothing in it moved, or the API
                    did not say whether there is one. Both are reported as
                    "no movement recorded", which is true either way; only the
                    first can also say how many snapshots exist. */
export function movementView(movement) {
   const moved = movement.improved + movement.declined;
   if (movement.comparable === false) {
      return { state: "unmeasured", moved: 0 };
   }
   if (moved === 0) {
      return { state: "still", moved: 0 };
   }
   return { state: "measured", moved: moved };
}
