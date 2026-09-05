import React, { useState, useEffect } from "react";
import "./serp_depth.scss";

import Cookies from "universal-cookie";
import axios from "axios";
import { toast } from "react-toastify";

import { Para, SmallText, TextLg, Tsk } from "../../commonComponents/parts";
import { ModalBox, ConfirmDialog } from "../../commonComponents/Modals";

// POST /prjctserpmode reads without "adv" and writes with it. /projectsetting
// also publishes srp_adv but reads request.POST, so a JSON body reaches it empty.
const SERP_MODE_URL = "/prjctserpmode";

export const DEPTH_LITE = false;
export const DEPTH_ADVANCED = true;

// A keyword may override this project's depth and the account's pages. One
// sentence, used verbatim here and on the keyword detail page -- two settings
// that can disagree need one explanation, not two that drift apart.
export const PRECEDENCE_NOTE =
   "A keyword uses its own setting when it has one, and the project or account " +
   "default when it does not.";

// Reads and clears per-keyword overrides for one project. Posting without a
// scope counts them and changes nothing.
const OVERRIDE_URL = "/kwconfigreset";

const OPTIONS = [
   {
      value: DEPTH_LITE,
      name: "Lite",
      tag: "Default",
      desc:
         "Organic results plus ads, featured snippets, People Also Ask, the local pack, " +
         "knowledge panel, videos and related searches.",
   },
   {
      value: DEPTH_ADVANCED,
      name: "Advanced",
      tag: "",
      desc: "Also asks for Google's AI Overview — the AI answer and the sources it cites.",
   },
];

const authHeaders = () => {
   const cookies = new Cookies();
   return { Authorization: "Token " + cookies.get("session_token") };
};

// Resolves to a boolean or rejects. Never resolves to a default: "could not read
// it" and "it is Lite" must not render as the same radio.
export const readSerpDepth = (grpid, signal) => {
   const cookies = new Cookies();
   const userid = cookies.get("session_userid");

   return axios
      .post(
         global.apiurl + SERP_MODE_URL,
         { userid: userid, grpid: grpid },
         { headers: authHeaders(), signal: signal }
      )
      .then((response) => response.data)
      .then((res) => {
         if (res.status !== "true") {
            throw new Error(res.message || "Could not read extraction depth");
         }
         return Boolean(res.adv);
      });
};

export const writeSerpDepth = (grpid, advanced) => {
   const cookies = new Cookies();
   const userid = cookies.get("session_userid");

   return axios
      .post(
         global.apiurl + SERP_MODE_URL,
         { userid: userid, grpid: grpid, adv: Boolean(advanced) },
         { headers: authHeaders() }
      )
      .then((response) => response.data)
      .then((res) => {
         if (res.status !== "true") {
            throw new Error(res.message || "Could not save extraction depth");
         }
         return Boolean(res.adv);
      });
};

export const readOverrideCounts = (grpid, signal) => {
   const cookies = new Cookies();

   return axios
      .post(
         global.apiurl + OVERRIDE_URL,
         { userid: cookies.get("session_userid"), grpid: grpid },
         { headers: authHeaders(), signal: signal }
      )
      .then((response) => response.data)
      .then((res) => {
         if (res.status !== "true") {
            throw new Error(res.message || "Could not read keyword overrides");
         }
         return res;
      });
};

export const clearOverrides = (grpid, scope) => {
   const cookies = new Cookies();

   return axios
      .post(
         global.apiurl + OVERRIDE_URL,
         { userid: cookies.get("session_userid"), grpid: grpid, scope: scope },
         { headers: authHeaders() }
      )
      .then((response) => response.data)
      .then((res) => {
         if (res.status !== "true") {
            throw new Error(res.message || "Could not apply this setting to every keyword");
         }
         return res;
      });
};

/* Measured against DataBlue on 3 Sep 2026: `advanced: true` is accepted and
   echoed back in search_parameters, and no ai_overview block came back on any
   of three query shapes. Advanced is billed at the higher rate regardless, so
   this states the position rather than selling the feature. */
export const AdvancedStatusNote = () => (
   <div className="depthNote">
      <span className="depthNoteLead">Advanced adds AI Overview.</span> It records whether
      Google answered the query with an AI Overview and which sites it cited, so you can see
      where you are quoted and where a competitor is quoted instead. Lite never asks for it,
      and a keyword measured on Lite reports AI Overview as not measured rather than absent.
   </div>
);

