import React, { useState, useEffect } from "react";
import Cookies from "universal-cookie";
import axios from "axios";
import { toast } from "react-toastify";

import { SmallText } from "../../commonComponents/parts";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/**
 * "Suggest prompts": asks the backend to draft Geo Citations prompts (optionally
 * scoped to a topic), then lets the user add any of them through the SAME
 * create-prompt endpoint the onboarding uses (/llmtracker/add). It never invents
 * its own persistence -- Add just feeds one string into the existing flow.
 *
 * Generating needs an AI provider key, so a `status:"false"` reply (the "No AI
 * provider key" case) is surfaced as a toast rather than an empty list.
 */
function LLMSuggestPrompts({ refetchLLMPrompts }) {
   const [open, setOpen] = useState(false);
   const [topic, setTopic] = useState("");
   const [loading, setLoading] = useState(false);
   const [suggestions, setSuggestions] = useState([]);
   const [addingIdx, setAddingIdx] = useState(-1);

   const auth = () => {
      const cookies = new Cookies();
      return {
         userid: cookies.get("session_userid"),
         groupid: cookies.get("activegrp"),
         token: cookies.get("session_token"),
      };
   };

   const generate = () => {
      if (loading) return;
      const { userid, groupid, token } = auth();
      if (!userid || !token) {
         toast.error("Something went wrong");
         return;
      }
      setLoading(true);
      axios
         .post(
            global.apiurl + "/llmtracker/generate-prompts",
            { userid: userid, groupid: groupid, topic: topic.trim() },
            { headers: { Authorization: "Token " + token } }
         )
         .then((r) => r.data)
         .then((res) => {
            if (res && res.status === "false") {
               toast.error(res.message || "No AI provider key connected.");
               setSuggestions([]);
            } else {
               const list = res && res.data && Array.isArray(res.data.suggestions)
                  ? res.data.suggestions
                  : [];
               setSuggestions(list);
               if (list.length === 0) toast.info("No suggestions returned. Try a topic.");
            }
            setLoading(false);
         })
         .catch((error) => {
            const status = error && error.response && error.response.status;
            if (status === 401) toast.warning("Session timeout! Log in again");
            else toast.error("Could not reach SearchMirror. Please try again.");
            setLoading(false);
         });
   };

   const addSuggestion = (text, idx) => {
      if (addingIdx !== -1) return;
      const { userid, groupid, token } = auth();
      setAddingIdx(idx);
      axios
         .post(
            global.apiurl + "/llmtracker/add",
            { userid: userid, groupid: groupid, prompts: [text] },
            { headers: { Authorization: "Token " + token } }
         )
         .then((r) => r.data)
         .then((res) => {
            if (res.status === "true") {
               toast.success(res.message || "Prompt added");
               // Drop the added row so the list reflects what is left to add.
               setSuggestions((prev) => prev.filter((_, i) => i !== idx));
               if (refetchLLMPrompts) refetchLLMPrompts();
            } else {
               toast.error(res.message || "Something went wrong");
            }
            setAddingIdx(-1);
         })
         .catch(() => {
            toast.error("Something went wrong");
            setAddingIdx(-1);
         });
   };

   const addAll = () => {
      if (addingIdx !== -1 || !suggestions.length) return;
      const { userid, groupid, token } = auth();
      setAddingIdx(-2); // -2 = bulk in progress
      axios
         .post(
            global.apiurl + "/llmtracker/add",
            { userid: userid, groupid: groupid, prompts: suggestions },
            { headers: { Authorization: "Token " + token } }
         )
         .then((r) => r.data)
         .then((res) => {
            if (res.status === "true") {
               toast.success(`Added ${suggestions.length} prompts`);
               setSuggestions([]);
               if (refetchLLMPrompts) refetchLLMPrompts();
            } else {
               toast.error(res.message || "Something went wrong");
            }
            setAddingIdx(-1);
         })
         .catch(() => {
            toast.error("Something went wrong");
            setAddingIdx(-1);
         });
   };

   const close = () => {
      setOpen(false);
      // Fresh slate next open, but keep the topic so it need not be retyped.
      setSuggestions([]);
      setAddingIdx(-1);
   };

   // Preserve the MUI Modal's escape-to-close behaviour now that the overlay is
   // a plain element. Only listens while open.
   useEffect(() => {
      if (!open) return;
      const onKey = (e) => {
         if (e.key === "Escape") close();
      };
      window.addEventListener("keydown", onKey);
      return () => window.removeEventListener("keydown", onKey);
   }, [open]);

   return (
      <>
         {/* Secondary: opening the panel costs nothing, and only "Run
             analysis" should read as the primary action on this header. */}
         <Button variant="secondary" onClick={() => setOpen(true)}>
            Suggest prompts
         </Button>

         {open ? (
            <div
               className="fixed inset-0 z-[1300] flex items-center justify-center bg-black/50 p-4"
               onClick={close}
            >
               {/* Stop propagation so clicks inside the panel don't close it. */}
               <Card
                  className="w-[min(560px,92vw)] max-h-[88vh] overflow-y-auto p-6 shadow-lg"
                  onClick={(e) => e.stopPropagation()}
               >
                  <div className="d-flex align-items-center justify-content-between m-b10">
                     <span className="text-[18px] font-semibold text-ink">
                        Suggest prompts
                     </span>
                     <Button variant="ghost" size="icon" onClick={close} aria-label="Close">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 16 16">
                           <path
                              d="M13.4,12l6.3-6.3a.99.99,0,0,0-1.4-1.4L12,10.6,5.7,4.3A.99.99,0,0,0,4.3,5.7L10.6,12,4.3,18.3A.908.908,0,0,0,4,19a.945.945,0,0,0,1,1,.908.908,0,0,0,.7-.3L12,13.4l6.3,6.3a.967.967,0,0,0,1.4,0,.967.967,0,0,0,0-1.4Z"
                              transform="translate(-4 -4)"
                              fill="currentColor"
                           />
                        </svg>
                     </Button>
                  </div>

                  <SmallText class="secondaryClr m-b10">
                     Draft Geo Citations prompts with AI. Add a topic to focus them, or leave it
                     blank. Uses your connected provider key.
                  </SmallText>

                  <div className="d-flex align-items-end gap-3">
                     <div className="flex-1">
                        <Label htmlFor="suggest-topic" className="block mb-1">Topic (optional)</Label>
                        <Input
                           id="suggest-topic"
                           value={topic}
                           placeholder="e.g. project management tools"
                           onChange={(e) => setTopic(e.target.value)}
                        />
                     </div>
                     <div className="flex-none">
                        <Button variant="primary" disabled={loading} onClick={generate}>
                           {loading ? "Generating" : "Generate"}
                        </Button>
                     </div>
                  </div>

                  {suggestions.length > 0 ? (
                     <>
                        <div className="d-flex align-items-center justify-content-between m-t15 m-b5">
                           <SmallText class="fieldLabel m-b0">
                              {suggestions.length} suggestion{suggestions.length === 1 ? "" : "s"} — add the ones you want
                           </SmallText>
                           <Button
                              variant="secondary"
                              size="sm"
                              disabled={addingIdx !== -1}
                              onClick={addAll}
                           >
                              {addingIdx === -2 ? "Adding…" : "Add all"}
                           </Button>
                        </div>
                        <div className="llmSuggestList">
                           {suggestions.map((s, i) => (
                              <div className="llmSuggestRow" key={i}>
                                 <span style={{ overflowWrap: "anywhere" }}>{s}</span>
                                 <Button
                                    variant="ghost"
                                    size="sm"
                                    className="flex-none text-accent"
                                    disabled={addingIdx !== -1}
                                    onClick={() => addSuggestion(s, i)}
                                 >
                                    {addingIdx === i ? "Adding…" : "Add"}
                                 </Button>
                              </div>
                           ))}
                        </div>
                     </>
                  ) : null}
               </Card>
            </div>
         ) : null}
      </>
   );
}

export default LLMSuggestPrompts;
