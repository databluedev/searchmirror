import React, { useState, useEffect } from "react";
import "../style.scss";

import {
   AppButton,
   TextLg,
   Text,
   SmallText,
   Para,
   ParaLg,
   NormalInput,
   Tsk,
} from "../../commonComponents/parts";

import { Grid, Chip, Select, MenuItem, InputLabel } from "@mui/material";
import { SelectDownArrow } from "../../commonComponents/icons";

import Cookies from "universal-cookie";
import axios from "axios";
import { toast } from "react-toastify";
import { Logout } from "../../common_fun";
import { revealFormError } from "../../commonComponents/form_feedback";

const PROVIDER = "datablue";
const PROVIDER_LABEL = "DataBlue";
const PROVIDER_URL = "https://datablue.dev";
const RESULTS_PER_PAGE = 10;

const DEPTH_OPTIONS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// THE API ANSWERS 200 WITH status:"false" FOR A PROVIDER REJECTION AND 4xx WITH
// THE SAME ENVELOPE FOR A BAD REQUEST, SO BOTH BRANCHES READ res.message.
const GENERIC_ERROR = "Could not reach SearchMirror. Please try again.";

// Thousands separators: these run to six figures and are unreadable without.
const num = (v) => (typeof v === "number" ? v.toLocaleString() : null);

