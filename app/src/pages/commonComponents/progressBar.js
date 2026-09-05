import React from "react";

/* Geometry (height, radius, spacing) lives in _surfaces.scss under .meterTrack
   / .meterFill so every meter in the app is the same shape. The caller supplies
   only the two colours and the percentage, because on the usage cards the fill
   colour is what encodes how close the meter is to its cap.

   The fill used to animate its own width. docs/DESIGN.md allows a transition on
   colour, opacity and transform only -- never on width -- so the fill now
   simply lands at its value. */
function ProgressBar({ bgcolor, bglightcolor, completed }) {
  return (
    <div className="meterTrack" style={{ backgroundColor: bglightcolor }}>
      <div
        className="meterFill"
        style={{ width: `${completed}%`, backgroundColor: bgcolor }}
      />
    </div>
  );
}

export default ProgressBar;
