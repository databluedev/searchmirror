import React from "react";
import ReactApexChart from "react-apexcharts";
import { Panel } from "./panel";
import CHART from "../../commonComponents/chart_palette";
import { staticChart, axisStyle } from "./chart_base";
import { whenLabel, windowPhrase } from "../dashboard_data";

/* VISIBILITY TREND -- the hero, and the only chart on the page with an axis.

   Ink, not a series colour. There is one series and its own label names it, so
   a palette slot would be spent distinguishing it from nothing; docs/DESIGN.md
   is monochrome editorial and this is what that looks like at chart scale --
   a thin dark line over recessive rules.

   The y axis starts at zero and is stated, and that is the whole reason it is
   drawn at all. A line auto-scaled to its own extremes turns any short run into
   a cliff whatever the numbers are: 44 -> 37 and 90 -> 4 draw the identical
   descent. Against a stated floor the fall is in proportion to the score.

   No marker on every point. A marker per reading turns a nine-point series into
   a row of dots and implies each one is a datum worth reading off; only the
   latest is, so only the latest gets one. Under four readings every point is
   marked instead -- three points are three measurements and not yet a trend,
   and a bare line between them would claim otherwise. */

const HEIGHT = 178;

/* A round ceiling above the best reading, in tens.

   Apex's own "nice scale" only works when it owns the maximum, and it cannot be
   allowed to: left alone it fits the axis to the data and a 44 -> 37 run
   becomes a cliff. Setting an exact maximum keeps the floor at zero but gives
   labels like 55 and 28, so the maximum is rounded here instead and the axis
   reads 0 / 30 / 60.

   Capped at 100, because the score is one: it has always been clamped to 0-100.
   Without the cap a project scoring 100 got an axis running to 120 and a line
   sitting below a ceiling that cannot be reached. */
const ceilingFor = (points) => {
   const peak = Math.max.apply(null, points);
   return Math.min(100, Math.max(10, Math.ceil((peak * 1.2) / 10) * 10));
};

function Line({ points }) {
   const ceiling = ceilingFor(points);
   const few = points.length < 4;

   const options = {
      ...staticChart("area", HEIGHT),
      colors: [CHART.label],
      /* A wash under the line, not a colour. Anchoring the axis at zero leaves
         a lot of plot below a mid-range score, and a bare stroke floating in it
         reads as an unfinished chart; the fill ties the series to its own floor
         at an opacity low enough that it is a tone rather than an area. */
      fill: { type: "solid", opacity: 0.06 },
      stroke: { width: 2, curve: "straight", lineCap: "round" },
      dataLabels: { enabled: false },
      /* Horizontal rules only. Vertical ones would divide the series by
         reading index, which is not a unit anybody reads off this chart.

         `borderColor` is set to the palette's annotation ink and then taken
         back down to --line-2 by a stroke rule in style.scss. Apex needs a
         concrete string here and the palette has no rule-weight entry; the
         stylesheet is the only place the real token can be applied, and a
         gridline at --ink-4 would be heavier than the series. */
      grid: {
         show: true,
         borderColor: CHART.note,
         strokeDashArray: 0,
         xaxis: { lines: { show: false } },
         yaxis: { lines: { show: true } },
         padding: { top: 0, right: 8, bottom: 0, left: 4 },
      },
      markers: {
         size: few ? 4 : 0,
         strokeWidth: 0,
         colors: [CHART.label],
         /* The latest reading, always marked. It is the number in the stat row
            above, and the dot is what ties the two together. */
         discrete: few
            ? []
            : [{ seriesIndex: 0, dataPointIndex: points.length - 1, size: 4, fillColor: CHART.label, strokeColor: CHART.label }],
      },
      xaxis: {
         labels: { show: false },
         axisBorder: { show: false },
         axisTicks: { show: false },
         tooltip: { enabled: false },
         crosshairs: { show: false },
      },
      yaxis: {
         show: true,
         min: 0,
         max: ceiling,
         forceNiceScale: false,
         tickAmount: 2,
         labels: { style: axisStyle, formatter: (value) => Math.round(value) },
         axisBorder: { show: false },
         axisTicks: { show: false },
      },
   };

   return (
      <div
         className="dashTrend"
         role="img"
         aria-label={"Visibility over the last " + points.length + " readings"}
      >
         <ReactApexChart options={options} series={[{ name: "Visibility", data: points }]} type="area" height={HEIGHT} />
      </div>
   );
}

