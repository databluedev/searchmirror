import * as React from "react";

import COUNTRY_NAMES from "./country_names";

// Country flags are served from this app's own public/flags directory.
// They used to be hotlinked from a third-party flag CDN, which handed that CDN
// the IP, referrer and user-agent of everyone who loaded a table, a region
// dropdown or -- worst of all -- a public Live Report, where the people beaconed
// are the agency's clients rather than its own users. DESIGN.md non-negotiable
// #7 forbids shipping anything that calls a third-party account or service, so
// the images are vendored instead. Nothing in here touches the network.

const FLAG_DIR = "/flags";

// The vendored files are named for the lowercase ISO 3166-1 alpha-2 code, plus
// the handful of subdivision codes the data can carry (gb-eng, us-ca, ...).
// Call sites pass the code straight off the API row, so normalise here rather
// than making each of them remember to lowercase it.
export function flagSrc(code) {
   const key = String(code == null ? "" : code).trim().toLowerCase();
   return `${FLAG_DIR}/${key}.png`;
}

// Accessible name for a flag, for the many places where the flag is the only
// thing on screen telling you which country a row belongs to.
export function countryName(code) {
   const key = String(code == null ? "" : code).trim().toLowerCase();
   if (!key) return "";
   return COUNTRY_NAMES[key] || key.toUpperCase();
}

// Every prop other than `code` is forwarded untouched, so each call site keeps
// its own className, width/height, inline style and loading behaviour.
// `alt` defaults to the country name because most flags here sit alone in a
// table cell; the dropdowns and menus that already print the country name
// beside the flag pass alt="" so it is not announced twice.
// forwardRef because several call sites hand the flag straight to a MUI
// Tooltip, which needs a ref on the underlying DOM node to anchor itself.
const CountryFlag = React.forwardRef(function CountryFlag(
   { code, alt, ...imgProps },
   ref
) {
   const src = flagSrc(code);
   const label = alt === undefined ? countryName(code) : alt;
   return <img ref={ref} {...imgProps} src={src} srcSet={`${src} 2x`} alt={label} />;
});

export default CountryFlag;
