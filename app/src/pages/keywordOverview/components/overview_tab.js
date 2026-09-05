import React from "react";
import { isRanked, rankCeiling, rankExplanation, rankLabel, rankState } from "../../../utils/rank_state";
import RecheckAction from "../../commonComponents/recheck_action";
import { Link } from "react-router-dom";
import "../style.scss";
import { Rating, Tooltip, Zoom } from "@mui/material";

import { DesktopIcon, MobileIcon, ExactDomainIcon, GoogleFullClrIcon, FillArrow } from "../../commonComponents/icons";
import { fstLtrCapitalfun, getfulldate, openLiveGoogleSerp } from "../../common_fun";
import ManageTagFullPage from "../../commonComponents/manage_tag_full_page";
import KWGooglePage from "../../serpRank/components/keyword_google_page";
import KWTypoerror from "../../serpRank/components/keyword_typo_error";
import SerpFeatures from "./serp_features";
import KeywordConfigDialog, { KeywordConfigFacts, PRECEDENCE_NOTE } from "./keyword_config";
import { Para, AppTooltip, Tsk } from "../../commonComponents/parts";
import { Button } from "@/components/ui/button";
import { toast } from "react-toastify";
import CountryFlag from "../../commonComponents/country_flag";

export const  Snippetdetails = ({kwdata, snp}) => {

   return (
      <>
      {(snp && Object.keys(snp).length > 0) ?
         <div className="d-flex justify-content-between snippet">
            <div className={(snp.img && snp.img !== "") ? "w-80pr text-left" : "w-100 text-left"} >
               <a target="_blank" href={snp.lk} rel="noopener noreferrer">
               <div className="f14x gpretitle txtOverflowEllipsis">{ (snp.mt && snp.mt.length > 0) ? snp.mt.map((i) => <span key={i.toString()}>{i}</span>) : null }</div>
               <h3 className="kwgtitle txtOverflowEllipsis">{ snp.tt }</h3> </a>
               <div className="f14x text-justify twolinetxtOverflowEllipsis discription">{ snp.ds ? snp.ds[0] : null }</div>

               { (snp.rt && parseInt(snp.rt) > 0 ) ?
                   <div className="f14x lh20x d-flex rating align-items-center">
                      <Rating name="half-rating-read" size="small" value={snp.rt ? parseFloat(snp.rt) : 0} precision={0.5} readOnly />
                      <span className="rtrvw m-l5"> <span>Rating: {snp.rt}</span> · <span>{snp.rv}</span> </span>
                   </div>
               : null }
            </div>
            { (snp.img && snp.img !== "") ?
                 <div className="imgdiv">
                     <img src={snp.img} className="img" height="92" width="92" alt="SearchMirror" />
                     <div className="img-overlay"> </div>
                 </div>
            : null }
         </div>
      : (snp && Object.keys(snp).length === 0) ?
         <p className="kwEmpty">Google returned no snippet for this result.</p>
      :
         <div className="snippet">
             <div className="w-100 text-left">
                 <div className="f14x gpretitle"><Tsk width={250} /></div>
                 <div className="f-xl f-semi pClr kwgtitle txtOverflowEllipsis m-t10 m-b10"><Tsk width={"60%"} height={20} /></div>
                 <div className="f14x f-semi m-t5 lh20x rating "> <Tsk width={"90%"} height={40} /> </div>
                 <div className="f14x f-semi lh20x rating m-t5"> <Tsk width={250} /> </div>
             </div>
         </div>
      }
      </>
   )
}


