import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import "./keyword_config.scss";

import Cookies from "universal-cookie";
import axios from "axios";
import { toast } from "react-toastify";
import { Select, MenuItem, InputLabel } from "@mui/material";

import { Input, Para } from "../../commonComponents/parts";
import { ModalBox } from "../../commonComponents/Modals";
import { Button } from "@/components/ui/button";
import CountryFlag from "../../commonComponents/country_flag";
import { PRECEDENCE_NOTE } from "../../projectSettings/components/serp_depth";

// dev_style.scss:944 sets `.MuiModal-root { z-index: 9989 !important }` and
// :949 lifts `.Toggle-Modal` to 10000. A MUI select menu is also a
// .MuiModal-root, so it opens BEHIND every dialog in this app -- present in
// the accessibility tree, unclickable on screen. An inline z-index loses to
// that !important, so the lift is a rule of higher specificity in
// keyword_config.scss and this only names the class.
//
// It is also why the shared SelectLang / KNRSelectRegion are not reused here:
// they hardcode their own MenuProps and accept no className.
const MENU_PROPS = {
   className: "kwCfgMenu",
   PaperProps: { style: { maxHeight: 260, boxShadow: "0px 2px 4px #00000029" } },
};

// Re-exported so this page has one import site for the keyword config, and the
// sentence itself still has one definition.
export { PRECEDENCE_NOTE };

const authHeaders = () => {
   const cookies = new Cookies();
   return { Authorization: "Token " + cookies.get("session_token") };
};

const ids = () => {
   const cookies = new Cookies();
   return { userid: cookies.get("session_userid"), grpid: cookies.get("activegrp") };
};

// Rejects rather than resolving to a default: "the save failed" and "the value
// is X" must never render the same.
export const saveKeywordConfig = (kwid, patch) => {
   const { userid, grpid } = ids();

   return axios
      .post(
         global.apiurl + "/kwconfigsave",
         { userid: userid, grpid: grpid, kwid: kwid, ...patch },
         { headers: authHeaders() }
      )
      .then((response) => response.data)
      .then((res) => {
         if (res.status !== "true" || !res.cfg) {
            throw new Error(res.message || "Could not save this keyword's settings");
         }
         return res.cfg;
      })
      .catch((error) => {
         const body = error && error.response && error.response.data;
         throw new Error((body && body.message) || error.message || "Could not save this keyword's settings");
      });
};

const readTargetingOptions = (signal) => {
   const { userid, grpid } = ids();

   return axios
      .post(
         global.apiurl + "/getsetting",
         { userid: userid, grpid: grpid || 0 },
         { headers: authHeaders(), signal: signal }
      )
      .then((response) => response.data)
      .then((res) => {
         if (res.status !== "true") {
            throw new Error(res.message || "Could not load countries and languages");
         }
         return { regions: res.rg || [], languages: res.lnge || [] };
      });
};

const SOURCE_LABEL = {
   account: "Account default",
   project: "Project default",
   keyword: "Set for this keyword",
};

/* Says where a value came from, next to the value. A number on its own is what
   made the account and project settings look like they were being ignored. */
export function ConfigSource({ source }) {
   const label = SOURCE_LABEL[source];
   if (!label) {
      return null;
   }
   return (
      <span className={"kwCfgSource" + (source === "keyword" ? " isOverride" : "")}>{label}</span>
   );
}

export const pagesLabel = (pages) => (pages === 1 ? "1 page" : pages + " pages");

export const pagesCost = (pages) =>
   pages === 1
      ? "1 credit per check"
      : pages + " credits per check — DataBlue bills every page separately";

const depthName = (advanced) => (advanced ? "Advanced" : "Lite");

/* The rows the facts list gains. Kept here rather than in overview_tab so the
   value, the tier it came from and the cost stay described in one file. */
