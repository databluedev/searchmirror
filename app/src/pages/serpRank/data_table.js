import React, { useEffect, useState, useMemo, useRef } from "react";
import { isRanked, rankExplanation, rankLabel, rankSortKey } from "../../utils/rank_state";
import DataTable from "react-data-table-component";
import { DayDiffTool, ExactURLTool, GSCToolTip } from "./gridTableComponents/tool_tip";
import { Box, Tooltip, useMediaQuery, Zoom } from "@mui/material";
import { AppTooltip, Tsk, Csk } from "../commonComponents/parts";
import ClickAway from "../commonComponents/click_away";
import ManageTagFullPage from "../commonComponents/manage_tag_full_page";
import { DataEmptyIcon, FillArrow, RefreshIcon, ExactDomainIcon, GoLinkIcon, FeatureSnptIcon, TagIcon, GoOverviewPageIcon, SortingIcon } from "../commonComponents/icons";
import { getfulldate, convertSiteUrl, fstLtrCapitalfun, VolTool, SFRatingClrIcon } from "../common_fun";
import Cookies from 'universal-cookie';
import { SIMPLE_FEATURES, AD_FEATURES, SNIPPET_FEATURES } from "./serp_features";
import KWTypoerror from "./components/keyword_typo_error";

import { KnowMore } from "../../utils/external_link";
import { plainText } from "../../utils/provider_text";

const orderChange = (data, order) => {
   const ordered = Object.keys(order)
      .map((columnId) => data.find((column) => column.id === columnId))
      // A saved legacy column preference can outlive the provider-backed
      // column itself. react-data-table cannot accept undefined columns.
      .filter(Boolean)

   // The mirror of that: a column added after a project saved its order is
   // absent from the saved order, and dropping it would hide it permanently.
   return ordered.concat(data.filter((column) => !(column.id in order)))
}

/* The AIO column answers one question -- is my site quoted by Google's AI --
   so every state answers it in a word rather than in a glyph the reader has to
   decode. A filled sparkle and an outline sparkle differ only in fill at 16px,
   which made "you are cited" and "someone else is cited" look alike, and the
   count of cited sites was a number about Google, not about the reader.

   Weight carries the ladder: accent for the win, ink-2 for the opportunity,
   ink-3 for the measured absence, a dash for the states nobody measured. */
const AI_OVERVIEW_CELL = {
   owned: { word: "Cited", sparkle: true, tone: "aioOwned" },
   shown: { word: "Shown", sparkle: true, tone: "aioShown" },
   absent: { word: "None", sparkle: false, tone: "aioAbsent" },
   lite: { word: "—", sparkle: false, tone: "aioUnknown" },
   unknown: { word: "—", sparkle: false, tone: "aioUnknown" },
   never: { word: "—", sparkle: false, tone: "aioUnknown" },
};

// "unavailable"/"unknown"/never-parsed are absences of measurement, not a
// measured "no", so they get the dash and never the word.
const AI_OVERVIEW_TIP = {
   owned: "Your site is cited in Google's AI Overview.",
   shown: "Google showed an AI Overview. Your site is not among its cited sources.",
   absent: "Google showed no AI Overview for this search.",
   lite: "Not measured — AI Overview is only returned on an Advanced run.",
   unknown: "Not measured — the provider did not report the search depth.",
   never: "Not measured — this keyword has not been ranked since AI Overview tracking was added.",
};

const aiOverview = (row) => {
   const features = row.sf || {};
   const block = features.ai_overview;
   if (!block || !block.state) return { kind: "never", sources: [] };

   const sources = Array.isArray(block.sources) ? block.sources : [];
   if (block.state === "present") return { kind: block.owned ? "owned" : "shown", sources };
   if (block.state === "absent") return { kind: "absent", sources: [] };
   return { kind: features.mode === "unknown" ? "unknown" : "lite", sources: [] };
};

const AI_OVERVIEW_SORT = { owned: 0, shown: 1, absent: 2, lite: 3, unknown: 3, never: 3 };

function AIOverviewIcon({ filled }) {
   return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
         <path
            d="M12 3.2l1.95 5.35L19.3 10.5l-5.35 1.95L12 17.8l-1.95-5.35L4.7 10.5l5.35-1.95L12 3.2z"
            fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"
         />
         <path
            d="M18.7 15.4l.75 2.05 2.05.75-2.05.75-.75 2.05-.75-2.05-2.05-.75 2.05-.75.75-2.05z"
            fill={filled ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round"
         />
      </svg>
   );
}

// Source titles arrive with the provider's markup in them, so they go through
// plainText -- rendering them raw showed a literal "<b>" to the reader.
const aiOverviewTip = (kind, sources) => (
   <div className="lh18x">
      <div>{AI_OVERVIEW_TIP[kind]}</div>
      {sources.length > 0 ?
         <div className="m-t5 text-start">
            {sources.slice(0, 4).map((source, k) => {
               const domain = plainText(source && source.domain);
               const title = plainText(source && source.title);
               return (
                  <div key={k} className="maxW240x m-t5">
                     <div className="text-truncate fM">{domain}</div>
                     {title ? <div className="text-truncate f12x newlightTxtClr">{title}</div> : null}
                  </div>
               );
            })}
            {sources.length > 4 ? <div className="f12x m-t5">{"+" + (sources.length - 4) + " more"}</div> : null}
         </div>
         : null}
   </div>
);

