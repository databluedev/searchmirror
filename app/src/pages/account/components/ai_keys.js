import React, { useState, useEffect } from "react";
import "../style.scss";

import {
   TextLg,
   SmallText,
   Para,
} from "../../commonComponents/parts";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import Cookies from "universal-cookie";
import axios from "axios";
import { toast } from "react-toastify";
import { Logout } from "../../common_fun";
import { clearCapabilities } from "../../commonComponents/capability_notice";

// Order matters: this is the order they appear on screen. All four are
// queried by Geo Citations, each on this account's own key.
const PROVIDERS = [
   {
      slug: "chatgpt",
      label: "ChatGPT",
      vendor: "OpenAI",
      url: "https://platform.openai.com/api-keys",
      powers: "Geo Citations, for what ChatGPT says about your domain.",
   },
   {
      slug: "claude",
      label: "Claude",
      vendor: "Anthropic",
      url: "https://console.anthropic.com/settings/keys",
      powers: "Geo Citations, for what Claude says about your domain.",
   },
   {
      slug: "perplexity",
      label: "Perplexity",
      vendor: "Perplexity",
      url: "https://www.perplexity.ai/settings/api",
      powers: "Geo Citations, for what Perplexity says about your domain.",
   },
   {
      slug: "gemini",
      label: "Gemini",
      vendor: "Google",
      url: "https://aistudio.google.com/app/apikey",
      powers: "Geo Citations, for what Gemini says about your domain.",
   },
];

const GENERIC_ERROR = "Could not reach SearchMirror. Please try again.";

// Sentinel select value that reveals the free-text field. Real model ids never
// look like this, so it can never collide with a provider's own option.
const CUSTOM_OPTION = "__custom__";

