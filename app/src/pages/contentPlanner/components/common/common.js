import React from "react";
import { Tsk } from "../../../commonComponents/parts";

const cleanPercentage = (percentage) => {
  const tooLow = !Number.isFinite(+percentage) || percentage < 0;
  const tooHigh = percentage > 100;
  return tooLow ? 0 : tooHigh ? 100 : +percentage;
};

const Circle = ({ r, cx, cy, colour, pct }) => {
  const circ = 2 * Math.PI * r;
  const strokePct = ((100 - pct) * circ) / 100;
  return (
    <circle
      r={r}
      cx={cx}
      cy={cy}
      fill="transparent"
      stroke={strokePct !== circ ? colour : ""} // remove colour as 0% sets full circumference
      strokeWidth={"10px"}
      strokeDasharray={circ}
      strokeDashoffset={pct ? strokePct : 0}
      strokeLinecap="round"
    ></circle>
  );
};


const Text1 = ({ x, y, fsz, cl }) => {
  return (
    <text
      x={x}
      y={y}
      fontSize={fsz}
      style={{ fill: 'currentColor' }}
      color={cl}> /100 </text>
  )
}
const Text2 = ({ x, y, fsz, colour, tx }) => {
  return (
    <text
      x={x}
      y={y}
      fontSize={fsz}
      className="fM"
      fontFamily={"Bold"}
      style={{ fill: colour }}
    >{tx}</text>
  )
}

const Text3 = ({ x, y, fsz, percentage, loading, colour }) => {
  return (
    <text
      x={x}
      y={y}
      dominantBaseline="central"
      textAnchor="middle"
      fontSize={fsz}
      fontFamily={"Bold"}
      style={{ fill: colour }}

    >
      {loading ? <Tsk width={20} /> : percentage.toFixed(0)}
    </text>
  );
};

const Pie = ({ type, serpscore, yserpscore, loading, res, firstcolor, secondcolor, text }) => {
  const pct = cleanPercentage(serpscore || 0);
  return (
    <svg width={150} height={150} className="overview_pie_chart">
      <g transform={`rotate(-90 ${"50 50"})`}>
        <Circle r={60} cx={20} cy={80} colour={firstcolor} />
        <Circle r={60} cx={20} cy={80} colour={secondcolor} pct={pct} />
      </g>
      <Text3 x="43%" y="48%" fsz="25px" percentage={pct} colour="#0a0a0a" />
      <Text1 x="58%" y="54%" fsz="10px" />
      <Text2 x="34%" y="67%" fsz="17px" tx={text} colour={secondcolor} />
    </svg>
  );
};

export default Pie;