export default function LstDataTable({ managetagopenFunc, resetSelectedRowIds, kwCount, lstresult, lstfltrresult, tableUpdate, tabledataUpdate, gridtableUpdate, handleRowSelected, selectedRowIds, updatefullpage, projectbase, keywordpageroute, canSelectKeywords }) {

   /* On a phone this table laid out at its full desktop width inside a 356px
      scroller, which put RANK -- the one number the product exists to show --
      and the chevron into the keyword 150-570px past the right edge, so both
      were reachable only by scrolling sideways inside the table, which is the
      thing no one does.

      Below 576px the row keeps what a phone can act on: the keyword, its rank,
      its best rank and the link into the keyword. The columns that drop are
      still there on a wider screen, and everything they carried -- the SERP
      features, the tags, the last-checked date -- is on the keyword's own
      page, one tap away through the chevron that now fits. */
   const narrow = useMediaQuery("(max-width:575.98px)");

   /* CLKS and IMPS are Search Console figures. Google Search Console is parked
      on this build until it has a server-side OAuth flow, so with no client id
      configured no project can have a click or an impression -- and both
      columns default to on, which printed a column of 0 next to every keyword
      on a 30-keyword project. A 0 there is not "no clicks", it is "not
      connected", and the two are different facts. With no client id the
      columns are not shown at all, and the Column menu does not offer them. */
   const gscConfigured = Boolean(global.gscClientId);

   const [totalRows, setTotalRows] = useState(kwCount);
   const [perPage, setPerPage] = useState(25);

   // const history = useHistory();

   const [toggleCleared, setToggleCleared] = useState(false);
   const hadSelectionRef = useRef(false);

   useEffect(() => {
      setTotalRows(kwCount)
      /* `clearSelectedRows` is an edge, not a level: flipping it tells rdt to
         dispatch CLEAR_SELECTED_ROWS. selectedRowIds is a new array on every
         setSelectedRowIds call, so the unguarded version flipped it -- and made
         rdt clear and re-render -- on every selection change including the ones
         that had just added a row. Flip it only on the transition into empty. */
      if (selectedRowIds.length === 0 && hadSelectionRef.current) {
         setToggleCleared((cleared) => !cleared)
      }
      hadSelectionRef.current = selectedRowIds.length > 0

      const cookies = new Cookies();
      const savedPageSize = parseInt(cookies.get('__sp_pg_lmt__'), 10)
      const lstblPgSize = [10, 25, 50, 100].includes(savedPageSize) ? savedPageSize : 25
      setPerPage(parseInt(lstblPgSize))

      // kwsearchFunc.current = listkwsearchFuc
      // eslint-disable-next-line react-hooks/exhaustive-deps


   }, [lstresult.length, kwCount, selectedRowIds]);

   const conditionalRowStyles = useMemo(() => [
      {
         when: row => selectedRowIds.includes(row.key),
         style: {
            // Tokens, not hex -- rdt writes this straight onto the row as an
            // inline style, which is the only thing that outranks its own
            // styled-components rules. See docs/DESIGN.md "Table".
            backgroundColor: "var(--accent-weak)",
            borderBottomColor: "var(--line-2)",
            userSelect: "none"
         }
      }
   ], [selectedRowIds]);


   // The per-row icons and the legend under the table read one code/icon/label
   // list -- see serp_features.js. They used to be two hand-written copies of
   // the same fifteen triples in two files. The rating keeps a tooltip of its
   // own because that one carries the rating value, not the legend's text.
   const snippetFeatures = (sValue, rating = 0) => {
      if (sValue.length > 0) {
         // Both groups are mutually exclusive per row: the first match wins,
         // so 'Ain' outranks the fold positions and 'fs1' outranks 'fs0'.
         const ad = AD_FEATURES.find((feature) => sValue.includes(feature.code));
         const snippet = SNIPPET_FEATURES.find((feature) => sValue.includes(feature.code));

         return (
            <>
               {sValue.includes('rv') === true ?
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={rating !== "-" ? <>You have {rating} star ratings</> : "Reviews found"} TransitionComponent={Zoom} >
                     <span className="cursorNO"> <SFRatingClrIcon value={rating} /> </span>
                  </Tooltip>
                  : null}
               {ad ?
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={ad.label} TransitionComponent={Zoom} >
                     <span className="cursorNO"> {ad.icon} </span>
                  </Tooltip>
                  : null}

               {snippet ?
                  <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={<div className="lh18x"><div> {snippet.label} </div> <KnowMore href={global.featursnipt} className="f12x m-l5 fw600 text-underline fM pClr" /> </div>} TransitionComponent={Zoom} >
                     <span className="cursorNO">  {snippet.icon} </span>
                  </Tooltip>
                  : null}

               {SIMPLE_FEATURES.map((feature) => (
                  sValue.includes(feature.code) === true ?
                     <Tooltip key={feature.code} classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={feature.label} TransitionComponent={Zoom} >
                        <span className="cursorNO"> {feature.icon} </span>
                     </Tooltip>
                     : null
               ))}
            </>
         );
      }
      else
         return (
            <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={<div className="lh18x"><div> {"The result has a featured snippet"} </div> <KnowMore href={global.featursnipt} className="f12x m-l5 fw600 text-underline fM pClr" /> </div>} TransitionComponent={Zoom} >
               <span className=""> <FeatureSnptIcon /> </span>
            </Tooltip>
         )
   }

   // No ACTIONS column: live Google page, rank history and favourite are all on
   // the keyword's own page, one click away through the chevron.
   const columns = useMemo(() => [
      {
         id: "kw",
         name: <div className="p-l15"> KEYWORD </div>,
         // rdt gives every column `flex-grow: 1; flex-basis: 0` and falls back
         // to `max-width: 100%` when no maxWidth is set. KEYWORD was the only
         // column without one, so it absorbed all the slack -- 826px on a
         // project where the delta and GSC columns are omitted, which pushed
         // the numbers to the far edge and left a hole mid-table. A cap keeps
         // the numerals next to the content they describe. 560px is still
         // ~70ch, more than the truncation width the cell already enforces.
         /* react-data-table gives every column flex-grow:1, so KEYWORD takes
            whatever the others leave. On a 356px scroller that is enough slack
            to push RANK back off the edge, which is what the cap is for:
            32 checkbox + 230 keyword + 58 rank + 35 chevron = 355. BEST is the
            column that gives way for those 55px: at 175px the keyword itself
            truncated to "competit..." and "backlink m...", which makes two rows
            indistinguishable, and a best-ever rank is worth less than knowing
            which keyword you are looking at. It is on the keyword's own page,
            beside the current rank, with the change between them. */
         minWidth: narrow ? "120px" : "400px",
         maxWidth: narrow ? "230px" : "560px",
         /* The cell's truncation caps are fixed pixel classes (maxW300x,
            maxW315x, maxW260x ...) sized for the desktop column. At the narrow
            cap they are wider than the column, and nothing in the chain
            established a containing block, so the keyword ran under RANK.
            overflow:hidden here plus min-width:0 down the flex chain makes the
            column the limit. */
         style: { display: "grid", overflow: "hidden" },
         sortable: true,
         selector: (row) => row.KW,
         cell: (row, index, column, id) => (
            <div
               className="d-flex align-items-center p-l15 p-r10 py-2"
               style={{ minWidth: 0 }}
            >

               <div className="d-flex align-items-center overflow-hidden" style={{ minWidth: 0 }}>
                  <div className="d-flex align-items-center" style={{ minWidth: 0 }}>
                     {row.KW ?
                        <div style={{ minWidth: 0 }}>
                           <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={row.KW} TransitionComponent={Zoom}>
                              <div style={narrow ? { maxWidth: "100%" } : undefined} className={"text-truncate m-r5 m-b5 cursorP " + (((row.kwas !== '' && row.kwas !== '-') || row.cnn) ? "maxW300x" : "maxW315x")} onClick={() => keywordpageroute(row)}>
                                 {row.KW}
                              </div>
                           </Tooltip>
                           <div className="d-flex" style={{ minWidth: 0 }}>
                              {row.edm ? <div className="d-flex m-r5"><ExactDomainIcon /></div> : null}
                              <div style={narrow ? { maxWidth: "100%" } : undefined} className={"text-truncate f12x lh14x newlightTxtClr " + (((row.kwas !== '' && row.kwas !== '-') || row.cnn) ? "maxW260x" : row.edm ? "maxW260x" : "maxW280x")}>
                                 {convertSiteUrl(row.SR)}
                              </div>
                              <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={<ExactURLTool url={row.SR} exact={row.edm} />} TransitionComponent={Zoom}>
                                 <a href={row.SR} className="lh20x d-flex align-items-center" target="_blank" rel="noopener noreferrer">
                                    <GoLinkIcon height={10} width={10} className={"m-l5 newlightTxtClr"} />
                                 </a>
                              </Tooltip>
                           </div>
                        </div>
                        :
                        <div className="">
                           <div className="maxW240x text-truncate m-r5 m-b5">
                              <Tsk width={180} />
                           </div>
                           <div className={"maxW240x text-truncate fsES lh14x " + (row.edm ? "pClr" : "lightTxtClr")}>
                              <Tsk width={280} />
                           </div>
                        </div>
                     }
                  </div>
               </div>
               <div
                  className="d-flex align-items-center m-l10"
                  style={{ flex: "0 0 auto" }}
               >
                  <div className="d-flex m-r5">
                     <div className="keywordCheckIcon mr-2 redIcon">
                        {((row.kwas !== '' && row.kwas !== '-') || row.cnn) ?
                           <AppTooltip className="red md p-2 typoerrortooltip" dimension="14"
                              title={
                                 <div className="p-1">
                                    {(row.kwas !== '' && row.kwas !== '-') &&
                                       <KWTypoerror row={row} tableUpdate={tableUpdate} updatefullpage={updatefullpage} />
                                    }
                                    {row.cnn &&
                                       <>
                                          {(row.kwas !== '' && row.kwas !== '-') ? <div className="brdBottom m-t10 m-b5" /> : null}
                                          <div className="text-center lh22x">
                                             <span>{"Fix "}</span>
                                             <span><b className="pClr f-wg600 fM mx-1">{"'" + row.KW + "'"}</b></span>
                                             <span>{" keyword cannibalization issues ! "} </span>
                                             <span className="fM pClr mx-1"> <KnowMore href={global.cannbltnurl} className="f-xsm ml-1 f-wg600 fM text-underline pClr" /></span>
                                          </div>
                                       </>
                                    }
                                 </div>
                              }
                              place="top"
                           />
                           : null
                        }
                     </div>
                  </div>
               </div>
            </div>
         ),
      },

      {
         // id: "rnk",
         id: "rank",
         name: "RANK",
         right: true,
         sortable: true,
         class: "bgGrey",
         minWidth: narrow ? "50px" : "60px",
         maxWidth: narrow ? "58px" : "80px",
         // Sorted on RSK, not RW: RW is null for everything that does not
         // rank, and null has no order. RSK sorts those past every real rank
         // without pretending to be a position.
         selector: (row) => rankSortKey(row),
         cell: (row, index, column, id) => (
            isRanked(row) ?
               <span className="fM">{row.RW}</span>
            : (row.RK && row.RK.length > 0) || row.RS ?
               <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={rankExplanation(row)} TransitionComponent={Zoom}>
                  <span className="fM lightgray">{rankLabel(row, true)}</span>
               </Tooltip>
            :
               <Tsk width={30} />
         ),
      },

      {
         id: "clks",
         name: <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} title="Total clicks in the past 7 days." placement="top"><div>CLKS</div></Tooltip>,
         right: true,
         sortable: true,
         class: "bgGrey",
         minWidth: "10px",
         maxWidth: "76px",
         omit: narrow || !gscConfigured || !projectbase.lth['clks'],
         selector: (row) => row.clks === "-" ? 100000000 : parseInt(row.clks),
         cell: (row, index, column, id) => (
            /* A real row with no clks at all means this project is not
               connected to Search Console -- the API omits the field rather
               than sending a zero. The skeleton below is for a row still
               loading, and would otherwise shimmer forever. */
            (row.clks) ?
               <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={row.clks_v !== "NC" && <GSCToolTip row={row} type="clks" />} TransitionComponent={Zoom}>
                  <div className="d-flex align-items-center">
                     <VolTool value={row.clks} />
                     <span className={(row.clks_v === "H" ? 'arrow green m-l5 d-flex' : row.clks_v === "D" ? 'arrow red m-l5 d-flex' : 'd-none')}>
                        <FillArrow />
                     </span>
                  </div>
               </Tooltip>
            : row.RS ?
               <span className="fM lightgray" title="Not connected to Search Console.">—</span>
            :
               <Tsk width={30} />
         ),
      },


      {
         id: "imps",
         name: <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} title="Total impressions in the past 7 days." placement="top"><div>IMPS</div></Tooltip>,
         right: true,
         class: "bgGrey",
         minWidth: "10px",
         maxWidth: "76px",
         sortable: true,
         omit: narrow || !gscConfigured || !projectbase.lth['imps'],
         selector: (row) => row.imps === "-" ? 100000000 : parseInt(row.imps),
         cell: (row, index, column, id) => (
            /* A real row with no imps at all means this project is not
               connected to Search Console -- the API omits the field rather
               than sending a zero. The skeleton below is for a row still
               loading, and would otherwise shimmer forever. */
            (row.imps) ?
               <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={row.imps_v !== "NC" && <GSCToolTip row={row} type="imps" />} TransitionComponent={Zoom}>
                  <div className="d-flex align-items-center">
                     <VolTool value={row.imps} />
                     <span className={(row.imps_v === "H" ? 'arrow green m-l5 d-flex' : row.imps_v === "D" ? 'arrow red m-l5 d-flex' : 'd-none')}>
                        <FillArrow />
                     </span>
                  </div>
               </Tooltip>
            : row.RS ?
               <span className="fM lightgray" title="Not connected to Search Console.">—</span>
            :
               <Tsk width={30} />
         ),
      },

      {
         id: "brk",
         name: "BEST",
         right: true,
         minWidth: "60px",
         maxWidth: "96px",
         sortable: true,
         omit: narrow || !projectbase.lth['brk'],
         selector: (row) => row.brnk,
         cell: (row, index, column, id) => (
            (row.RK && row.RK.length > 0 && row.brnk > 0) ?
               <span className="d-flex justify-content-center">{row.brnk}</span>
               : (row.RK && row.RK.length > 0 && row.brnk === 0) ?
                  <span className="fM lightTxtClr">{'-'}</span>
                  : <Tsk width={30} />
         ),
      },
      {
         id: "1d",
         name: "1D",
         right: true,
         minWidth: "60px",
         maxWidth: "92px",
         sortable: true,
         // reorder: true,
         // omit: (projectage > 1 && lsttblhdlst.includes('1d')) ? false : true,
         omit: narrow || !(projectbase.age > 1 && projectbase.lth['1d']),
         selector: (row) => row.OD,
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center justify-content-center">
               {row.KW && row.OD === 0 ?
                  <span className="fM lightTxtClr">{'-'}</span>
                  : row.KW ?
                     <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={<DayDiffTool row={row} day="1d" />} TransitionComponent={Zoom}>
                        <div className="d-flex align-items-center">
                           <span className="ml-2 fM" >{Math.abs(row.OD)}</span>
                           <span className={(row.OD > 0 ? 'arrow green m-l5 d-flex' : row.OD < 0 ? 'arrow red m-l5 d-flex' : 'd-none')}>
                              <FillArrow />
                           </span>
                        </div>
                     </Tooltip>
                     : <Tsk width={30} />}
            </div>
         ),
      },
      {
         id: "7d",
         name: "7D",
         right: true,
         minWidth: "60px",
         maxWidth: "92px",
         // maxWidth: "68px",
         sortable: true,
         // reorder: true,
         // omit: (projectage > 7 && lsttblhdlst.includes('7d')) ? false : true,
         omit: narrow || !(projectbase.age > 7 && projectbase.lth['7d']),
         selector: (row) => row.SD,
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center justify-content-center">
               {row.KW && row.SD === 0 ?
                  <span className="fM lightTxtClr">{'-'}</span>
                  : row.KW ?
                     <>
                        <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={<DayDiffTool row={row} day="7d" />} TransitionComponent={Zoom}>
                           <div className="d-flex align-items-center">
                              <span className="ml-2 fM" >{Math.abs(row.SD)}</span>
                              <span className={(row.SD > 0 ? 'arrow green m-l5 d-flex' : row.SD < 0 ? 'arrow red m-l5 d-flex' : 'd-none')}>
                                 <FillArrow />
                              </span>
                           </div>
                        </Tooltip>
                     </>
                     : <Tsk width={30} />}
            </div>
         ),
      },



      {
         id: "15d",
         name: "15D",
         right: true,
         minWidth: "60px",
         maxWidth: "92px",
         // maxWidth: "65px",
         sortable: true,
         // reorder: true,
         // omit: (projectage > 15 && lsttblhdlst.includes('15d')) ? false : true,
         omit: narrow || !(projectbase.age > 15 && projectbase.lth['15d']),
         selector: (row) => row.XD,
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center justify-content-center">
               {row.KW && row.XD === 0 ?
                  <span className="fM lightTxtClr">{'-'}</span>
                  : row.KW ?
                     <>
                        <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={<DayDiffTool row={row} day="15d" />} TransitionComponent={Zoom}>
                           <div className="d-flex align-items-center">
                              <span className="ml-2 fM" >{Math.abs(row.XD)}</span>
                              <span className={(row.XD > 0 ? 'arrow green m-l5 d-flex' : row.XD < 0 ? 'arrow red m-l5 d-flex' : 'd-none')}>
                                 <FillArrow />
                              </span>
                           </div>
                        </Tooltip>
                     </>
                     : <Tsk width={30} />}
            </div>
         ),
      },
      {
         id: "fts",
         // Inset so the right-aligned "1D" label does not run into "SERP".
         name: <div className="p-l20"> SERP </div>,
         minWidth: "58px",
         maxWidth: "84px",
         style: { paddingLeft: "20px" },
         // omit: (lsttblhdlst.includes('fts')) ? false : true,
         omit: narrow || !projectbase.lth['fts'],
         // selector: (row) => row.fs_s,
         // reorder: true,
         cell: (row, index, column, id) => (
            <>
               {((row.RK).length > 0 && row.sp.length > 0) ?
                  <>
                     <Box
                        sx={{
                           display: "grid",
                           gridTemplateColumn: "1fr 1fr 1fr 1fr 1fr 1fr",
                           gap: "3px",
                        }}
                        className="d-flex p-l10 align-items-center"
                     >
                        {snippetFeatures(row.sp.slice(0, Number(2)), row.trg)}
                        {row.sp.length > 2 ?
                           <div className="moreIcon">
                              <ClickAway height={14}>
                                 <Box
                                    sx={{
                                       display: "grid",
                                       gridTemplateColumn: "1fr 1fr 1fr 1fr 1fr 1fr",
                                       gap: "7px",
                                    }}
                                    className="d-flex flex-wrap align-items-center"
                                 >
                                    {snippetFeatures(row.sp, row.trg)}
                                 </Box>
                              </ClickAway>
                           </div>
                           : null}
                     </Box>
                  </>
                  : (row.RK).length > 0 ?
                     <span className="d-flex justify-content-center fM lightTxtClr m-l10">{'NA'}</span>
                     :
                     <Tsk width={60} className="m-l10" />
               }

               { /*(row.RK).length > 0 ?
                  row.rvw || row.fds || row.knw || row.ads || row.snp.length > 0 ? 
                    <div className="d-flex align-items-center p-l10 FSnptcolumn" style={{gap: "7px"}}>
                       {row.rvw ?
                          <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={row.trg !== "-" ? <>You have {row.trg} star ratings</> : "Reviews found"} TransitionComponent={Zoom} >
                             <span className=""> <SFRatingClrIcon value={row.trg} /> </span> 
                          </Tooltip>
                       : null}
                       {row.ads !== false && (row.ads==="Ain" || row.ads==="Atb" || row.ads==="At" || row.ads==="Ab") ? 
                          <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={row.ads === "Ain" ? "You are in Google Ads" : row.ads === "Atb" ? "Ads found above & below the fold" : row.ads === "At" ? "Ads found above the fold" : row.ads === "Ab" ? "Ads found below the fold" : ""} TransitionComponent={Zoom} >
                             <span className=""> {row.ads === "Ain" ? <AdsIcon color="#1a3cff" /> : row.ads === "Atb" ? <AdTopBottomIcon /> : row.ads === "At" ? <AdTopIcon /> : row.ads === "Ab" ? <AdbottomIcon /> : null} </span>
                          </Tooltip>
                       : null }

                       {row.fds ?  
                          <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={<div className="lh18x"><div> {row.fs_s  === "yes" ? "You are in the featured snippets" : "The result has a featured snippet"} </div> <KnowMore href={global.featursnipt} className="f12x m-l5 fw600 text-underline fM pClr" /> </div>} TransitionComponent={Zoom} >
                             <span className="">  {row.fs_s  === "yes" ? <FeatureSnptIcon color="#1a3cff" /> : <FeatureSnptIcon /> } </span>
                          </Tooltip>
                       : null}

                       {row.knw ? 
                          <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a knowledge panel"} TransitionComponent={Zoom} >
                             <span className=""> <SFKnwlgPanelIcon /> </span>
                          </Tooltip>
                       : null}

                       {(row.snp.length > 0 && row.fsc < 3) &&
                          snippetFeatures(row.snp.slice(0,Number(3)-Number(row.fsc)) )
                       }

                      {Number(row.fsc)+Number(row.snp.length) > 3 &&
                          <div className="moreIcon">
                            <ClickAway height={14}>
                              <Box
                                sx={{
                                  display: "grid",
                                  gridTemplateColumn: "1fr 1fr 1fr 1fr 1fr 1fr",
                                  gap: "7px",
                                }}
                                className="d-flex flex-wrap align-items-center"
                              >
                                {row.rvw ?
                                   <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={row.trg !== "-" ? "You have "+row.trg+" star ratings" : "Reviews found"} TransitionComponent={Zoom} >
                                      <span className=""> <SFRatingClrIcon value={row.trg} /> </span> 
                                   </Tooltip>
                                : null}
                                {row.ads !== false && (row.ads==="Ain" || row.ads==="Atb" || row.ads==="At" || row.ads==="Ab") ? 
                                   <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={row.ads === "Ain" ? "You are in Google Ads" : row.ads === "Atb" ? "Ads found above & below the fold" : row.ads === "At" ? "Ads found above the fold" : row.ads === "Ab" ? "Ads found below the fold" : ""} TransitionComponent={Zoom} >
                                      <span className=""> {row.ads === "Ain" ? <AdsIcon color="#1a3cff" /> : row.ads === "Atb" ? <AdTopBottomIcon /> : row.ads === "At" ? <AdTopIcon /> : row.ads === "Ab" ? <AdbottomIcon /> : null} </span>
                                   </Tooltip>
                                : null }

                                {row.fds ?  
                                   <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={<div className="lh18x"><div> {row.fs_s  === "yes" ? "You are in the featured snippets" : "The result has a featured snippet"} </div> <KnowMore href={global.featursnipt} className="f12x m-l5 fw600 text-underline fM pClr" /> </div>} TransitionComponent={Zoom} >
                                      <span className="">  {row.fs_s  === "yes" ? <FeatureSnptIcon color="#1a3cff" /> : <FeatureSnptIcon /> } </span>
                                   </Tooltip>
                                : null}

                                {row.knw ? 
                                   <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"The result has a knowledge panel"} TransitionComponent={Zoom} >
                                      <span className=""> <SFKnwlgPanelIcon /> </span>
                                   </Tooltip>
                                : null}

                                {(row.snp.length > 0) &&
                                   snippetFeatures(row.snp)
                                }
                              </Box>

                            </ClickAway> 
                          </div>
                      }
                    </div>
                  :
                  <span className="d-flex justify-content-center fM lightTxtClr m-l10">{'NA'}</span>
              :
                  <Tsk width={70} className="m-l10" />
              */}
            </>
         ),
      },
      {
         id: "aio",
         name: <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} title="AI Overview. Cited = Google's AI quotes your site. Shown = it answered without you. None = no AI Overview on this search. A dash means the run never looked. Advanced runs only." placement="top"><div>AIO</div></Tooltip>,
         center: true,
         minWidth: "72px",
         maxWidth: "104px",
         sortable: true,
         // Absent from a saved column order until the user re-applies the menu,
         // so it shows unless it was explicitly switched off.
         omit: narrow || projectbase.lth['aio'] === 0,
         selector: (row) => AI_OVERVIEW_SORT[aiOverview(row).kind],
         cell: (row, index, column, id) => {
            if (!row.KW) return <Tsk width={30} />;
            const { kind, sources } = aiOverview(row);
            const state = AI_OVERVIEW_CELL[kind] || AI_OVERVIEW_CELL.never;
            return (
               <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={aiOverviewTip(kind, sources)} TransitionComponent={Zoom}>
                  <span className={"aioMark " + state.tone}>
                     {state.sparkle ? <AIOverviewIcon filled={kind === "owned"} /> : null}
                     <span className="aioWord">{state.word}</span>
                  </span>
               </Tooltip>
            );
         },
      },
      {
         id: "tg",
         name: "TAGS",
         center: true,
         maxWidth: "50px",
         minWidth: "36px",
         // reorder: true,
         // omit: (lsttblhdlst.includes('tg')) ? false : true,
         omit: narrow || !projectbase.lth['tg'],
         // selector: (row) => row.tg,
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center justify-content-center flex-column tagshow">
               {row.KW && row.tg.length > 0 ?
                  <Tooltip
                     title={<div className="mb-0 tagshow d-flex flex-wrap justify-content-start">
                        {row.tg.map((tag, k) => (
                           <span key={k} className="tool_txt m-1" >{fstLtrCapitalfun(tag.toLowerCase())}</span>
                        ))}
                        <div className="tool_txt m-1 cursorP bgPentanaryClr" onClick={() => managetagopenFunc.current([row.key], row.tg, projectbase.otg)}>
                           ADD
                        </div>
                     </div>}
                     classes={{ tooltip: "TagTooltip text-center" }} TransitionComponent={Zoom} placement="top">
                     <div className="d-flex align-items-center justify-content-center">
                        <span className="text-truncate m-r5">{row.tg.length}</span>
                        <TagIcon />
                     </div>
                  </Tooltip>
                  : row.KW ?
                     <div className="f10x addtag cursorP" onClick={() => managetagopenFunc.current([row.key], row.tg, projectbase.otg)}>
                        ADD
                     </div>

                     : <Tsk width={40} />}
            </div>
         ),
      },
      {
         id: "dt",
         name: <div className="p-l10"> DATE </div>,
         // omit: (lsttblhdlst.includes('dt')) ? false : true,
         omit: narrow || !projectbase.lth['dt'],
         // selector: (row) => row.cd,
         // reorder: true,
         minWidth: "110px",
         maxWidth: "132px",
         cell: (row, index, column, id) => (
            <div className="d-flex align-items-center flex-wrap p-l10">
               <span className="w-100 m-b5"> {row.KW ? getfulldate(row.cd) : <Tsk width={86} />}</span>
               <div className="d-flex m-r5 align-items-center">
                  {row.KW ? <RefreshIcon className="refrshIcon newlightTxtClr" height="10" width="10" color="var(--ink-4)" /> : <Csk width={12} height={12} />}
                  <span className="text-truncate m-l5 f12x newlightTxtClr">{row.KW ? row.lrupt : <Tsk width={68} />}</span>
               </div>
            </div>
         ),
      },

      {
         id: "lnk",
         name: "",
         // selector: (row) => row.SR,
         minWidth: "35px",
         maxWidth: "35px",
         style: { justifyContent: 'start' },
         center: true,
         cell: (row, index, column, id) => (
            <div className="p-l3">
               <div className="d-flex justify-content-center">
                  {row.KW ?
                     <div className="nw_circleArrow cursorP" onClick={() => keywordpageroute(row)}>
                        <GoOverviewPageIcon />
                     </div>
                     : <Csk width={24} height={24} className="flag" />}
               </div>
            </div>
         ),
      },



      // eslint-disable-next-line react-hooks/exhaustive-deps 
   ], [lstresult, projectbase.age, projectbase.lth, narrow, gscConfigured]);

   /* The array handed to <DataTable columns=...> must keep its identity between
      renders. react-data-table-component runs
         useFirstUpdate(() => setTableColumns(decorateColumns(columns)), [columns])
      so a fresh array literal makes it rebuild every column object on every
      render of this component -- and its sort state (`selectedColumn`) points
      at the objects it just replaced. That is why the header stopped responding
      after the first click: the first sort worked, and every click after it
      landed on a header whose column had been swapped out from under the
      reducer. `columns` is already memoised; the ordered copy has to be too. */
   const orderedColumns = useMemo(() => [
      ...columns.slice(0, 2),
      ...orderChange(columns.slice(2, -1), projectbase.lth),
      columns[columns.length - 1],
   ], [columns, projectbase.lth]);

   //
   // const handlePageChange = page => {
   //    const cookies = new Cookies();
   //    const usertoken = cookies.get('session_token')
   //    const userid = cookies.get('session_userid')
   //    var grpid = cookies.get('activegrp')

   //    var limit = page*perPage
   //    if (lstresult.length < limit){
   //       tableUpdate(userid, grpid, 'load', limit)
   //    }
   //    // fetchUsers(page);
   // };

   const handlePerRowsChange = async (newPerPage, page) => {
      const cookies = new Cookies();
      cookies.set('__sp_pg_lmt__', newPerPage, { path: '/', maxAge: global.cookiesexpire });
      setPerPage(newPerPage)
      // setToggleCleared(!toggleCleared);



      // const usertoken = cookies.get('session_token')
      // const userid = cookies.get('session_userid')
      // var grpid = cookies.get('activegrp')

      // var limit = page*newPerPage
      // if (lstresult.length < limit){
      //    console.log("test tableUpdate", page*newPerPage)
      //    tableUpdate(userid, grpid, 'load', limit)
      //    console.log("test")
      // }

   };


   //  function getNumberOfPages(rowCount, rowsPerPage) {
   //    return Math.ceil(rowCount / rowsPerPage);
   //  }

   //  function toPages(pages) {
   //    const results = [];

   //    for (let i = 1; i < pages; i++) {
   //       results.push(i);
   //    }

   //    return results;
   //  }

   // const BootyPagination = ({
   //   rowsPerPage,
   //   rowCount,
   //   onChangePage,
   //   onChangeRowsPerPage, // available but not used here
   //   currentPage
   // }) => {
   //    const handleBackButtonClick = () => {
   //       onChangePage(currentPage - 1);
   //    };

   //    const handleNextButtonClick = () => {
   //       onChangePage(currentPage + 1);
   //    };

   //    const handlePageNumber = (e) => {
   //       onChangePage(Number(e.target.value));
   //    };

   //    const pages = getNumberOfPages(rowCount, rowsPerPage);
   //    const pageItems = toPages(pages);
   //    const nextDisabled = currentPage === pageItems.length;
   //    const previosDisabled = currentPage === 1;

   //    return (
   //       <nav>
   //          <ul className="pagination">
   //          <li className="page-item">
   //           <button
   //             className="page-link"
   //             onClick={handleBackButtonClick}
   //             disabled={previosDisabled}
   //             aria-disabled={previosDisabled}
   //             aria-label="previous page"
   //           >
   //             Previous
   //           </button>
   //          </li>
   //          {pageItems.map((page) => {
   //           const className =
   //             page === currentPage ? "page-item active" : "page-item";

   //           return (
   //             <li key={page} className={className}>
   //               <button
   //                 className="page-link"
   //                 onClick={handlePageNumber}
   //                 value={page}
   //               >
   //                 {page}
   //               </button>
   //             </li>
   //           );
   //          })}
   //          <li className="page-item">
   //           <button
   //             className="page-link"
   //             onClick={handleNextButtonClick}
   //             disabled={nextDisabled}
   //             aria-disabled={nextDisabled}
   //             aria-label="next page"
   //           >
   //             Next
   //           </button>
   //          </li>
   //          </ul>
   //       </nav>
   //    );
   // };

   // The list table scrolls horizontally (overflow-x:auto on react-data-table's
   // responsive wrapper) because it is wider than the page. In Chrome a
   // horizontal scroll container swallows the vertical wheel, and react-data-
   // table stops the event from bubbling, so a React onWheel never sees it and
   // the page could not be scrolled while the pointer was over the table. A
   // native capture-phase listener fires before the inner element and forwards
   // a vertical wheel to the page's own scroll container.
   const listTableRef = React.useRef(null);
   useEffect(() => {
      const node = listTableRef.current;
      if (!node) return;
      const onWheel = (e) => {
         if (Math.abs(e.deltaY) <= Math.abs(e.deltaX)) return; // real horizontal scroll
         const scroller = node.closest('section.layout') || document.querySelector('section.layout');
         if (scroller && scroller.scrollHeight > scroller.clientHeight + 1) {
            scroller.scrollTop += e.deltaY;
            e.preventDefault();
         }
      };
      node.addEventListener('wheel', onWheel, { capture: true, passive: false });
      return () => node.removeEventListener('wheel', onWheel, { capture: true });
   }, []);

   return (
      <>
         {/* selectedRowIds.length > 0 ? : null */}
         <ManageTagFullPage type="listtable" managetagopenFunc={managetagopenFunc} resetSelectedRowIds={resetSelectedRowIds} lstresult={lstresult} tabledataUpdate={tabledataUpdate} gridtableUpdate={gridtableUpdate} />
         <div id="listtable" className="table-responsive SR-Listtable" ref={listTableRef}>
            {lstfltrresult.length > 0 ?
               <DataTable
                  // title="Movies"
                  // columns={columns}
                  columns={orderedColumns}
                  data={lstfltrresult}
                  keyField="key"
                  // fixedHeader
                  defaultSortFieldId={"rank"}
                  defaultSortAsc={true}
                  sortIcon={<div className="d-flex"><SortingIcon /></div>}
                  pagination={totalRows > 10}
                  // paginationComponent={BootyPagination}
                  // paginationDefaultPage={1}
                  paginationPerPage={perPage}
                  paginationRowsPerPageOptions={[10, 25, 50, 100]}
                  paginationServer={false}
                  paginationTotalRows={totalRows}
                  onChangeRowsPerPage={handlePerRowsChange}
                  // onChangePage={handlePageChange}
                  selectableRows={canSelectKeywords}
                  selectableRowDisabled={(row) => !row.KW}
                  Clicked
                  // onColumnOrderChange={testrender}
                  // selectableRowsComponent={Checkbox} // Pass the function only
                  // selectableRowsComponentProps={selectProps}
                  // selectableRowsComponent={BootyCheckbox}
                  onSelectedRowsChange={handleRowSelected}
                  // selectableRowsSingle={true}
                  // selectableRowSelected={rowSelectCritera}
                  clearSelectedRows={toggleCleared}
                  selectableRowsHighlight={true}
                  conditionalRowStyles={conditionalRowStyles}

               // subHeader
               // subHeaderComponent={subHeaderComponent}
               />
               :
               <div className="empty_list_table text-center justify-content-center">
                  <div>
                     <DataEmptyIcon />
                     <div className="ls-table-empty">
                        No keywords match
                     </div>
                     <div className="ls-table-empty-body">
                        Nothing in this project matches the current search or column filters.
                     </div>
                  </div>
               </div>
            }
         </div>
      </>
   );
}