const MOVES = [
   { key: "improved", label: "improved", tone: "isUp" },
   { key: "declined", label: "declined", tone: "isDown" },
   { key: "unchanged", label: "held", tone: "isFlat" },
];

/* Movement lives under the trend rather than in a panel of its own, because it
   is the same subject at a different resolution: the line is the score over
   time, this is what the keywords did over the last window.

   It never prints three zeros. The panel it replaces did, on a project with one
   snapshot, and a zero is a measurement -- printing one for a measurement that
   was never taken is indistinguishable from a project that has genuinely gone
   flat. `comparable` is the API's answer to which of those it is.

   The colours are the one place --up / --down / --flat belong: rank direction
   is the only job those three tokens have. They are carried by a mark beside
   the number, never by the number itself, which stays ink. */
function Movement({ movement, view }) {
   /* The window measured, not the window configured -- and as a range on the
      one occasion that matters, when a keyword that moved was measured over a
      shorter span than the label claims. A project younger than `window_days`
      gets a shorter comparison and the payload keeps reporting the configured
      figure, so this sentence used to attribute a four-day reading to seven
      days. */
   const window = windowPhrase(movement);

   if (view.state === "unmeasured") {
      const when = whenLabel(movement.firstComparisonAt);
      return (
         <p className="dashMove__say">
            {movement.snapshots === 1 ? "One ranking snapshot so far" : "Not enough ranking snapshots yet"}, so there
            is nothing to compare.{" "}
            <span className="dashMove__when">
               {when ? "First comparison " + when + "." : "The first comparison lands after the next run."}
            </span>
         </p>
      );
   }

   if (view.state === "still") {
      return (
         <p className="dashMove__say">
            No movement recorded in the last {window}.{" "}
            {movement.absent > 0 ? (
               <span className="dashMove__when">
                  {movement.absent} {movement.absent === 1 ? "keyword has" : "keywords have"} no position to compare.
               </span>
            ) : null}
         </p>
      );
   }

   return (
      <ul className="dashMove">
         {MOVES.map(({ key, label, tone }) => (
            <li key={key} className={"dashMove__item " + tone}>
               <span className="dashMove__swatch" aria-hidden="true" />
               <span className="dashMove__value">{movement[key]}</span>
               <span className="dashMove__label">{label}</span>
            </li>
         ))}
         <li className="dashMove__item dashMove__item--note">in the last {window}</li>
      </ul>
   );
}

/* Why the line may have moved without a ranking moving.

   This sits under the chart rather than beside the KEYWORDS tile because the
   two answer different questions. The tile answers "did the list change?"; this
   answers the one the chart provokes, "did my rankings collapse?" The false
   conclusion forms here, so the correction belongs here. Both are the same
   fact, and the tile keeps its own figure.

   Set in --ink-2 rather than the caption grey: it is a statement a reader must
   not skim on the one project where it applies, and a footnote under a cliff is
   exactly what gets skimmed. It is not --warn -- nothing has gone wrong, and
   that token belongs to a failed run.

   No day count in the wording. It is the same window as the movement line below
   it, which states the number once. */
function ListChange({ shift }) {
   const added = shift.delta > 0;
   const n = Math.abs(shift.delta);

   return (
      <p className="dashTrend__note">
         <span className="dashTrend__noteFig">
            {n} {n === 1 ? "keyword" : "keywords"} {added ? "added" : "removed"}
         </span>{" "}
         in this window. The score divides by every tracked keyword, so {added ? "a fall" : "a rise"} here need not be
         {added ? " lost rankings" : " gained rankings"}.
      </p>
   );
}

export default function TrendPanel({ visibility, movement, view, shift }) {
   const points = visibility.spark;

   return (
      <Panel label="Visibility trend" className="dashTrendPanel">
         {points.length < 2 ? (
            <p className="dashPanel__empty">
               One reading so far, so there is no line yet. It starts at the second.
            </p>
         ) : (
            <Line points={points} />
         )}
         {shift && shift.material ? <ListChange shift={shift} /> : null}
         <div className="dashTrendPanel__foot">
            <Movement movement={movement} view={view} />
         </div>
      </Panel>
   );
}
