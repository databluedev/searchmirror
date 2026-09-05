import React from "react";
import { SFLinkIcon, SFTwitterIcon, SFLocalPackIcon, SFImageIcon, SFNewsIcon, SFLocationIcon, SFRelatedQuestionIcon, SFVideoPackIcon, FeatureSnptIcon, AdsIcon, AdbottomIcon, AdTopBottomIcon, AdTopIcon, SFKnwlgPanelIcon } from "../commonComponents/icons";
import { SFRatingClrIcon } from "../common_fun";
import { ParaLg } from "../commonComponents/parts";

// One source for every SERP-feature code the keyword table can paint. The same
// fifteen code/icon/label triples used to be written out twice -- once as the
// per-row tooltips in data_table.js, once as the static legend under the table
// -- which is how the two drift. The table reads these per row; the legend
// reads the ones the loaded keywords actually trigger.

// These icons paint their paths with `props.color || "currentColor"`, and a
// var() does not resolve inside an SVG presentation attribute -- passing
// color="var(--accent)" leaves the fill unresolved. The colour goes on a
// wrapper as CSS instead, and the SVG picks it up through currentColor.
// display:contents keeps the wrapper out of layout entirely.
const accentIcon = (icon) => <span style={{ color: "var(--accent)", display: "contents" }}>{icon}</span>;

// Codes that map one-to-one onto an icon. This is the order the table paints
// them in, after the rating / ads / featured-snippet groups below.
export const SIMPLE_FEATURES = [
   { code: "knw", label: "The result has a knowledge panel", icon: <SFKnwlgPanelIcon /> },
   { code: "slrs", label: "The result has a sitelink", icon: <SFLinkIcon /> },
   { code: "twrs", label: "The result has twitter pack", icon: <SFTwitterIcon /> },
   { code: "lcrs", label: "The result has a local pack", icon: <SFLocalPackIcon /> },
   { code: "imrs", label: "The result has an image pack", icon: <SFImageIcon /> },
   { code: "vdrs", label: "The result has a video pack", icon: <SFVideoPackIcon /> },
   { code: "nwrs", label: "The result has news pack", icon: <SFNewsIcon /> },
   { code: "rqrs", label: "The result has related questions", icon: <SFRelatedQuestionIcon /> },
   { code: "mprs", label: "The result has a map pack", icon: <SFLocationIcon /> },
];

// Mutually exclusive: a row paints one ad icon, the first of these it matches.
export const AD_FEATURES = [
   { code: "Ain", label: "You are in Google Ads", icon: accentIcon(<AdsIcon />) },
   { code: "Atb", label: "Ads found above & below the fold", icon: <AdTopBottomIcon /> },
   { code: "At", label: "Ads found above the fold", icon: <AdTopIcon /> },
   { code: "Ab", label: "Ads found below the fold", icon: <AdbottomIcon /> },
];

// Also mutually exclusive: fs1 ("you are in it") outranks fs0 ("it exists").
export const SNIPPET_FEATURES = [
   { code: "fs1", label: "You are in the featured snippets", icon: accentIcon(<FeatureSnptIcon />) },
   { code: "fs0", label: "The result has a featured snippet", icon: <FeatureSnptIcon /> },
];

// One code -- 'rv' -- covers the whole rating scale, so these key off the band
// SFRatingClrIcon colours the star by rather than off a code of their own.
// Their table tooltip is the rating value, not this text, so only the legend
// uses these labels.
export const RATING_FEATURES = [
   { code: "rv:high", label: "Your rating ranges between 4 to 5", icon: <SFRatingClrIcon value={5} /> },
   { code: "rv:mid", label: "Your ratings ranges between 2 to 4", icon: <SFRatingClrIcon value={3} /> },
   { code: "rv:low", label: "Your ratings ranges below 2", icon: <SFRatingClrIcon value={1} /> },
   { code: "rv:none", label: "You have no ratings", icon: <SFRatingClrIcon value={0} /> },
];

// Mirrors SFRatingClrIcon's branches exactly -- a missing or "-" rating parses
// to NaN, fails every comparison and lands on "no ratings", which is the same
// star the icon draws for it.
const ratingBand = (value) => {
   const rating = parseFloat(value);
   if (rating >= 4) return "rv:high";
   if (rating >= 2) return "rv:mid";
   if (rating !== 0 && rating < 2) return "rv:low";
   return "rv:none";
};

const FEATURES_BY_CODE = new Map(
   [...SIMPLE_FEATURES, ...AD_FEATURES, ...SNIPPET_FEATURES, ...RATING_FEATURES].map((feature) => [feature.code, feature])
);

// Reading order for the legend, which groups by kind rather than by the order
// the table paints a row.
const LEGEND_ORDER = [
   "slrs", "imrs", "rqrs", "lcrs", "twrs", "vdrs", "nwrs", "mprs",
   "Ain", "Atb", "At", "Ab",
   "rv:high", "rv:mid", "rv:low", "rv:none",
   "fs1", "fs0",
   "knw",
];

// The codes the loaded keywords actually carry. `sp` is the same value the
// table hands to snippetFeatures, so the legend cannot show an icon the table
// does not, and the mutually-exclusive groups resolve the way a row does.
export const presentFeatures = (rows) => {
   const present = new Set();

   (rows || []).forEach((row) => {
      const codes = row && row.sp;
      if (!codes || codes.length === 0) return;

      SIMPLE_FEATURES.forEach((feature) => {
         if (codes.includes(feature.code)) present.add(feature.code);
      });

      const ad = AD_FEATURES.find((feature) => codes.includes(feature.code));
      if (ad) present.add(ad.code);

      const snippet = SNIPPET_FEATURES.find((feature) => codes.includes(feature.code));
      if (snippet) present.add(snippet.code);

      if (codes.includes("rv")) present.add(ratingBand(row.trg));
   });

   return present;
};

export const legendFeatures = (present) => LEGEND_ORDER.filter((code) => present.has(code)).map((code) => FEATURES_BY_CODE.get(code));

// A project typically triggers two or three of the fifteen, so this is an
// inline wrapping row rather than a four-column grid -- a grid holding three
// items reads as a broken layout. Renders nothing when nothing is present.
export function SerpLegend({ rows }) {
   const features = React.useMemo(() => legendFeatures(presentFeatures(rows)), [rows]);

   if (features.length === 0) return null;

   return (
      <section className="SR-legend m-b20">
         <ParaLg class="fB m-b20 m-t25 lineHAuto">
            SERP Legend
         </ParaLg>
         <ul className="flex flex-wrap items-center gap-[var(--sp-3)_var(--sp-5)] list-none m-0 p-0">
            {features.map((feature) => (
               <li
                  key={feature.code}
                  className="flex items-center gap-[var(--sp-2)]"
               >
                  <span className="d-flex">{feature.icon}</span>
                  <span className="f12x">{feature.label}</span>
               </li>
            ))}
         </ul>
      </section>
   );
}
