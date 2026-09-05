import React from "react";
import {Tsk} from "../commonComponents/parts";

const cleanPercentage = (percentage) => {
  const tooLow = !Number.isFinite(+percentage) || percentage < 0;
  const tooHigh = percentage > 100;
  return tooLow ? 0 : tooHigh ? 100 : +percentage;
};

const Circle = ({ r, cx, cy, colour, pct }) => {
  // const r = r;
  const circ = 2 * Math.PI * r;
  const strokePct = ((100 - pct) * circ) / 100;
  return (
    <circle
      r={r}
      cx={cx}
      cy={cy}
      fill="transparent"
      stroke={strokePct !== circ ? colour : ""} // remove colour as 0% sets full circumference
      strokeWidth={"4px"}
      strokeDasharray={circ}
      strokeDashoffset={pct ? strokePct : 0}
      strokeLinecap="round"
    ></circle>
  );
};

//
const Text = ({ x, y, fsz, percentage, loading }) => {
  return (
    <text
      x={x}
      y={y}
      dominantBaseline="central"
      textAnchor="middle"
      fontSize={fsz}
      fontFamily={"Bold"}
    >
      { loading ? <Tsk width={20} /> : percentage.toFixed(0) }
    </text>
  );
};

/* Ink over a hairline track: a score is a quantity, not an action. The old
   `colour`/`bgColour` props were never read, so they are gone. */
export const SmallPie = ({ serpscore, loading }) => {
  const pct = cleanPercentage(serpscore || 0);
  return (
    <svg width={45} height={45}>
      <g transform={`rotate(-90 ${"17 20"})`}>
        <Circle r={20} cx={15} cy={25} colour={loading ? "var(--surface-2)" : "var(--line-2)"} />
        <Circle r={20} cx={15} cy={25} colour={loading ? "var(--surface-2)" : serpscore > 0 ? "var(--ink)" : "var(--line)"} pct={pct} />
      </g>
      <Text x="49%" y="49%" fsz="16px" percentage={pct} loading={loading} />
    </svg>
  );
};

/* The ring reports the direction of the score, so it takes the rank-direction
   tokens and nothing else: --up rising, --down dropping, --flat unchanged.
   It used to draw those three states in #1a3cff / #CF4343 / #43CF62 -- blue for
   a rise and a bright green for NO change, which is the reserved "improved"
   green spent on the one state that has not improved. A 37/100 in a green ring
   reads as a good score; it is neither good nor a change. The track behind it
   is --line, because it is chrome and carries no state. */
const ringColour = (delta) => (
  delta > 0 ? "var(--up)" : delta < 0 ? "var(--down)" : "var(--flat)"
);

const Pie = ({ type, serpscore, yserpscore, loading }) => {
  const pct = cleanPercentage(serpscore || 0);
  const delta = serpscore - yserpscore;
  return (
    <svg width={65} height={65}>
      <g transform={`rotate(-90 ${"25 25"})`}>
        <Circle r={25} cx={20} cy={30} colour={loading ? "var(--surface-2)" : "var(--line)"} />
        <Circle r={25} cx={20} cy={30} colour={loading ? "var(--surface-2)" : ringColour(delta)} pct={pct} />
      </g>
      {/* `loading` was never forwarded here, so a card still waiting on
          /projectoverview printed a confident 0 out of 100 for as long as the
          request took. A score that has not arrived is not a score of zero. */}
      <Text x="47%" y="47%" fsz="20px" percentage={pct} loading={loading} />
    </svg>
  );
};

export default Pie;