export const AdvancedCostNote = () => (
   <div className="depthNote">
      <span className="depthNoteLead">Advanced costs more.</span> Each keyword check is billed
      at a higher rate on your own DataBlue key, on every scheduled run. This multiplies with
      your pages-per-keyword setting.
   </div>
);

export const ADVANCED_CONFIRM_BODY =
   "Every keyword in this project will be checked at the higher Advanced rate from the next " +
   "run, including scheduled runs. Google's AI Overview is not currently coming back from " +
   "DataBlue, so this may cost more and change nothing. You can switch back to Lite at any time.";

/* The control: two radios, no fetching, no saving. `value` is a boolean --
   true is Advanced. Scope-agnostic, so a per-keyword override can reuse it. */
export function SerpDepthChoice({ value, onChange, disabled, name = "serpdepth", note }) {
   return (
      <>
         <div className="depthChoice" role="radiogroup" aria-label="SERP extraction depth">
            {OPTIONS.map((opt) => (
               <label
                  className={"depthOption" + (value === opt.value ? " isOn" : "")}
                  key={opt.name}
               >
                  <input
                     type="radio"
                     name={name}
                     value={opt.name.toLowerCase()}
                     checked={value === opt.value}
                     disabled={disabled}
                     onChange={() => onChange(opt.value)}
                  />
                  <span className="depthOptionMark" aria-hidden="true" />
                  <span className="depthOptionBody">
                     <span className="depthOptionName">
                        {opt.name}
                        {opt.tag ? <span className="depthOptionTag">{opt.tag}</span> : null}
                     </span>
                     <span className="depthOptionDesc">{opt.desc}</span>
                  </span>
               </label>
            ))}
         </div>

         {/* Shown whether or not Advanced is selected: the cost is only worth
             weighing against what it currently returns. */}
         <AdvancedStatusNote />
         {value === DEPTH_ADVANCED ? <AdvancedCostNote /> : null}
         {note ? <div className="depthScope">{note}</div> : null}
      </>
   );
}

/* Reads the project's depth on mount and writes on change. Lite -> Advanced
   asks first; Advanced -> Lite does not. */