//
export default function KWOverview({kwdata, tagUpdate, keyid, tabledataUpdate, canManageTags, canFixSpelling, canEditConfig, reloadKeyword}) {

  const managetagopenFunc = React.useRef(null)

  // The saved config, not a copy of the form. /keyauth publishes it on both
  // paths and the save endpoint returns the row it just wrote, so the page
  // never renders a value it only hopes was stored.
  const [config, setConfig] = React.useState(null);
  const [configOpen, setConfigOpen] = React.useState(false);
  React.useEffect(() => { setConfig(kwdata.cfg || null); }, [kwdata.cfg]);

  // "" is no suggestion, "-" is one already dismissed. Anything else is the one
  // field of a keyword the backend can still change (/typoerrorfix).
  const spellingSuggestion = kwdata.kwas && kwdata.kwas !== "-" ? kwdata.kwas : "";

  /* Whether the "best" SERP view would render exactly what the current one
     does. Compared on the rendered snippet -- link, title, description -- not
     on the ranks, because two different ranks can still have produced the same
     result row and it is the DRAWING that would be duplicated. */
  const serpFingerprint = (snp) => {
     if (!snp || typeof snp !== "object" || Object.keys(snp).length === 0) return "";
     return JSON.stringify([snp.lk || "", snp.tt || "", (snp.ds && snp.ds[0]) || ""]);
  };
  const currentPrint = serpFingerprint(kwdata.spt);
  const bestPrint = serpFingerprint(kwdata.spb);
  const sameSerpView = Boolean(currentPrint) && currentPrint === bestPrint;

  const openLiveSerp = () => {
     openLiveGoogleSerp(keyid).catch((error) => {
        toast.error(error.message || "Could not open live Google results");
     });
  }



   const CGoogle = (
      <div>
         <Para>
            Your present rank on Google's SERP for the keyword.
         </Para>
      </div>
   );
   const BGoogle = (
      <div>
         <Para>
         Your best rank on Google's SERP for the same keyword
         </Para>
      </div>
   );
   const Current = (
      <div>
         <Para>
            Present position of your keyword.
         </Para>
      </div>
   );
   const Last = (
      <div>
         <Para>
         Previous position of your keyword.
         </Para>
      </div>
   );
   const Best = (
      <div>
         <Para>
         Your best ranking so far.
         </Para>
      </div>
   );

   const Improved = (
      <div>
         <Para>
         The difference between your present ranking position and your previous ranking position.
         </Para>
      </div>
   );

   /// FLAG
   const Flag = ({code, height="20", width="20" }) => {
      return (
         <CountryFlag
            style={{ borderRadius: "3px" }}
            loading="lazy"
            className="flag md"
            width={width}
            height={height}
            code={code}
         />
      );
   };

   return (
      <>
         {canManageTags ? <ManageTagFullPage type="kwoverview" managetagopenFunc={managetagopenFunc} kwdata={kwdata} tagUpdate={tagUpdate} /> : null}

         <KeywordConfigDialog
            open={configOpen}
            onClose={() => setConfigOpen(false)}
            cfg={config}
            keyid={keyid}
            onSaved={setConfig}
         />

         {/* A check that produced nothing is said on the keyword itself, not
             only as a count in a project-wide banner -- and with the same
             priced, confirmed re-check the banner offers, so the user can act
             on it from where they noticed it. */}
         {rankState(kwdata) === "not_measured" ? (
            <div className="kwFailedNote">
               <p className="kwFailedNote__text">
                  {rankExplanation(kwdata)}
                  {kwdata.lrupt ? " Last checked " + kwdata.lrupt + "." : ""}
               </p>
               <RecheckAction
                  className="kwFailedNote__action"
                  action={{
                     kind: "recheck",
                     keyword_ids: [keyid],
                     label: "Re-check this keyword",
                     cost_note: "This spends " + (rankCeiling(kwdata) ? rankCeiling(kwdata) / 10 : 3) +
                        " DataBlue searches, billed to your own API key.",
                  }}
                  onDone={reloadKeyword}
               />
            </div>
         ) : null}

         {/* Four figures across the top of the page. No tiles: the label is
             above the number, and a hairline is all the separation four
             numbers in a row ever needed. */}
         <div className="kwStats">
            <div className="kwStat">
               <div className="kwStatLabel">
                  <Tooltip title={Current} placement="bottom-start">
                     <span className="kwStatLabelHint">Current</span>
                  </Tooltip>
               </div>
               <div className="kwStatValue">
                  {/* Read from the state, not from RK[0]. The old test printed
                      a hardcoded ">30" for any zero, which is the wrong ceiling
                      for a keyword not tracked at three pages and says nothing
                      about a check that failed outright. */}
                  { !kwdata.RS && (!kwdata.RK || kwdata.RK.length === 0) ?
                    <Tsk width={60} height={34} />
                  : isRanked(kwdata) ?
                    <span>{kwdata.RW}</span>
                  :
                    <Tooltip title={rankExplanation(kwdata)} placement="bottom-start">
                      <span className="kwStatNone">{rankLabel(kwdata, true)}</span>
                    </Tooltip>
                  }
               </div>
            </div>

            <div className="kwStat">
               <div className="kwStatLabel">
                  <Tooltip title={Last} placement="bottom-start">
                     <span className="kwStatLabelHint">Last</span>
                  </Tooltip>
               </div>
               <div className="kwStatValue">
                  {/* Yesterday's entry. A history row carries no failure
                      marker, so a zero there can only mean "did not appear in
                      the depth searched that day" -- worded against this
                      keyword's own ceiling rather than a fixed one. */}
                  { (!kwdata.RK || kwdata.RK.length === 0) ?
                    <Tsk width={60} height={34} />
                  : (kwdata.RK.length > 1 && kwdata.RK[1] === 0) ?
                    <span className="kwStatNone">{rankCeiling(kwdata) ? "> " + rankCeiling(kwdata) : "Not ranked"}</span>
                  : (kwdata.RK.length < 2 && kwdata.OD === 0) ?
                    <span className="kwStatNone">—</span>
                  : (kwdata.RK.length > 1) ?
                    <span>{kwdata.RK[1]}</span>
                  : null }
               </div>
            </div>

            <div className="kwStat">
               <div className="kwStatLabel">
                  <Tooltip title={Improved} placement="bottom-start">
                     <span className="kwStatLabelHint">Change</span>
                  </Tooltip>
               </div>
               <div className="kwStatValue">
                  { kwdata.OD ?
                     <>
                     <span>{ Math.abs(kwdata.OD) }</span>
                     <span className={"arrow "+ (kwdata.OD < 0 ? "red" : "green")}>
                       <FillArrow width="14" height="10" />
                     </span>
                     </>
                  : (kwdata && kwdata.OD === 0) ?
                     <span className="kwStatNone">—</span>
                  : <Tsk width={60} height={34} /> }
               </div>
            </div>

            <div className="kwStat">
               <div className="kwStatLabel">
                  <Tooltip title={Best} placement="bottom-start">
                     <span className="kwStatLabelHint">Best</span>
                  </Tooltip>
               </div>
               <div className="kwStatValue">
                  { kwdata.brnk ?
                     <span>{kwdata.brnk}</span>
                  : (kwdata && kwdata.brnk === 0) ?
                     <span className="kwStatNone">—</span>
                  : <Tsk width={60} height={34} /> }
               </div>
            </div>
         </div>

         <div className="kwCols">
            {/* One grid column, so the note is not a third grid child. */}
            <div className="kwFactsCol">
            {/* Every one of these is now editable, so the column gets the same
                header-with-an-action the Tags panel opposite it has. */}
            <div className="kwSectionHead">
               <div className="kwSectionTitle">Tracking setup</div>
               {canEditConfig && config ? <Button
                  type="button"
                  variant="secondary"
                  className="sm p-r10 p-l10 h28x"
                  onClick={() => setConfigOpen(true)}
               >
                  <span>Edit</span>
               </Button> : null}
            </div>

            {/* What this keyword is: label/value pairs, read down. */}
            <dl className="kwFacts">
               <div className="kwFact">
                  <dt className="kwFactLabel">
                     Target page
                     <span className="kwFactAside">the page you expect to rank</span>
                  </dt>
                  <dd className="kwFactValue ovrwUrl">
                     { kwdata.SR ?
                        <Tooltip classes={{ tooltip: "Tltpsmall text-center d-flex align-items-center" }} TransitionComponent={Zoom} placement="top" title={kwdata.SR} >
                           <a target="_blank" href={kwdata.SR} rel="noopener noreferrer">
                              { kwdata.edm ? <span className="kwFactMark"><ExactDomainIcon width="13" height="13" color="currentColor" /></span> : null }
                              <span>{kwdata.SR}</span>
                           </a>
                        </Tooltip>
                     :
                        <Tsk width={180} height={14} />
                     }
                  </dd>
               </div>

               <div className="kwFact">
                  <dt className="kwFactLabel">Last update</dt>
                  <dd className="kwFactValue">{kwdata.lrupt ? kwdata.lrupt : <Tsk width={180} height={14} /> }</dd>
               </div>

               <div className="kwFact">
                  <dt className="kwFactLabel">Platform</dt>
                  <dd className="kwFactValue">
                     { !kwdata.PM ?
                        <Tsk width={100} height={14} />
                     : kwdata.PM === "M" ?
                        <>
                           <span className="kwFactMark"><MobileIcon width="13" height="15" color="currentColor" /></span>
                           <span>Mobile</span>
                        </>
                     :
                        <>
                           <span className="kwFactMark"><DesktopIcon width="16" height="14" color="currentColor" /></span>
                           <span>Desktop</span>
                        </>
                     }
                  </dd>
               </div>

               <div className="kwFact">
                  <dt className="kwFactLabel">Search engine</dt>
                  <dd className="kwFactValue">
                     { kwdata.cd ?
                        <>
                           <span className="kwFactMark"><GoogleFullClrIcon /></span>
                           <span>Google</span>
                           <button type="button" className="kwFactAction" onClick={openLiveSerp}>View live SERP</button>
                        </>
                     :
                        <Tsk width={100} height={14} />
                     }
                  </dd>
               </div>

               <div className="kwFact">
                  <dt className="kwFactLabel">Country</dt>
                  <dd className="kwFactValue">
                     { kwdata.lct ?
                        <>
                           { kwdata.io ? <span className="kwFactMark"><Flag code={kwdata.io} height={12} width={18} /></span> : null }
                           <span>{kwdata.lct}</span>
                        </>
                     :
                        <Tsk width={180} height={14} />
                     }
                  </dd>
               </div>

               <div className="kwFact">
                  <dt className="kwFactLabel">Language</dt>
                  <dd className="kwFactValue">{ kwdata.lng ? kwdata.lng : <Tsk width={180} height={14} /> }</dd>
               </div>

               {/* Pages, depth and the match rule. Skeletons rather than
                   defaults while /keyauth is in flight: a "1 page" drawn
                   before the read lands is a number nobody chose. */}
               { config ? <KeywordConfigFacts cfg={config} /> :
                  [1,2,3].map((i) =>
                     <div className="kwFact" key={i.toString()}>
                        <dt className="kwFactLabel"><Tsk width={110} height={11} /></dt>
                        <dd className="kwFactValue"><Tsk width={200} height={14} /></dd>
                     </div>
                  )
               }

               {/* "Results reported by Google" used to sit here. parser_json.py
                   sets TOTAL_RESULTS to "-" unconditionally, so no current path
                   can populate it -- the row could only ever read "Not
                   reported" beside a sentence explaining why. A field that can
                   never say anything is not a field. If the provider starts
                   returning a result count, add it back with the value. */}

               <div className="kwFact">
                  <dt className="kwFactLabel">Created on</dt>
                  <dd className="kwFactValue">{kwdata.cd ? getfulldate(kwdata.cd) : <Tsk width={160} height={14} /> }</dd>
               </div>
            </dl>

            {/* Says which tier each value comes from and where the defaults
                live, in the same sentence the project settings panel uses. */}
            {/* Five lines of running prose used to sit here, unavoidable,
                below a list of measured values. It is worth reading once and
                never again, so it is reachable rather than in the way. A
                <details> element, not a state hook: it needs no JavaScript and
                it is what the control actually is. */}
            <details className="kwFactsNote">
               <summary className="kwFactsNoteSummary">How these settings are chosen</summary>
               <p className="kwFactsFoot">
                  {PRECEDENCE_NOTE} Country, language and device each change which Google search is
                  run, so a keyword measured on one combination keeps that history. The defaults
                  every keyword inherits are on{" "}
                  <Link className="kwFactsFootLink" to="/settings/apikey">the DataBlue API Key tab</Link>,
                  which is also where you can push them back onto every keyword at once. Changing
                  any of this does not re-check the keyword.
               </p>
            </details>
            </div>

            <div className="kwPanels">
               <section className="kwSection smallButton">
                  <div className="kwSectionHead">
                     <div className="kwSectionTitle">Tags</div>
                      {/* The dialog behind it is "Manage tags" and removes too. */}
                      {canManageTags ? <Button
                       type="button"
                       variant="secondary"
                       className="sm p-r10 p-l10 h28x"
                       onClick={() => managetagopenFunc.current([keyid])}
                     >
                       <span>Edit</span>
                      </Button> : null}
                  </div>
                  <div className="kwTags">
                     { (kwdata.tg && kwdata.tg.length > 0) ?
                        kwdata.tg.map((tag) =>
                           <div className="tag" key={tag.toString()}>{fstLtrCapitalfun(tag)}</div>
                        )
                     : (kwdata.tg && kwdata.tg.length === 0) ?
                        <p className="kwEmpty">No tags on this keyword yet. Add one to group it with related keywords.</p>
                     :
                        [1,2,3].map((i) =>
                           <Tsk width={90} height={26} key={i.toString()} />
                        )
                     }
                  </div>
               </section>

               {/* Applying it rewrites the tracked term, so it is an offer with
                   two answers. KWTypoerror is the keywords table's control,
                   reused whole -- its wording lives in serpRank/. */}
               {spellingSuggestion && canFixSpelling ?
                  <section className="kwSection">
                     <div className="kwSectionHead">
                        <div className="kwSectionTitle">Spelling</div>
                     </div>
                     <div className="kwTypoInline">
                        <KWTypoerror row={kwdata} tableUpdate={reloadKeyword} updatefullpage={reloadKeyword} />
                        <p className="kwEmpty">
                           Fixing retracks this keyword under Google's spelling; ignoring keeps the
                           one you entered.
                        </p>
                     </div>
                  </section>
               : null}

               <section className="kwSection">
                  <div className="kwSectionHead">
                     <div className="kwSectionTitle">SERP features</div>
                  </div>
                  <SerpFeatures kwdata={kwdata} />
               </section>

               {/* Two headed sections showing the same thing is not two facts.
                   When the current result IS the best one -- which is the
                   common case, and was true of every keyword on this project --
                   the page drew the identical snippet twice under different
                   titles. Compared on what is actually rendered, not on the
                   ranks behind it. */}
               <section className="kwSection">
                  <div className="kwSectionHead">
                     <div className="kwSectionTitle">
                        {sameSerpView ? "Google SERP view" : "Current Google SERP view"}
                        <AppTooltip place="bottom-end" title={CGoogle} color="currentColor" />
                     </div>
                     <KWGooglePage row={kwdata} lstresult={[kwdata]} tabledataUpdate={tabledataUpdate} pagetype="kwoverview" />
                  </div>

                  <Snippetdetails kwdata={kwdata} snp={kwdata.spt ? kwdata.spt : null} />

                  {sameSerpView ? (
                     <p className="kwEmpty">This is also the best result recorded for this keyword.</p>
                  ) : null}
               </section>

               {sameSerpView ? null : (
               <section className="kwSection">
                  <div className="kwSectionHead">
                     <div className="kwSectionTitle">
                        Best Google SERP view
                        <AppTooltip place="bottom-end" title={BGoogle} color="currentColor" />
                     </div>
                  </div>

                  <Snippetdetails kwdata={kwdata} snp={kwdata.spb ? kwdata.spb : null} />
               </section>
               )}
            </div>
         </div>
      </>
   );
}
