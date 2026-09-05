import React, { useState, useEffect } from "react";
import { useHistory, useParams, useLocation } from "react-router-dom";
import './style.scss';
import OverallPageScore from './components/cedit_score_widget';
import { Grid } from "@mui/material";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';
import { BacklinkIcon } from "../commonComponents/icons";
import { Title, Para, AppIconButton, AppButton } from "../commonComponents/parts";
import ReactQuill from "react-quill-new";
import CapabilityNotice from "../commonComponents/capability_notice";
import PageSkeleton, { Bone } from "../commonComponents/page_skeleton";
import "react-quill-new/dist/quill.snow.css"; // Include CSS
import { parseDocument } from "htmlparser2";
import DOMPurify from "dompurify";
import { allowsTeamAction } from '../../utils/team_permissions';

function CEditor(props) {

   const cookies = new Cookies();
   const usertoken = cookies.get('session_token')
   const userid = cookies.get('session_userid')
   const grpid = cookies.get('activegrp')
   const canManageContent = allowsTeamAction(props.fullbasedata, "ContentPlanner", "Manage Content");

   const history = useHistory();
   const location = useLocation();
   let { content_id } = useParams();

   const [primaryKeyword, setPrimaryKeyword] = React.useState("");
   const [secondaryKeywords, setSecondaryKeywords] = React.useState([]);
   const [headerSuggestions, setHeaderSuggestions] = React.useState([]);
   const [contentSuggestions, setContentSuggestions] = React.useState([]);
   const [primaryKeywordUsed, setPrimaryKeywordUsed] = React.useState(false);
   const [usedSecondaryKeywords, setUsedSecondaryKeywords] = React.useState([]);
   const [usedHeaderSuggestions, setUsedHeaderSuggestions] = useState([]);
   const [usedContentSuggestions, setUsedContentSuggestions] = useState([]);
   const [stats, setStats] = useState({ words: 0, images: 0, headers: 0, paragraphs: 0 });
   const [generatingAI, setGeneratingAI] = useState(false);

   const modules = {
      toolbar: [
         [{ header: [1, 2, 3, 4, 5, 6, false] }], // Headings (H1, H2, H3)
         ["bold", "italic", "underline", "strike"], // Inline formatting
         [{ list: "ordered" }, { list: "bullet" }], // Bullet & Numbered lists
         [{ indent: "-1" }, { indent: "+1" }], // Indentation
         [{ align: [] }], // Text alignment (left, center, right, justify)
         ["link", "image"], // Link & Image upload
         [{ blockquote: true }, { code: true }], // Block options (blockquote, code block)
         ["clean"], // Remove formatting
      ],
   };

   const formats = [
      "header",
      "bold",
      "italic",
      "underline",
      "strike",
      "list",
      "indent",
      "align",
      "link",
      "image",
      "blockquote",
      "code",
   ];

   const [content, setContent] = useState("");
   const [contentScore, setContentScore] = useState(0);
   const [initLoading, setInitLoading] = useState(true)
   const [dataSaving, setDataSaving] = useState(false)

   const extractAllTags = (htmlContent) => {
      const doc = parseDocument(htmlContent);
      let extractAllTags = [];

      function getText(node) {
         if (node.type === "text") {
            return node.data;
         } else if (node.children) {
            return node.children.map(getText).join(""); // Recursively extract text from children
         }
         return "";
      }

      function traverse(node) {
         if (node.type === "tag") {
            extractAllTags.push(getText(node).trim()); // Extract text including nested tags
         }
         if (node.children) {
            node.children.forEach(traverse);
         }
      }

      traverse(doc);
      return extractAllTags;
   };


   const extractHeaders = (htmlContent) => {
      const doc = parseDocument(htmlContent);
      let extractedHeaders = [];

      function getText(node) {
         if (node.type === "text") {
            return node.data;
         } else if (node.children) {
            return node.children.map(getText).join(""); // Recursively extract text from children
         }
         return "";
      }

      function traverse(node) {
         if (node.type === "tag" && ["h1", "h2", "h3", "h4", "h5", "h6"].includes(node.name)) {
            extractedHeaders.push(getText(node).trim()); // Extract text including nested tags
         }
         if (node.children) {
            node.children.forEach(traverse);
         }
      }

      traverse(doc);
      return extractedHeaders;
   };


   const extractNonHeaders = (htmlContent) => {
      const doc = parseDocument(htmlContent);
      let extractedNonHeaders = [];

      function getText(node) {
         if (node.type === "text") {
            return node.data;
         } else if (node.children) {
            return node.children.map(getText).join(""); // Recursively extract text from children
         }
         return "";
      }

      function traverse(node) {
         if (node.type === "tag" && !["h1", "h2", "h3", "h4", "h5", "h6"].includes(node.name)) {
            extractedNonHeaders.push(getText(node).trim()); // Extract text including nested tags
         }
         if (node.children) {
            node.children.forEach(traverse);
         }
      }

      traverse(doc);
      return extractedNonHeaders;
   };

   useEffect(() => {

      if (content) {
         const sanitizedContent = DOMPurify.sanitize(content);

         let wordCount = sanitizedContent.split(/\s+/).filter(Boolean).length;
         let imageCount = (sanitizedContent.match(/<img/g) || []).length;
         let headerCount = (sanitizedContent.match(/<h[1-6]/g) || []).length;
         let paragraphCount = (sanitizedContent.match(/<p/g) || []).length;

         setStats({ words: wordCount, images: imageCount, headers: headerCount, paragraphs: paragraphCount });

         const headerText = extractHeaders(content); // Extract text
         const nonHeaderText = extractNonHeaders(content); // Extract text
         const allText = extractAllTags(content); // Extract text

         // Score over the components that actually have data. Two of the four
         // read nlp_stats, which has no writer anywhere since the background
         // worker was retired, so a document using the primary keyword and
         // every secondary keyword still capped at 50/100 and was labelled
         // "Okay !" in amber. There was no input that produced a good score.
         let earnedScore = 0
         let possibleScore = 0

         if (headerSuggestions.length > 0) {
            const activeHeaderSuggestions = headerSuggestions.filter((eachSuggestion) =>
               new RegExp(`\\b${eachSuggestion.toLowerCase()}\\b`, "gi").test(headerText)
            );
            setUsedHeaderSuggestions(activeHeaderSuggestions);
            possibleScore += 25
            earnedScore += (activeHeaderSuggestions.length / 5) * 25
         }

         if (contentSuggestions.length > 0) {
            const activeContentSuggestions = contentSuggestions.filter((eachSuggestion) =>
               new RegExp(`\\b${eachSuggestion.toLowerCase()}\\b`, "gi").test(nonHeaderText)
            );
            setUsedContentSuggestions(activeContentSuggestions);
            possibleScore += 25
            earnedScore += (activeContentSuggestions.length / 5) * 25
         }

         if (primaryKeyword) {
            const hasPrimaryKeyword = (allText, primaryKeyword) => {
               return new RegExp(`\\b${primaryKeyword.toLowerCase()}\\b`, "gi").test(allText);
            };

            possibleScore += 25
            if (hasPrimaryKeyword(allText, primaryKeyword)) {
               earnedScore += 25
            }

            setPrimaryKeywordUsed(hasPrimaryKeyword(allText, primaryKeyword))
         }

         if (secondaryKeywords.length > 0) {
            const activeSecondaryKeywords = secondaryKeywords.filter((eachSuggestion) =>
               new RegExp(`\\b${eachSuggestion.toLowerCase()}\\b`, "gi").test(allText)
            );
            setUsedSecondaryKeywords(activeSecondaryKeywords);
            possibleScore += 25
            earnedScore += (activeSecondaryKeywords.length / secondaryKeywords.length) * 25
         }


         setContentScore(possibleScore ? (earnedScore / possibleScore) * 100 : 0);
      }



      if (initLoading) {
         getContentDetails()
      }

   }, [location, history, usertoken, userid, props.projectList, content]);

   const getContentDetails = () => {

      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')

      if (!usertoken || !userid) {
         history.push("/login");
      }

      axios.post(global.apiurl + '/contentmanager/details', { 'userid': userid, 'grpid': grpid, 'content_id': content_id }, {
         headers: { 'Authorization': 'Token ' + usertoken }
      }).then(response => {
         return response.data;
      }).then(res => {
         setInitLoading(false)
         if (res.status !== "true") {
            history.push("/contentplanner")
            toast.error(res.message)
         } else {
            const nlpStats = res.data.nlp_stats || {};
            const competitors = Array.isArray(nlpStats.competitors)
               ? nlpStats.competitors
               : [];
            setPrimaryKeyword(res.data.primary_keyword)
            setSecondaryKeywords(res.data.secondary_keywords)
            setStats({
               words: nlpStats.used_words || 0,
               images: nlpStats.used_images || 0,
               headers: nlpStats.used_headings || 0,
               paragraphs: nlpStats.used_paragraphs || 0,
            });
            setHeaderSuggestions(
               [...new Set(competitors.flatMap(comp => comp.header_suggestions || []))]
            );
            setContentSuggestions([...new Set(competitors.flatMap(comp => comp.content_suggestions || []))])
            setContent(res.data.content_html_data || "")
         }
      }).catch((error) => {
         setInitLoading(false)
         toast.error(error)
      });
   }

   const handleSaveContent = () => {

      setDataSaving(true)

      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      axios.post(global.apiurl + '/contentmanager/update', {
         'userid': userid,
         'grpid': grpid,
         'content_id': content_id,
         'content_score': Math.round(contentScore),
         'content_html_data': JSON.stringify(content)
      }, {
         headers: { 'Authorization': 'Token ' + usertoken }
      }).then(response => {
         return response.data;
      }).then(res => {
         setDataSaving(false)
         if (res.status === "true") {
            toast.success(res.message)
         } else {
            toast.error(res.message)
         }
      }).catch((error) => {
         setDataSaving(false)
         toast.error("Something went wrong")
      });
   }

   /* Generation is a 30-60s provider call. It used to be awaited inside the
      request, which held a server worker for the whole of it; it is now queued
      and polled, the same shape RefreshBar uses for a rank run -- fixed
      interval, an attempt cap so the bar cannot spin forever, an abort for the
      in-flight request, and teardown on unmount. */
   const genPollRef = React.useRef(null);
   const genAttemptsRef = React.useRef(0);
   const genAbortRef = React.useRef(null);
   if (genAbortRef.current === null) {
      genAbortRef.current = new AbortController();
   }
   const GEN_POLL_MS = 3000;
   // 60 polls x 3s = 3 minutes, well past a provider call that has not hung.
   const GEN_MAX_POLLS = 60;

   useEffect(() => () => {
      clearInterval(genPollRef.current);
      genAbortRef.current.abort();
   }, []);

   const applyGeneratedContent = (raw) => {
      let htmlContent = raw;

      // Remove any potential DOCTYPE, html, head or body tags that might have been included
      htmlContent = htmlContent.replace(/<!DOCTYPE.*?>/gi, '');
      htmlContent = htmlContent.replace(/<html.*?>|<\/html>/gi, '');
      htmlContent = htmlContent.replace(/<head>.*?<\/head>/gi, '');
      htmlContent = htmlContent.replace(/<body.*?>|<\/body>/gi, '');

      // Clean the HTML to prevent XSS issues
      htmlContent = DOMPurify.sanitize(htmlContent, {
         ADD_TAGS: ['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'li', 'ol', 'strong', 'em', 'blockquote'],
         ALLOWED_TAGS: ['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'li', 'ol', 'strong', 'em', 'blockquote']
      });

      // Ensure there are line breaks after headings for better readability in the editor
      htmlContent = htmlContent.replace(/<\/(h[1-6])>(?!\s*<br>)/g, '</$1><br><br>');

      setContent(htmlContent);
   }

   const pollGeneration = () => {
      genAttemptsRef.current = 0;
      genPollRef.current = setInterval(() => {
         genAttemptsRef.current += 1;
         if (genAttemptsRef.current > GEN_MAX_POLLS) {
            clearInterval(genPollRef.current);
            setGeneratingAI(false);
            toast.info("Generation is taking longer than expected. Reopen this plan to check on it.");
            return;
         }

         axios.post(global.apiurl + '/contentmanager/generate/status',
            { 'userid': userid, 'grpid': grpid, 'content_id': content_id },
            { headers: { 'Authorization': 'Token ' + usertoken }, signal: genAbortRef.current.signal }
         ).then(response => response.data).then(res => {
            const state = res.status === "true" && res.data ? res.data.gen_status : "";
            if (state === "QUEUED" || state === "RUNNING") {
               return;
            }
            clearInterval(genPollRef.current);
            setGeneratingAI(false);
            if (state === "DONE" && res.data.content) {
               applyGeneratedContent(res.data.content);
               toast.success("AI content generated successfully!");
            } else {
               toast.error(res.data && res.data.message
                  ? res.data.message
                  : "Failed to generate AI content. Please try again.");
            }
         }).catch(error => {
            // The unmount cleanup already cleared the interval; there is
            // nobody left to show a toast to.
            if (axios.isCancel(error)) {
               return;
            }
            clearInterval(genPollRef.current);
            setGeneratingAI(false);
            toast.error("Lost contact while generating. Reopen this plan to check on it.");
         });
      }, GEN_POLL_MS);
   }

   const handleGenerateAIContent = () => {
      setGeneratingAI(true);

      axios.post(global.apiurl + '/contentmanager/generate', { 'userid': userid, 'grpid': grpid, 'content_id': content_id }, {
         headers: { 'Authorization': 'Token ' + usertoken }
      }).then(response => {
         return response.data;
      }).then(res => {
         if (res.status !== "true") {
            throw new Error(res.message || "Failed to start generation");
         }
         // The work is queued, not done. Everything from here is the poller's.
         pollGeneration();
      }).catch(error => {
         setGeneratingAI(false);
         toast.error(
            error.response?.data?.message
            || error.message
            || "Failed to generate AI content. Please try again."
         );
      });
   }

   return (
      <>
         {
            initLoading ?
               /* The editor is a fixed two-column layout -- a full-height
                  writing pane and a narrow score rail -- so the skeleton can be
                  the exact shape of it rather than an approximation. */
               (<PageSkeleton label="Loading this content plan">
                  <Grid container spacing={2}>
                     <Grid item xs={12} md={12} lg={9} xl={9}>
                        <Bone height="calc(100vh - 110px)" />
                     </Grid>
                     <Grid item xs={12} md={12} lg={3} xl={3}>
                        <Bone height="calc(100vh - 110px)" />
                     </Grid>
                  </Grid>
               </PageSkeleton>)
               :
               (<>
                  <section className="layout" style={{ "height": "110vh" }}>
                     <header>
                        <div className="d-flex justify-content-between flex-wrap gap-3">
                           <div className="d-flex flex-wrap gap-3 align-items-center">
                              <span>
                                 <AppIconButton
                                    Icon={<BacklinkIcon />}
                                    onclick={() => { window.history.back(); }}
                                 />
                              </span>
                              <div>
                                 <>
                                    <Title class="wd-title">Content Planner</Title>
                                 </>
                                 <Para class="wd-subTitle m-b0 d-flex align-items-center lh14x">Create and optimize your content with real-time NLP analysis</Para>
                              </div>
                           </div>
                        </div>
                     </header>
                     <Grid container spacing={2} >
                        <Grid item xs={12} md={12} lg={9} xl={9} className="d-flex mt-2" style={{ height: "calc(100vh - 110px)", paddingTop: "6px" }}>
                           <div style={{ width: "100%", height: "100%" }} className="editor-wrapper" > {/* Width & Height */}
                              <ReactQuill
                                 theme="snow"
                                 value={content}
                                 onChange={setContent}
                                 modules={canManageContent ? modules : { toolbar: false }}
                                 formats={formats}
                                 readOnly={!canManageContent}
                                 style={{ height: "calc(100vh - 110px)" }} // Adjust editor height
                                 className="editor-container"
                              />
                           </div>
                        </Grid>
                        <Grid
                           item
                           xs={12} md={12} lg={3} xl={3}
                           className="d-flex mt-2 flex-column"
                           style={{ height: "calc(100vh - 110px)", overflowY: "auto", overflowX: "hidden" }}
                        >
                           <Grid container spacing={2} direction="column">

                              {/* Overall Score */}
                              <Grid item className="d-flex mt-2 justify-content-center oveGreyScore pb-4">
                                 <OverallPageScore score={contentScore} />
                              </Grid>

                              {/* Content Metrics */}
                              <Grid item className="d-flex oveGreyScore w-100 mt-2 flex-column">
                                 <div>
                                    <div className="mt-2">
                                       {canManageContent ? <div className="d-flex justify-content-end align-items-center m-b4 p-b10" style={{ paddingRight: '10px' }}>
                                          <AppButton noIcon="d-none" value="Save" color="primary" type="submit" onclick={handleSaveContent} loading={dataSaving} disabled={dataSaving} />
                                       </div> : <p className="lightTxtClr m-b10 p-b10">Read-only access</p>}
                                       {canManageContent ? <div className="d-flex justify-content-end align-items-center brdBottom m-b10 p-b10" style={{ paddingRight: '10px' }}>
                                          <AppButton
                                             noIcon="d-none"
                                             value="Create with AI"
                                             color="white"
                                             type="button"
                                             class="borderBtn mnW109"
                                             onclick={handleGenerateAIContent}
                                             loading={generatingAI}
                                             disabled={generatingAI || !primaryKeyword}
                                          />
                                       </div> : null}
                                       <CapabilityNotice name="content_planner" />
                                       <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
                                          <div className="fM f-md mb-1"><span className="m-r8">Content Metrics</span></div>
                                       </div>
                                       <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
                                          <div className="d-flex align-items-center"><span>Words</span></div>
                                          <div className="fB p-2">{stats.words}</div>
                                       </div>
                                       <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10">
                                          <div className="d-flex align-items-center"><span>Headings</span></div>
                                          <div className="fB p-2">{stats.headers}</div>
                                       </div>
                                       <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10">
                                          <div className="d-flex align-items-center"><span>Paragraphs</span></div>
                                          <div className="fB p-2">{stats.paragraphs}</div>
                                       </div>
                                       <div className="d-flex justify-content-between align-items-center">
                                          <div className="d-flex align-items-center"><span>Images</span></div>
                                          <div className="fB p-2">{stats.images}</div>
                                       </div>
                                    </div>
                                 </div>
                              </Grid>

                              {/* Primary Keyword */}
                              <Grid item className="d-flex oveGreyScore w-100 mt-2 flex-column">
                                 <div className="pageoverview_addtag">
                                    <div className="tags-input keyword">
                                       <div className="fM f-md mb-1"><span className="m-r8">Primary Keyword</span></div>
                                       <ul className="mt-2">
                                          <li className={primaryKeywordUsed ? "cursorP activetag" : "cursorP"}>
                                             <span className="p-r10">{primaryKeyword}</span>
                                          </li>
                                       </ul>
                                    </div>
                                 </div>
                              </Grid>

                              {/* Secondary Keywords */}
                              {secondaryKeywords.length > 0 && (
                                 <Grid item className="d-flex oveGreyScore w-100 mt-2 flex-column">
                                    <div className="pageoverview_addtag">
                                       <div className="tags-input keyword">
                                          <div className="fM f-md mb-1">Secondary Keywords</div>
                                          <ul className="overflow-y-auto mt-2">
                                             {secondaryKeywords.map((eachKeyword, index) => (
                                                <li
                                                   className={usedSecondaryKeywords.includes(eachKeyword) ? "cursorP activetag" : "cursorP"}
                                                   key={index}
                                                >
                                                   <span className="p-r10">{eachKeyword}</span>
                                                </li>
                                             ))}
                                          </ul>
                                       </div>
                                    </div>
                                 </Grid>
                              )}

                              {/* Both NLP panels are hidden when empty. nlp_stats has had no
                                  writer since the background worker was retired, so these
                                  rendered as titled boxes containing nothing, permanently --
                                  an empty panel for something that was never measured. */}
                              {headerSuggestions.length > 0 ? (
                              <Grid item className="d-flex oveGreyScore w-100 mt-2 flex-column">
                                 <div className="pageoverview_addtag">
                                    <div className="tags-input keyword">
                                       <div className="fM f-md mb-1">NLP Header Suggestions</div>
                                       <ul className="overflow-y-auto mt-2">
                                          {headerSuggestions.map((eachKeyword, index) => (
                                             <li
                                                className={usedHeaderSuggestions.includes(eachKeyword) ? "cursorP activetag" : "cursorP"}
                                                key={index}
                                             >
                                                <span className="p-r10">{eachKeyword}</span>
                                             </li>
                                          ))}
                                       </ul>
                                    </div>
                                 </div>
                              </Grid>
                              ) : null}

                              {contentSuggestions.length > 0 ? (
                              <Grid item className="d-flex oveGreyScore w-100 mt-2 flex-column">
                                 <div className="pageoverview_addtag">
                                    <div className="tags-input keyword">
                                       <div className="fM f-md mb-1">NLP Content Suggestions</div>
                                       <ul className="overflow-y-auto mt-2">
                                          {contentSuggestions.map((eachKeyword, index) => (
                                             <li
                                                className={usedContentSuggestions.includes(eachKeyword) ? "cursorP activetag" : "cursorP"}
                                                key={index}
                                             >
                                                <span className="p-r10">{eachKeyword}</span>
                                             </li>
                                          ))}
                                       </ul>
                                    </div>
                                 </div>
                              </Grid>
                              ) : null}

                           </Grid>
                        </Grid>

                     </Grid>
                  </section >
               </>)
         }
      </>
   )
}

export default CEditor;