export function KeywordConfigFacts({ cfg }) {
   if (!cfg) {
      return null;
   }

   return (
      <>
         <div className="kwFact">
            <dt className="kwFactLabel">Pages per check</dt>
            <dd className="kwFactValue">
               <span>{pagesLabel(cfg.pages.value)}</span>
               <ConfigSource source={cfg.pages.source} />
               <span className="kwFactAside">{pagesCost(cfg.pages.value)}</span>
            </dd>
         </div>

         <div className="kwFact">
            <dt className="kwFactLabel">Extraction depth</dt>
            <dd className="kwFactValue">
               <span>{depthName(cfg.advanced.value)}</span>
               <ConfigSource source={cfg.advanced.source} />
               <span className="kwFactAside">
                  {cfg.advanced.value
                     ? "asks for Google's AI Overview; billed at the higher rate"
                     : "organic results and the non-AI blocks"}
               </span>
            </dd>
         </div>

         <div className="kwFact">
            <dt className="kwFactLabel">Rank counts when</dt>
            <dd className="kwFactValue">
               <span>{cfg.exactdomain ? "This exact page ranks" : "Any page on the domain ranks"}</span>
               <span className="kwFactAside">
                  {cfg.exactdomain
                     ? "only the tracked URL above is treated as yours"
                     : "the tracked URL above is the page you expect, not a requirement"}
               </span>
            </dd>
         </div>
      </>
   );
}

const INHERIT = "inherit";

/* Radio group. With an inheritLabel it gains a third state, "inherit", which is
   a real option rather than "whichever value happens to match the default" --
   clearing an override has to be something the user can express. Without one it
   is a plain two-way choice, for the fields that have no default to inherit. */
function OverrideChoice({ label, name, value, options, inheritLabel, onChange, disabled }) {
   const all = inheritLabel ? [{ value: INHERIT, name: inheritLabel }].concat(options) : options;

   return (
      <div className="kwCfgField">
         <div className="kwCfgFieldLabel">{label}</div>
         <div className="kwCfgOptions" role="radiogroup" aria-label={label}>
            {all.map((opt) => (
               <label
                  key={String(opt.value)}
                  className={"kwCfgOption" + (value === opt.value ? " isOn" : "")}
               >
                  <input
                     type="radio"
                     name={name}
                     checked={value === opt.value}
                     disabled={disabled}
                     onChange={() => onChange(opt.value)}
                  />
                  <span className="kwCfgOptionMark" aria-hidden="true" />
                  <span className="kwCfgOptionBody">
                     <span className="kwCfgOptionName">{opt.name}</span>
                     {opt.desc ? <span className="kwCfgOptionDesc">{opt.desc}</span> : null}
                  </span>
               </label>
            ))}
         </div>
      </div>
   );
}