export default function SerpDepthPanel({ grpid, canManage = true, readOnlyReason = "" }) {
   const [loading, setLoading] = useState(true);
   const [readError, setReadError] = useState("");
   // null until the first successful read -- nothing renders a selection before
   // then, so an unread project never shows Lite pre-selected.
   const [saved, setSaved] = useState(null);
   const [value, setValue] = useState(null);
   const [saving, setSaving] = useState(false);
   const [confirmOpen, setConfirmOpen] = useState(false);
   // How many keywords in this project carry their own value. null until read;
   // a count drawn before the read lands would claim "0 overrides" without
   // having looked.
   const [overrides, setOverrides] = useState(null);
   const [applyOpen, setApplyOpen] = useState(false);
   const [applying, setApplying] = useState(false);

   useEffect(() => {
      const controller = new AbortController();

      if (readOnlyReason) {
         setLoading(false);
         return () => controller.abort();
      }

      if (!(Number.isInteger(grpid) && grpid > 0)) {
         setReadError("No project selected, so there is no extraction depth to show.");
         setLoading(false);
         return () => controller.abort();
      }

      readOverrideCounts(grpid, controller.signal)
         .then(setOverrides)
         .catch(() => {
            // Non-fatal: the depth control still works. Nothing is rendered
            // for a count that could not be read.
         });

      readSerpDepth(grpid, controller.signal)
         .then((adv) => {
            setSaved(adv);
            setValue(adv);
            setLoading(false);
         })
         .catch((error) => {
            if (axios.isCancel(error)) {
               return;
            }
            setReadError(
               "Could not read this project's extraction depth. Reload the page to try again."
            );
            setLoading(false);
         });

      return () => controller.abort();
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [grpid, readOnlyReason]);

   const persist = (next) => {
      setSaving(true);
      setValue(next);

      writeSerpDepth(grpid, next)
         .then((adv) => {
            setSaved(adv);
            setValue(adv);
            setSaving(false);
            toast.success(
               adv
                  ? "This project now runs at Advanced depth"
                  : "This project now runs at Lite depth"
            );
         })
         .catch((error) => {
            setSaving(false);
            // The saved value is the only one known to be true.
            setValue(saved);
            toast.error(
               (error && error.message) || "Could not save extraction depth. Try again."
            );
         });
   };

   const applyToAll = () => {
      setApplying(true);

      clearOverrides(grpid, "all")
         .then((res) => {
            setOverrides(res);
            setApplying(false);
            toast.success("Every keyword in this project now follows these settings");
         })
         .catch((error) => {
            setApplying(false);
            toast.error(
               (error && error.message) || "Could not apply this setting to every keyword."
            );
         });
   };

   const handleChange = (next) => {
      if (next === value) {
         return;
      }
      if (next === DEPTH_ADVANCED) {
         setConfirmOpen(true);
         return;
      }
      persist(next);
   };

   const heading = (
      <>
         <TextLg class="fB lineHAuto m-b5">SERP extraction depth</TextLg>
         <Para class="secondaryClr m-b15">
            How much of each Google results page is collected for every keyword in this project.
         </Para>
      </>
   );

   if (readOnlyReason) {
      return (
         <>
            {heading}
            <Para class="secondaryClr m-b0">{readOnlyReason}</Para>
         </>
      );
   }

   if (loading) {
      return (
         <>
            {heading}
            <Tsk width={"100%"} height={72} className="m-b10" />
            <Tsk width={"100%"} height={72} className="" />
         </>
      );
   }

   if (readError) {
      // No radios: a control drawn against a value we failed to read would show
      // a selection nobody chose.
      return (
         <>
            {heading}
            <Para class="secondaryClr m-b0">{readError}</Para>
         </>
      );
   }

   return (
      <>
         {heading}

         <SerpDepthChoice
            value={value}
            onChange={handleChange}
            disabled={saving || !canManage}
            name="serpdepth-settings"
            note={
               <>
                  The default for every keyword in this project, on manual refreshes and
                  scheduled runs alike. {PRECEDENCE_NOTE} Pages per keyword is set once for the
                  whole account, above, and a keyword can override that too.
               </>
            }
         />

         {overrides && overrides.total > 0 ? (
            <div className="depthOverrides">
               {overrides.pages + overrides.advanced === 0 ? (
                  <SmallText class="secondaryClr m-b0">
                     No keyword in this project overrides these settings, so all{" "}
                     {overrides.total} follow the values above.
                  </SmallText>
               ) : (
                  <>
                     <SmallText class="m-b0">
                        {overrides.advanced > 0
                           ? overrides.advanced + " of " + overrides.total + " keywords set their own extraction depth"
                           : ""}
                        {overrides.advanced > 0 && overrides.pages > 0 ? ", and " : ""}
                        {overrides.pages > 0
                           ? overrides.pages + " of " + overrides.total + " set their own pages per check"
                           : ""}
                        . Those keywords ignore the values above until you clear them.
                     </SmallText>
                     {canManage ? (
                        <button
                           type="button"
                           className="depthApply"
                           disabled={applying}
                           onClick={() => setApplyOpen(true)}
                        >
                           {applying ? "Applying…" : "Apply to all keywords in this project"}
                        </button>
                     ) : null}
                  </>
               )}
            </div>
         ) : null}

         {!canManage ? <SmallText class="secondaryClr m-t10">Read-only access.</SmallText> : null}

         {/* "light": ConfirmDialog's confirm button is the primary black pill,
             and the default dark ground renders it black on near-black. */}
         <ModalBox className="light" title="" open={confirmOpen} onClose={() => setConfirmOpen(false)}>
            <ConfirmDialog
               title="Switch this project to Advanced?"
               cancelTitle="Cancel"
               confirmTitle="Switch to Advanced"
               modalCancel={() => setConfirmOpen(false)}
               modalConfirm={() => {
                  setConfirmOpen(false);
                  persist(DEPTH_ADVANCED);
               }}
               content={ADVANCED_CONFIRM_BODY}
            />
         </ModalBox>

         <ModalBox className="light" title="" open={applyOpen} onClose={() => setApplyOpen(false)}>
            <ConfirmDialog
               title="Apply these settings to every keyword?"
               cancelTitle="Cancel"
               confirmTitle="Apply to all keywords"
               modalCancel={() => setApplyOpen(false)}
               modalConfirm={() => {
                  setApplyOpen(false);
                  applyToAll();
               }}
               content={
                  "Every keyword that sets its own extraction depth or pages per check goes back " +
                  "to following this project and your account. This changes what future checks " +
                  "cost. It cannot be undone in one step -- the individual values are not kept."
               }
            />
         </ModalBox>
      </>
   );
}
