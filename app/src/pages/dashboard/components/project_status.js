import React from "react";
import { Tooltip, Zoom } from "@mui/material";
import { Arrow } from "../../common_fun";

/* One counter in a project row: number, direction.

   It used to carry its own micro-label, which meant the same three words were
   set in uppercase once per project -- sixty labels on a page of twenty. The
   labels are constant down a column, so the list states them once in its header
   and a row is left holding only what differs. The label is still in the DOM,
   hidden (.prjSrOnly): this is a grid of divs rather than a table, so nothing
   associates a number with a header for a screen reader, and the stacked band
   has no header at all and shows the label again.

   Direction still comes from <Arrow>, which knows that "Declined" inverts (more
   declines is --down), and draws an arrow as well as colouring it.

   `title` is the semantic key -- <Arrow> matches on it -- so it must not be
   reworded for display. `label` is what the reader hears; it defaults to the
   title. */
const ProjectMetric = ({ title, label, kvalue, className }) => {
   const series = Array.isArray(kvalue) ? kvalue : [];
   const value = series.length > 0 ? Math.abs(series[0]) : 0;
   const known = series.length > 1;
   const prev = known ? Math.abs(series[1]) : value;

   return (
      <div className={"prjMetric" + (className ? " " + className : "")}>
         <span className="prjSrOnly">{label || title}</span>
         <Tooltip
            title={<>Yesterday, it was {known ? prev : <span className="newlightTxtClr fM">not available</span>}</>}
            TransitionComponent={Zoom}
            placement="top"
            classes={{ tooltip: "Tltpsmall" }}
         >
            <span className="prjMetricValue">
               <span className="prjNum">{value}</span>
               {/* The arrow keeps its slot whether or not there is an arrow to
                   draw, so the digits stay in line down the column. */}
               <span className="prjTrend">
                  <Arrow status={value - prev} type={title} y_sts={prev} tooltip={false} />
               </span>
            </span>
         </Tooltip>
      </div>
   );
};

export default ProjectMetric;
