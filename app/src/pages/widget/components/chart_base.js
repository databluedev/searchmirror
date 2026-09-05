import CHART from "../../commonComponents/chart_palette";

/* Shared ApexCharts configuration for the dashboard's three charts.

   Everything the library switches on by default and this design system does not
   want is switched off here, once, rather than forgotten in one of the three
   call sites: entry and update animations (docs/DESIGN.md allows none), the
   toolbar, zoom and selection, the hover brightness filter, and the legend --
   every series on this screen is labelled on its own axis.

   Tooltips are off on purpose. Each chart prints its values as data labels, so
   a tooltip would be a second copy of a number already on the screen, reachable
   only with a mouse -- which is also the reason the value has to be drawn
   rather than hovered for.

   `fontFamily: "inherit"` keeps the charts on the page's Space Grotesk without
   restating the stack; colours come from chart_palette.js, which is the one
   place concrete strings are allowed because Apex runs shading maths on them
   and cannot take a var(). */

export const staticChart = (type, height) => ({
   chart: {
      type: type,
      height: height,
      animations: { enabled: false },
      toolbar: { show: false },
      zoom: { enabled: false },
      selection: { enabled: false },
      parentHeightOffset: 0,
      fontFamily: "inherit",
      background: "transparent",
   },
   states: {
      hover: { filter: { type: "none" } },
      active: { filter: { type: "none" } },
   },
   legend: { show: false },
   tooltip: { enabled: false },
});

/* Axis text is chrome, so it takes --ink-3 rather than a series slot. */
export const axisStyle = {
   colors: CHART.axis,
   fontSize: "12px",
   fontWeight: 400,
};

/* A value printed on the chart is data, so it takes full-strength ink and the
   same tabular numerals every other column of numbers on this screen uses. */
export const valueStyle = {
   colors: [CHART.label],
   fontSize: "12px",
   fontWeight: 600,
};

export default staticChart;