export default function KeywordConfigDialog({ open, onClose, cfg, keyid, onSaved }) {
   const [options, setOptions] = useState(null);
   const [optionsError, setOptionsError] = useState("");
   const [saving, setSaving] = useState(false);
   const [error, setError] = useState("");

   // Form state. Seeded from cfg every time the dialog opens, so cancelling
   // and reopening never shows a half-edited value.
   const [url, setUrl] = useState("");
   const [edm, setEdm] = useState(false);
   const [platform, setPlatform] = useState("desktop");
   const [region, setRegion] = useState("");
   const [isocode, setIsocode] = useState("");
   const [countryname, setCountryname] = useState("");
   const [language, setLanguage] = useState("");
   const [pages, setPages] = useState(INHERIT);
   const [advanced, setAdvanced] = useState(INHERIT);

   useEffect(() => {
      if (!open || !cfg) {
         return undefined;
      }

      setUrl(cfg.url || "");
      setEdm(Boolean(cfg.exactdomain));
      setPlatform(cfg.platform || "desktop");
      setRegion(cfg.region || "");
      setIsocode(cfg.isocode || "");
      setCountryname(cfg.countryname || "");
      setLanguage(cfg.language || "");
      setPages(cfg.pages.override === null ? INHERIT : cfg.pages.override);
      setAdvanced(cfg.advanced.override === null ? INHERIT : cfg.advanced.override);
      setError("");

      const controller = new AbortController();
      readTargetingOptions(controller.signal)
         .then(setOptions)
         .catch((err) => {
            if (axios.isCancel(err)) {
               return;
            }
            // The two selects are hidden rather than drawn empty: an empty
            // country list reads as "no countries", which is not what is true.
            setOptionsError("Could not load the country and language lists. Reload to try again.");
         });

      return () => controller.abort();
   }, [open, cfg]);

   if (!cfg) {
      return null;
   }

   const pagesMax = (cfg.limits && cfg.limits.pagesMax) || 10;
   const resolvedPages = pages === INHERIT ? cfg.pages.inherited : pages;
   const resolvedAdvanced = advanced === INHERIT ? cfg.advanced.inherited : advanced;

   // A change to any of these three changes which Google search is run, so the
   // rank history already recorded was measured against a different question.
   const searchChanged =
      platform !== cfg.platform || region !== cfg.region || language !== cfg.language;

   const patch = () => {
      const body = {};
      if (url.trim() !== (cfg.url || "")) {
         body.url = url.trim();
      }
      if (edm !== Boolean(cfg.exactdomain)) {
         body.edm = edm;
      }
      if (platform !== cfg.platform) {
         body.platform = platform;
      }
      if (region !== cfg.region) {
         body.region = region;
      }
      if (language !== cfg.language) {
         body.language = language;
      }
      const nextPages = pages === INHERIT ? null : pages;
      if (nextPages !== cfg.pages.override) {
         body.pages = nextPages;
      }
      const nextAdvanced = advanced === INHERIT ? null : advanced;
      if (nextAdvanced !== cfg.advanced.override) {
         body.adv = nextAdvanced;
      }
      return body;
   };

   const submit = () => {
      const body = patch();
      if (Object.keys(body).length === 0) {
         onClose();
         return;
      }

      setSaving(true);
      setError("");
      saveKeywordConfig(keyid, body)
         .then((next) => {
            setSaving(false);
            onSaved(next);
            onClose();
            toast.success("Keyword settings saved. It will be checked this way from the next run.");
         })
         .catch((err) => {
            setSaving(false);
            setError(err.message);
         });
   };

   // Keyed by ISO code, which is unique; the Google domain and country name
   // are then read off the same row rather than tracked separately.
   const regionChange = (event) => {
      const selected = (options ? options.regions : []).find((r) => r.Rcd === event.target.value);
      if (!selected) {
         return;
      }
      setIsocode(selected.Rcd);
      setRegion(selected.RN);
      setCountryname(selected.Rcnt);
   };

   const pageOptions = [];
   for (let i = 1; i <= pagesMax; i += 1) {
      pageOptions.push(i);
   }

   return (
      <ModalBox className="light kwCfgModal" title="Keyword settings" open={open} onClose={onClose}>
         <div className="kwCfgBody">
            <Para class="kwCfgIntro">
               {PRECEDENCE_NOTE} Saving does not re-check this keyword — the next scheduled run
               uses the new settings.
            </Para>

            <div className="kwCfgGroup">
               <div className="kwCfgGroupTitle">What counts as your result</div>

               <div className="kwCfgField">
                  <InputLabel shrink htmlFor="kwcfg-url">
                     Target page <span className="redClr">*</span>
                  </InputLabel>
                  <Input
                     nolabel
                     id="kwcfg-url"
                     value={url}
                     onchange={(e) => setUrl(e.target.value)}
                     placeholder="example.com/blog/rank-higher-on-google"
                  />
                  <div className="kwCfgHelp">
                     The page you expect to rank for this keyword. It must be on this project's
                     own domain.
                  </div>
               </div>

               <OverrideChoice
                  label="Rank counts when"
                  name="kwcfg-edm"
                  value={edm}
                  options={[
                     {
                        value: false,
                        name: "Any page on the domain ranks",
                        desc:
                           "Whichever of your pages Google shows is recorded as your position. " +
                           "The target page above is then what you expected, not a requirement.",
                     },
                     {
                        value: true,
                        name: "Only the target page ranks",
                        desc:
                           "A different page of yours in the results is recorded as not ranking. " +
                           "Compared without the scheme, www. or a trailing slash.",
                     },
                  ]}
                  onChange={setEdm}
                  disabled={saving}
               />
            </div>

            <div className="kwCfgGroup">
               <div className="kwCfgGroupTitle">Which Google search is run</div>

               {optionsError ? (
                  <div className="kwCfgHelp">{optionsError}</div>
               ) : !options ? (
                  <div className="kwCfgHelp">Loading countries and languages…</div>
               ) : (
                  <>
                     <div className="kwCfgField">
                        <InputLabel shrink id="kwcfg-country-label">Country</InputLabel>
                        <Select
                           className="customSelect"
                           labelId="kwcfg-country-label"
                           value={isocode}
                           disabled={saving}
                           onChange={regionChange}
                           MenuProps={MENU_PROPS}
                           renderValue={() => (
                              <span className="kwCfgFlagRow">
                                 <CountryFlag className="flag md" code={isocode} width={18} height={12} alt="" />
                                 {region + " (" + countryname + ")"}
                              </span>
                           )}
                        >
                           {options.regions.map((r) => (
                              <MenuItem key={r.Rcd} value={r.Rcd}>
                                 <span className="kwCfgFlagRow">
                                    <CountryFlag className="flag md" code={r.Rcd} width={18} height={12} alt="" />
                                    {r.RN + " (" + r.Rcnt + ")"}
                                 </span>
                              </MenuItem>
                           ))}
                        </Select>
                     </div>

                     <div className="kwCfgField">
                        <InputLabel shrink id="kwcfg-language-label">Language</InputLabel>
                        <Select
                           className="customSelect"
                           labelId="kwcfg-language-label"
                           value={language}
                           disabled={saving}
                           onChange={(e) => setLanguage(e.target.value)}
                           MenuProps={MENU_PROPS}
                        >
                           {options.languages.map((l) => (
                              <MenuItem key={l.LN} value={l.LN}>{l.LN}</MenuItem>
                           ))}
                        </Select>
                     </div>
                  </>
               )}

               <OverrideChoice
                  label="Device"
                  name="kwcfg-platform"
                  value={platform}
                  options={[
                     { value: "desktop", name: "Desktop" },
                     { value: "mobile", name: "Mobile" },
                  ]}
                  onChange={setPlatform}
                  disabled={saving}
               />

               {searchChanged ? (
                  <div className="kwCfgWarn">
                     Country, language and device each change which Google search is run. The rank
                     history already recorded was measured on the previous combination and is kept
                     as it is, so positions before and after this change are not directly
                     comparable.
                  </div>
               ) : null}
            </div>

            <div className="kwCfgGroup">
               <div className="kwCfgGroupTitle">What each check costs</div>

               <div className="kwCfgField">
                  <InputLabel shrink id="kwcfg-pages-label">Pages per check</InputLabel>
                  <Select
                     className="customSelect"
                     labelId="kwcfg-pages-label"
                     value={pages}
                     disabled={saving}
                     onChange={(e) => setPages(e.target.value)}
                     MenuProps={MENU_PROPS}
                  >
                     <MenuItem value={INHERIT}>
                        {"Use the account setting — " + pagesLabel(cfg.pages.inherited)}
                     </MenuItem>
                     {pageOptions.map((n) => (
                        <MenuItem key={n} value={n}>
                           {pagesLabel(n) + (n === 1 ? " (top 10 results)" : " (about " + n * 10 + " results)")}
                        </MenuItem>
                     ))}
                  </Select>
                  <div className="kwCfgHelp">
                     {pagesCost(resolvedPages)}. A rank below the pages you pull is recorded as not
                     ranking. Pages for every other keyword is set on the{" "}
                     <Link className="kwCfgLink" to="/settings/apikey">DataBlue API Key tab</Link>.
                  </div>
               </div>

               <OverrideChoice
                  label="Extraction depth"
                  name="kwcfg-adv"
                  value={advanced}
                  inheritLabel={"Use the project setting — " + depthName(cfg.advanced.inherited)}
                  options={[
                     {
                        value: false,
                        name: "Lite",
                        desc:
                           "Organic results plus ads, featured snippets, People Also Ask, the " +
                           "local pack, knowledge panel, videos and related searches.",
                     },
                     {
                        value: true,
                        name: "Advanced",
                        desc:
                           "Also asks for Google's AI Overview. Billed at a higher rate per " +
                           "check, and it multiplies with the pages setting above.",
                     },
                  ]}
                  onChange={setAdvanced}
                  disabled={saving}
               />

               <div className="kwCfgHelp">
                  This keyword will be checked at {depthName(resolvedAdvanced)},{" "}
                  {pagesLabel(resolvedPages)} per check.
               </div>
            </div>

            {error ? <div className="kwCfgError">{error}</div> : null}

            <div className="kwCfgActions">
               <Button type="button" variant="secondary" onClick={onClose} disabled={saving}>
                  Cancel
               </Button>
               <Button type="button" variant="primary" onClick={submit} disabled={saving}>
                  {saving ? "Saving…" : "Save settings"}
               </Button>
            </div>
         </div>
      </ModalBox>
   );
}