function SerpKeyModule({ children, ...props }) {
   // A blocked submit scrolls the offending field into view and focuses it, so
   // the failure cannot happen off-screen.
   const keyInputRef = React.useRef(null);

   const [loading, setLoading] = useState(true);
   const [saving, setSaving] = useState(false);
   const [depthSaving, setDepthSaving] = useState(false);

   const [hasKey, setHasKey] = useState(false);
   const [maskedKey, setMaskedKey] = useState("");
   // Read live from the provider's usage endpoint, which it documents as not
   // charged. Null whenever that read did not come back -- an outage there
   // must not take this page down, so it renders as "unavailable".
   const [balance, setBalance] = useState(null);
   const [provider, setProvider] = useState(PROVIDER);
   const [savedDepth, setSavedDepth] = useState(1);

   // FORM
   const [editing, setEditing] = useState(false);
   const [removing, setRemoving] = useState(false);
   const [confirmRemove, setConfirmRemove] = useState(false);
   const [keyInput, setKeyInput] = useState("");
   const [keyError, setKeyError] = useState("");
   const [depth, setDepth] = useState(1);

   useEffect(() => {
      // Without this the request outlives the route change and both its
      // handlers touch state -- and toast/Logout -- after the tab is gone.
      const controller = new AbortController();
      fetchKey(controller.signal);
      return () => controller.abort();
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, []);

   const authHeaders = () => {
      const cookies = new Cookies();
      return { Authorization: "Token " + cookies.get("session_token") };
   };

   // TURNS ANY AXIOS FAILURE INTO THE MESSAGE THE USER SHOULD SEE. A 401 FROM
   // DJANGO IS AN HTML PAGE, NOT JSON, SO NEVER ASSUME A BODY IS THERE.
   const readError = (error) => {
      if (error && error.response && error.response.status === 401) {
         return "session";
      }
      if (
         error &&
         error.response &&
         error.response.data &&
         typeof error.response.data === "object" &&
         error.response.data.message
      ) {
         return error.response.data.message;
      }
      return GENERIC_ERROR;
   };

   const applyKeyState = (res) => {
      setBalance(res.balance || null);
      setProvider(res.serp_provider || PROVIDER);
      setMaskedKey(res.serp_key || "");
      setHasKey(res.has_key === "true");
      const nextDepth = parseInt(res.serp_depth, 10);
      const safeDepth = nextDepth >= 1 && nextDepth <= 10 ? nextDepth : 1;
      setSavedDepth(safeDepth);
      setDepth(safeDepth);
   };

   const fetchKey = (signal) => {
      axios
         .get(global.apiurl + "/api/account/serp-key/", { headers: authHeaders(), signal })
         .then((response) => {
            return response.data;
         })
         .then((res) => {
            if (res.status !== "true") {
               // e.g. the stored token can no longer be decrypted.
               toast.error(res.message);
               setHasKey(false);
               setEditing(true);
            } else {
               applyKeyState(res);
               setEditing(res.has_key !== "true");
            }
            setLoading(false);
         })
         .catch((error) => {
            // The unmount cleanup aborted this; there is no failure to report.
            if (axios.isCancel(error)) {
               return;
            }
            const msg = readError(error);
            if (msg === "session") {
               toast.warning("Session timeout! Log in again");
               Logout();
               return;
            }
            toast.error(msg);
            setLoading(false);
            setEditing(true);
         });
   };

   const submitKey = (e) => {
      e.preventDefault();

      const rawKey = keyInput.trim();
      if (!rawKey) {
         const message = "Please paste your " + PROVIDER_LABEL + " API key";
         setKeyError(message);
         revealFormError(message, keyInputRef);
         return false;
      }

      setKeyError("");
      setSaving(true);

      const data = {
         serp_key: rawKey,
         serp_provider: PROVIDER,
         serp_depth: depth,
      };

      axios
         .post(global.apiurl + "/api/account/serp-key/", data, { headers: authHeaders() })
         .then((response) => {
            return response.data;
         })
         .then((res) => {
            setSaving(false);
            if (res.status !== "true") {
               // PROVIDER REJECTION ARRIVES AS HTTP 200 - SHOW IT ON THE FIELD.
               setKeyError(res.message);
               toast.error(res.message);
               return;
            }
            applyKeyState(res);
            // THE RAW KEY LEAVES MEMORY THE MOMENT IT IS ACCEPTED.
            setKeyInput("");
            setEditing(false);
            toast.success("Key validated and saved");
         })
         .catch((error) => {
            setSaving(false);
            const msg = readError(error);
            if (msg === "session") {
               toast.warning("Session timeout! Log in again");
               Logout();
               return;
            }
            setKeyError(msg);
            toast.error(msg);
         });
   };

   // DELETE CLEARS serp_key ONLY - THE SERVER DELIBERATELY KEEPS serp_provider AND
   // serp_depth, SO applyKeyState CARRIES THE USER'S DEPTH SETTING THROUGH A REMOVAL.
   const removeKey = () => {
      setRemoving(true);

      axios
         .delete(global.apiurl + "/api/account/serp-key/", { headers: authHeaders() })
         .then((response) => {
            return response.data;
         })
         .then((res) => {
            setRemoving(false);
            if (res.status !== "true") {
               toast.error(res.message);
               return;
            }
            applyKeyState(res);
            setConfirmRemove(false);
            setKeyInput("");
            setKeyError("");
            setEditing(true);
            toast.success(res.message);
         })
         .catch((error) => {
            setRemoving(false);
            const msg = readError(error);
            if (msg === "session") {
               toast.warning("Session timeout! Log in again");
               Logout();
               return;
            }
            toast.error(msg);
         });
   };

   // PATCH CHANGES DEPTH ALONE. POST WOULD DEMAND THE RAW KEY BACK, WHICH THE
   // USER NO LONGER HAS - THE PAGE SHOWS ONLY A MASK - SO DEPTH USED TO BE
   // EDITABLE ONLY AT KEY-ENTRY TIME. IT DECIDES WHETHER A RANK BEYOND PAGE 1
   // IS VISIBLE AT ALL, SO IT HAS TO BE CHANGEABLE AFTERWARDS.
   const saveDepth = () => {
      setDepthSaving(true);

      axios
         .patch(
            global.apiurl + "/api/account/serp-key/",
            { serp_depth: depth },
            { headers: authHeaders() }
         )
         .then((response) => {
            return response.data;
         })
         .then((res) => {
            setDepthSaving(false);
            if (res.status !== "true") {
               toast.error(res.message);
               setDepth(savedDepth);
               return;
            }
            applyKeyState(res);
            toast.success(res.message);
         })
         .catch((error) => {
            setDepthSaving(false);
            setDepth(savedDepth);
            const msg = readError(error);
            if (msg === "session") {
               toast.warning("Session timeout! Log in again");
               Logout();
               return;
            }
            toast.error(msg);
         });
   };

   const startReplace = () => {
      setKeyInput("");
      setKeyError("");
      setDepth(savedDepth);
      setConfirmRemove(false);
      setEditing(true);
   };

   const cancelReplace = () => {
      setKeyInput("");
      setKeyError("");
      setDepth(savedDepth);
      setEditing(false);
   };

   const depthLabel = (value) => {
      return value === 1
         ? "1 page (about " + RESULTS_PER_PAGE + " results)"
         : value + " pages (about " + value * RESULTS_PER_PAGE + " results)";
   };

   const depthSelect = (
      <>
         <InputLabel shrink className="mb-1">
            Pages per keyword <span className="spanClass">*</span>
         </InputLabel>
         <Select
            className="customSelect"
            value={depth}
            disabled={saving}
            IconComponent={SelectDownArrow}
            onChange={(e) => setDepth(e.target.value)}
            inputProps={{ "aria-label": "Pages per keyword" }}
            fullWidth
         >
            {DEPTH_OPTIONS.map((value) => (
               <MenuItem key={value} value={value}>
                  {depthLabel(value)}
               </MenuItem>
            ))}
         </Select>
         <SmallText class="secondaryClr m-t5">
            {PROVIDER_LABEL} bills every page separately. At {depth}{" "}
            {depth === 1 ? "page" : "pages"} each keyword costs {depth}
            {depth === 1 ? " credit" : " credits"} per rank check, so raising this multiplies the
            cost of every run.
         </SmallText>
      </>
   );

   const keyForm = (
      <form id="serpkeyform" autoComplete="off" onSubmit={submitKey} noValidate>
         <Grid container spacing={3}>
            <Grid item xs={12} ref={keyInputRef}>
               <NormalInput
                  label={PROVIDER_LABEL + " API key"}
                  span={" *"}
                  classname="apiKeyField"
                  type="password"
                  value={keyInput}
                  placeholder={hasKey ? "Paste your new key" : "wh_..."}
                  disabled={saving}
                  maxlength={200}
                  error={keyError.length > 0}
                  errmsg={keyError}
                  onchange={(e) => {
                     setKeyInput(e.target.value);
                     setKeyError("");
                  }}
               />
               <SmallText class="secondaryClr m-t5">
                  SearchMirror uses this key to run your rank checks against {PROVIDER_LABEL}. Find it
                  under API keys in your{" "}
                  <a className="fieldHelpLink" href={PROVIDER_URL} target="_blank" rel="noreferrer noopener">
                     {PROVIDER_LABEL} dashboard
                  </a>
                  . We encrypt it before storing it and never show it again — only the first and
                  last few characters.
               </SmallText>
            </Grid>

            <Grid item xs={12}>
               {depthSelect}
            </Grid>

            <Grid item xs={12}>
               <SmallText class="secondaryClr m-b10">
                  Saving runs one live check against {PROVIDER_LABEL} to confirm the key works. This
                  takes a couple of seconds.
               </SmallText>
               <div className="d-flex align-items-center gap-3 flex-wrap">
                  <div className="min-w-[150px]">
                     <AppButton
                        loading={saving}
                        value={hasKey ? "Save new key" : "Validate and save"}
                        noIcon="d-none"
                        class="wd-btn-add"
                        onclick={submitKey}
                        type="submit"
                     />
                  </div>
                  {hasKey ? (
                     <Para class="m-b0 quietAction cursorPointer" onclick={saving ? undefined : cancelReplace}>
                        Cancel
                     </Para>
                  ) : null}
               </div>
            </Grid>
         </Grid>
      </form>
   );

   const connectedCard = (
      <section className="projectCard apiKeyCard">
         <div className="d-flex align-items-center justify-content-between m-b15">
            <ParaLg class="fB m-b0">Connected to {PROVIDER_LABEL}</ParaLg>
            <Chip className="statusChip" label="Active" size="small" />
         </div>

         <Grid container spacing={2} className="m-b15">
            <Grid item xs={12}>
               <SmallText class="fieldLabel m-b0">Provider</SmallText>
               <Text class="fB m-b0 text-capital">
                  {provider === PROVIDER ? PROVIDER_LABEL : provider}
               </Text>
            </Grid>
            <Grid item xs={12}>
               <SmallText class="fieldLabel m-b0">API key</SmallText>
               {/* Masked, and it has to look masked: an inset slab in a
                   tabular face, so it reads as a stored secret and not as an
                   editable value. */}
               <div className="maskedKey">{maskedKey}</div>
            </Grid>
            <Grid item xs={12}>
               <SmallText class="fieldLabel m-b5">Pages per keyword</SmallText>
               <Select
                  className="customSelect"
                  value={depth}
                  disabled={depthSaving}
                  IconComponent={SelectDownArrow}
                  onChange={(e) => setDepth(e.target.value)}
                  inputProps={{ "aria-label": "Pages per keyword" }}
                  fullWidth
               >
                  {DEPTH_OPTIONS.map((value) => (
                     <MenuItem key={value} value={value}>
                        {depthLabel(value)}
                     </MenuItem>
                  ))}
               </Select>
               {/* The Save button appears only once the value actually differs,
                   so the settled state stays a plain reading surface. */}
               {depth !== savedDepth ? (
                  <div className="d-flex align-items-center gap-3 flex-wrap m-t10">
                     <div className="min-w-[150px]">
                        <AppButton
                           type="button"
                           text={depthSaving ? "Saving..." : "Save pages"}
                           disabled={depthSaving}
                           onClick={saveDepth}
                        />
                     </div>
                     <Para
                        class="m-b0 quietAction cursorPointer"
                        onclick={depthSaving ? undefined : () => setDepth(savedDepth)}
                     >
                        Cancel
                     </Para>
                  </div>
               ) : null}
               <SmallText class="secondaryClr m-t5">
                  A rank below the pages you pull is recorded as not ranking. {PROVIDER_LABEL} bills
                  every page separately, so each keyword costs {depth}
                  {depth === 1 ? " credit" : " credits"} per rank check.
               </SmallText>
            </Grid>
            <Grid item xs={12}>
               <SmallText class="fieldLabel m-b0">Credits</SmallText>
               {balance ? (
                  <>
                     <Text class="fB m-b0">
                        {balance.unlimited
                           ? "Unlimited"
                           : num(balance.total_available) !== null
                           ? num(balance.total_available) + " available"
                           : "—"}
                        {balance.plan ? " · " + balance.plan + " plan" : ""}
                     </Text>
                     <SmallText class="secondaryClr m-b0">
                        {num(balance.used) !== null ? num(balance.used) + " used this period" : ""}
                        {!balance.unlimited && num(balance.included) !== null
                           ? " of " + num(balance.included)
                           : ""}
                        {num(balance.topup_balance) ? " · " + num(balance.topup_balance) + " top-up" : ""}
                     </SmallText>
                  </>
               ) : (
                  <Text class="fB m-b0 secondaryClr">Unavailable</Text>
               )}
            </Grid>
         </Grid>

         <div className="datablueUses">
            <SmallText class="fieldLabel m-b5">What your {PROVIDER_LABEL} key powers in SearchMirror</SmallText>
            <ul className="datablueUsesList">
               <li><span className="useTag">SERP</span> Keyword rank tracking — every position check runs on {PROVIDER_LABEL}'s Google SERP API.</li>
               <li><span className="useTag">Usage</span> The credit balance above, read from {PROVIDER_LABEL}'s usage summary (not charged).</li>
            </ul>
            <SmallText class="secondaryClr m-t5">
               Geo Citations uses your AI provider keys (AI Keys tab), not {PROVIDER_LABEL}. Keyword
               research and content-gap lookups use separate instance integrations.
            </SmallText>
         </div>

         <Para class="secondaryClr">
            Your key is stored encrypted and is never shown again. Replace it to enter a new key or
            change how many pages each rank check reads — {PROVIDER_LABEL} re-validates the key on
            every save.
         </Para>

         {confirmRemove ? (
            <div className="revokeConfirm">
               <Para class="revokeWarning m-b10">
                  Removing this key stops every rank check on this account until you add another
                  one.
               </Para>
               <Para class="secondaryClr">
                  Your API key will be removed from your account. Your pages-per-keyword setting is
                  kept, so you can add a new key later without setting it up again.
               </Para>
               <div className="d-flex align-items-center gap-3 flex-wrap">
                  <div className="min-w-[150px]">
                     <AppButton
                        loading={removing}
                        value="Remove key"
                        noIcon="d-none"
                        class="deleteAccBtn m-t0"
                        onclick={removeKey}
                     />
                  </div>
                  <Para
                     class="m-b0 quietAction cursorPointer"
                     onclick={removing ? undefined : () => setConfirmRemove(false)}
                  >
                     Cancel
                  </Para>
               </div>
            </div>
         ) : (
            <div className="d-flex align-items-center gap-3 flex-wrap">
               <div className="min-w-[150px]">
                  <AppButton value="Replace key" noIcon="d-none" class="wd-btn-add" onclick={startReplace} />
               </div>
               {/* Destructive, so it is never the same blue as "Replace". */}
               <Para class="m-b0 destructiveAction cursorPointer" onclick={() => setConfirmRemove(true)}>
                  Remove key
               </Para>
            </div>
         )}
      </section>
   );

   const explainer = (
      <section className="projectCard apiKeyExplainer">
         <ParaLg class="fB m-b15">Why SearchMirror needs your key</ParaLg>
         <Para>
            SearchMirror runs rank checks using your own {PROVIDER_LABEL} account. Your key stays
            encrypted and is only used for your own projects.
         </Para>
         <Para>
            Every rank check is billed to your {PROVIDER_LABEL} account, so you see the usage and
            the invoice directly from them — nothing is marked up here.
         </Para>
         <Para class="m-b0">
            Don't have a key yet?{" "}
            <a
               className="primaryClr"
               href={PROVIDER_URL}
               target="_blank"
               rel="noreferrer noopener"
            >
               Create one at datablue.dev
            </a>
            .
         </Para>
      </section>
   );

   return (
      <div className="m-b70 m-t25">
         <Grid container spacing={4}>
            <Grid item xs={12} md={7} lg={5}>
               {loading ? (
                  <>
                     <Tsk width={220} height={26} className="m-b15" />
                     <Tsk width={"100%"} height={48} className="m-b15" />
                     <Tsk width={"100%"} height={48} className="m-b15" />
                     <Tsk width={150} height={40} className="" />
                  </>
               ) : editing ? (
                  <>
                     <TextLg class="lineHAuto m-b5">
                        {hasKey ? "Replace your API key" : "Connect your " + PROVIDER_LABEL + " key"}
                     </TextLg>
                     <Para class="secondaryClr m-b20">
                        {hasKey
                           ? "Enter a new key to replace the one on file. The current key keeps working until the new one is validated."
                           : "Paste the key from your " +
                             PROVIDER_LABEL +
                             " dashboard. We check it against " +
                             PROVIDER_LABEL +
                             " before saving, so you know straight away that it works."}
                     </Para>
                     {keyForm}
                  </>
               ) : (
                  connectedCard
               )}
            </Grid>

            <Grid item xs={12} md={5} lg={4}>
               {explainer}
            </Grid>
         </Grid>
      </div>
   );
}

export default SerpKeyModule;