function AiKeysModule() {
   const [loading, setLoading] = useState(true);
   const [savingSlug, setSavingSlug] = useState("");
   const [savingModelSlug, setSavingModelSlug] = useState("");
   const [state, setState] = useState({});
   const [drafts, setDrafts] = useState({});
   const [customModel, setCustomModel] = useState({});
   const [fallback, setFallback] = useState(true);

   const authHeaders = () => {
      const cookies = new Cookies();
      return { Authorization: "Token " + cookies.get("session_token") };
   };

   // A 401 from Django is an HTML page, not JSON, so never assume a body.
   const readError = (error) => {
      if (error && error.response && error.response.status === 401) return "session";
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

   const handleFailure = (error) => {
      if (axios.isCancel(error)) return;
      const msg = readError(error);
      if (msg === "session") {
         toast.warning("Session timeout! Log in again");
         Logout();
         return;
      }
      toast.error(msg);
   };

   const fetchKeys = (signal) => {
      axios
         .get(global.apiurl + "/api/account/ai-keys/", { headers: authHeaders(), signal })
         .then((r) => r.data)
         .then((res) => {
            if (res.status === "true") {
               setState(res.providers || {});
               setFallback(res.instance_fallback === "true");
            } else {
               toast.error(res.message);
            }
            setLoading(false);
         })
         .catch((error) => {
            handleFailure(error);
            setLoading(false);
         });
   };

   useEffect(() => {
      const controller = new AbortController();
      fetchKeys(controller.signal);
      return () => controller.abort();
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, []);

   const saveKey = (slug) => {
      const raw = (drafts[slug] || "").trim();
      if (!raw) {
         toast.error("Paste a key first");
         return;
      }
      setSavingSlug(slug);
      axios
         .post(
            global.apiurl + "/api/account/ai-keys/",
            { provider: slug, api_key: raw },
            { headers: authHeaders() }
         )
         .then((r) => r.data)
         .then((res) => {
            if (res.status === "true") {
               setState((p) => ({
                  ...p,
                  [slug]: { ...(p[slug] || {}), has_key: "true", key: res.key },
               }));
               setDrafts((p) => ({ ...p, [slug]: "" }));
               // A new key can unlock Geo Citations; drop the cached capability
               // map so the "needs a key" notice and the Run button refresh
               // without a full page reload.
               clearCapabilities();
               toast.success(res.message);
            } else {
               toast.error(res.message);
            }
            setSavingSlug("");
         })
         .catch((error) => {
            handleFailure(error);
            setSavingSlug("");
         });
   };

   const removeKey = (slug) => {
      setSavingSlug(slug);
      axios
         .delete(global.apiurl + "/api/account/ai-keys/", {
            headers: authHeaders(),
            data: { provider: slug },
         })
         .then((r) => r.data)
         .then((res) => {
            if (res.status === "true") {
               setState((p) => ({ ...p, [slug]: { has_key: "false", key: "" } }));
               clearCapabilities();
               toast.success(res.message);
            } else {
               toast.error(res.message);
            }
            setSavingSlug("");
         })
         .catch((error) => {
            handleFailure(error);
            setSavingSlug("");
         });
   };

   // Change only the model for a provider -- POST { provider, model } with no
   // api_key, so the stored key is untouched. An empty string clears the
   // override and the provider falls back to the instance default.
   const saveModel = (slug, model) => {
      setSavingModelSlug(slug);
      axios
         .post(
            global.apiurl + "/api/account/ai-keys/",
            { provider: slug, model: model },
            { headers: authHeaders() }
         )
         .then((r) => r.data)
         .then((res) => {
            if (res.status === "true") {
               setState((p) => ({
                  ...p,
                  [slug]: { ...(p[slug] || {}), model: model },
               }));
               toast.success(res.message || "Model updated");
            } else {
               toast.error(res.message);
            }
            setSavingModelSlug("");
         })
         .catch((error) => {
            handleFailure(error);
            setSavingModelSlug("");
         });
   };

   const onModelSelect = (slug, value) => {
      if (value === CUSTOM_OPTION) {
         // Reveal the free-text field; nothing is saved until they confirm.
         setCustomModel((p) => ({ ...p, [slug]: state[slug] ? state[slug].model || "" : "" }));
         return;
      }
      setCustomModel((p) => {
         const next = { ...p };
         delete next[slug];
         return next;
      });
      saveModel(slug, value);
   };

   if (loading) {
      return <Para class="secondaryClr">Loading your AI provider keys</Para>;
   }

   return (
      <div className="aiKeys">
         <TextLg class="fB lineHAuto m-b5">AI provider keys</TextLg>
         <Para class="secondaryClr m-b20">
            Geo Citations asks each AI model what it says about your domain. The model
            provider bills those calls, so SearchMirror runs them on your key, never a shared
            one.
         </Para>

         {!fallback ? (
            <Para class="revokeWarning m-b20">
               This instance has no shared fallback key. A provider with no key here is
               simply not queried.
            </Para>
         ) : null}

         <div className="aiKeyGrid">
            {PROVIDERS.map((p) => {
               const st = state[p.slug] || { has_key: "false", key: "" };
               const connected = st.has_key === "true";
               const busy = savingSlug === p.slug;
               const modelBusy = savingModelSlug === p.slug;
               const options = Array.isArray(st.model_options) ? st.model_options : [];
               const customOpen = Object.prototype.hasOwnProperty.call(customModel, p.slug);
               const currentModel = st.model || "";
               // A saved custom model that is not one of the suggestions still
               // needs an option to render against, or the select would show blank.
               const showsExtra =
                  !customOpen && currentModel && options.indexOf(currentModel) === -1;
               const selectValue = customOpen ? CUSTOM_OPTION : currentModel;

               return (
                  <Card className="aiKeyCard p-4" key={p.slug}>
                        <div className="flex items-center justify-between gap-3 mb-2">
                           <div className="text-[15px] font-semibold text-ink">{p.label}</div>
                           <Badge variant={connected ? "up" : "default"}>
                              {connected ? "Connected" : "Not connected"}
                           </Badge>
                        </div>

                        <SmallText class="secondaryClr m-b10">{p.powers}</SmallText>

                        {connected ? (
                           <>
                              <Label className="block mb-1">Key</Label>
                              <div className="mb-2.5 text-[13px] font-semibold text-ink">{st.key}</div>

                              <Label htmlFor={p.slug + "-model"} className="block mb-1">Model</Label>
                              <select
                                 id={p.slug + "-model"}
                                 value={selectValue}
                                 disabled={modelBusy}
                                 onChange={(e) => onModelSelect(p.slug, e.target.value)}
                                 className={`h-[38px] w-full rounded-sm border-[1px] border-solid border-line bg-surface px-2.5 text-[13px] text-ink ${modelBusy ? "cursor-default" : "cursor-pointer"}`}
                              >
                                 <option value="">Default (instance)</option>
                                 {options.map((m) => (
                                    <option key={m} value={m}>
                                       {m}
                                    </option>
                                 ))}
                                 {showsExtra ? (
                                    <option value={currentModel}>{currentModel}</option>
                                 ) : null}
                                 <option value={CUSTOM_OPTION}>Custom…</option>
                              </select>
                              {modelBusy ? (
                                 <SmallText class="secondaryClr m-t5 m-b0">Saving model…</SmallText>
                              ) : null}

                              {customOpen ? (
                                 <div className="mt-2.5">
                                    <Label htmlFor={p.slug + "-custom"} className="block mb-1">Custom model id</Label>
                                    <Input
                                       id={p.slug + "-custom"}
                                       value={customModel[p.slug] || ""}
                                       placeholder="e.g. gpt-4o-mini"
                                       onChange={(e) =>
                                          setCustomModel((prev) => ({
                                             ...prev,
                                             [p.slug]: e.target.value,
                                          }))
                                       }
                                    />
                                    <div className="flex items-center gap-3 mt-2">
                                       <Button
                                          variant="primary"
                                          size="sm"
                                          disabled={modelBusy}
                                          onClick={() =>
                                             saveModel(
                                                p.slug,
                                                (customModel[p.slug] || "").trim()
                                             )
                                          }
                                       >
                                          {modelBusy ? "Saving" : "Set model"}
                                       </Button>
                                       <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() =>
                                             setCustomModel((prev) => {
                                                const next = { ...prev };
                                                delete next[p.slug];
                                                return next;
                                             })
                                          }
                                       >
                                          Cancel
                                       </Button>
                                    </div>
                                 </div>
                              ) : null}

                              <div className="mt-2.5">
                                 <Button
                                    variant="danger"
                                    size="sm"
                                    disabled={busy}
                                    onClick={() => removeKey(p.slug)}
                                 >
                                    {busy ? "Removing" : "Remove key"}
                                 </Button>
                              </div>
                           </>
                        ) : (
                           <>
                              <Label htmlFor={p.slug + "-key"} className="block mb-1">{p.vendor + " API key"}</Label>
                              <Input
                                 id={p.slug + "-key"}
                                 type="password"
                                 value={drafts[p.slug] || ""}
                                 onChange={(e) =>
                                    setDrafts((prev) => ({ ...prev, [p.slug]: e.target.value }))
                                 }
                              />
                              <div className="mt-2.5">
                                 <Button
                                    variant="primary"
                                    size="sm"
                                    disabled={busy}
                                    onClick={() => saveKey(p.slug)}
                                 >
                                    {busy ? "Saving" : "Save key"}
                                 </Button>
                              </div>
                              <SmallText class="secondaryClr m-t5">
                                 Get one at{" "}
                                 <a href={p.url} target="_blank" rel="noreferrer">
                                    {p.url.replace("https://", "")}
                                 </a>
                              </SmallText>
                           </>
                        )}
                  </Card>
               );
            })}
         </div>

         <Para class="secondaryClr m-t20 m-b0">
            Keys are encrypted before they are stored and only ever shown back to you
            masked. SearchMirror sends them nowhere except the provider they belong to.
         </Para>
      </div>
   );
}

export default AiKeysModule;
