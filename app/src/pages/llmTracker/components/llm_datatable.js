import React, { useEffect, useMemo, useState } from 'react';
import DataTable from 'react-data-table-component';
import { Tsk } from '../../commonComponents/parts';
import { SortingIcon } from '../../commonComponents/icons';
import { Badge } from "@/components/ui/badge";
import '../style.scss';
import { Zoom, Tooltip } from "@mui/material";
import { LLMSecondaryKeywordChipModal } from "../../commonComponents/llm/llm_secondary_keyword_modal";

// Leading affordance on the prompt cell. It is deliberately BEFORE the text:
// the table is wider than a phone, so anything after a 30%-wide truncated
// prompt is off-screen, which is how the row's only "open" control ended up
// behind a horizontal scroll in the first place.
const ChevronRight = () => (
    <svg width="7" height="11" viewBox="0 0 7 11" fill="none" aria-hidden="true">
        <path d="M1.25 1.25 5.5 5.5l-4.25 4.25" stroke="currentColor" strokeWidth="1.8"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

// Mention marks. Monochrome by design contract -- green and red are reserved
// for rank direction, and "not mentioned" is the ordinary state of most rows,
// not an error. Weight carries the signal: a named brand is ink, a silent
// answer is a light rule.
const MentionMark = () => (
    <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
        <path d="M2 6.9 5 9.9 11 3.2" stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

const NoMentionMark = () => (
    <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
        <path d="M3 3.2 10 10M10 3.2 3 10" stroke="currentColor" strokeWidth="1.6"
            strokeLinecap="round" />
    </svg>
);

function LLMDatatable({ ...props }) {
    const [data, setData] = useState([])
    const [toggleCleared, setToggleCleared] = useState(false);
    const [openSecondaryModal, setOpenSecondaryModal] = useState(false);
    const [secondaryKeywords, setSecondaryKeywords] = useState([]);

    useEffect(() => {
        setData(props.data)
    }, [props.data])


    // Model icon mapping function removed since model column is no longer used

    const customStyles = {
        table: {
            style: {
                fontFamily: "SemiBold",
                width: '100%'
            },
        },
        rows: {
            style: {
                fontSize: "14px",
                color: "var(--ink)",
                maxHeight: "50px",
                minHeight: "70px",
                borderBottom: "1px solid var(--line-2) !important",
            },
        },
        cells: {
            style: {
                fontVariantNumeric: "tabular-nums",
                fontSize: "14px",
                lineHeight: "18px",
                color: "var(--ink)",
                fontFamily: "Regular",
                maxHeight: "76px",
                minHeight: "50px",

            },
        },
        headRow: {
            style: {
                minHeight: "40px",
                maxWidth: "100%",
                borderBottom: "1px solid var(--line)",
            },
        },
        headCells: {
            style: {
                backgroundColor: "var(--surface)",
                fontSize: "11px",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
                color: "var(--ink-3)",
                lineHeight: "16px",
                fontFamily: "SemiBold",
                padding: '0px',

            },
        },
        pagination: {
            style: {
                border: "none !important",
                minHeight: "56px !important",
                padding: "0px 8px 5px 8px !important",
                fontSize: "13px !important",
                color: "var(--ink-3) !important",
            },
        }, noData: {
            style: {
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: "var(--accent)",
                backgroundColor: "transparent",
                height: "350px !important",
            },
        },
        progress: {
            style: {
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: "var(--accent)",
                backgroundColor: "transparent",
            },
        },
    }

    // Geo Citations queries four models, each on the account's own key, and the
    // list endpoint returns is_mentioned_in_<key> / ran_<key> for every one.
    const PROVIDERS = [
        { key: "chatgpt", label: "ChatGPT" },
        { key: "claude", label: "Claude" },
        { key: "gemini", label: "Gemini" },
        { key: "perplexity", label: "Perplexity" },
    ];

    const isPending = (row) => ["INIT", "SCHD"].includes(row.track_status);
    const isOpenable = (row) => row.track_status === "DONE";
    // A prompt is only marked FAIL when NO provider succeeded and there was no
    // earlier result to keep (views.py:488-496), so every mention figure on the
    // row is from a run that produced nothing. Showing a cross there reads as
    // "the model answered and did not name you"; it was never asked.
    const isFailed = (row) => row.track_status === "FAIL";

    // Only the providers that actually answered get a column. Rendering all
    // four regardless meant a single-model project carried six columns of "—",
    // which is what pushed the row's own action past the right edge of a
    // 1440px screen -- and past the first column on a phone.
    const providers = useMemo(
        () => PROVIDERS.filter((p) => (data || []).some((row) => row[`ran_${p.key}`] === true)),
        [data]
    );

    // Percentages have to leave room for the 48px selection column; these keep
    // the sum under 100 for every provider count from zero to four.
    const modelW = 10;
    const promptW = Math.max(28, 66 - providers.length * modelW);

    const openRow = (row) => { if (isOpenable(row) && props.onRowOpen) props.onRowOpen(row); };

    const mentionCol = ({ key, label }) => ({
        id: key,
        name: label.toUpperCase(),
        style: { display: "grid", minWidth: `${modelW}%`, justifyContent: "center" },
        sortable: false,
        maxWidth: `${modelW}%`,
        minWidth: `${modelW}%`,
        center: true,
        selector: (row) => row[`is_mentioned_in_${key}`],
        cell: (row) => {
            if (isPending(row)) {
                return <span className="lightTextColour">NA</span>;
            }
            if (isFailed(row)) {
                return <span className="lightTextColour" title="Last run failed — this model returned no result">—</span>;
            }
            if (row[`ran_${key}`] === false) {
                // This model never ran for the prompt (no key connected).
                // A neutral dash, not a mark of failure -- nothing failed, it
                // just wasn't tracked here.
                return <span className="lightTextColour" title="Not tracked — no key for this model">—</span>;
            }
            const mentioned = !!row[`is_mentioned_in_${key}`];
            const analyticsId = row[`${key}_analytics_id`];
            const title = (mentioned ? `${label} named your brand` : `${label} did not name your brand`)
                + (analyticsId ? ` — open ${label}'s answer` : "");
            return (
                <Tooltip classes={{ tooltip: "Tltpsmall text-center pgaudit_MuiTooltip-tooltip" }} placement="top"
                    title={title} TransitionComponent={Zoom}>
                    <button
                        type="button"
                        className="geoModelCell"
                        aria-label={title}
                        disabled={!analyticsId}
                        style={{
                            background: "none",
                            border: 0,
                            padding: "6px",
                            cursor: analyticsId ? "pointer" : "default",
                            color: mentioned ? "var(--ink)" : "var(--ink-4)",
                        }}
                        onClick={(e) => {
                            e.stopPropagation();
                            if (analyticsId && props.onCitationsClick) props.onCitationsClick(row, key);
                        }}
                    >
                        {mentioned ? <MentionMark /> : <NoMentionMark />}
                    </button>
                </Tooltip>
            );
        },
    });

    const columns = useMemo(() => [
        {
            id: 'prompt',
            name: 'PROMPT',
            style: { display: "grid", minWidth: `${promptW}%`, justifyContent: "start" },
            sortable: true,
            // No maxWidth: the prompt absorbs whatever the fixed columns leave,
            // so the table fills its container instead of ending in a stripe of
            // dead space, and the text truncates later on a wide screen.
            grow: 2,
            minWidth: `${promptW}%`,
            selector: row => row.prompt,
            cell: (row) => {
                const openable = isOpenable(row);
                const body = (
                    <div className="geoPromptCell">
                        {openable ? <span className="geoPromptChevron"><ChevronRight /></span> : null}
                        <div className="geoPromptText">
                            <div className="text-truncate maxW85x">
                                {row.prompt ? <span className="fM text-right w60pg">{row.prompt}</span> : <Tsk width={100} />}
                            </div>
                            {/* Phone only: the last-run column is hidden below
                                640px to keep the row inside the viewport, so
                                the date rides along under the prompt instead of
                                disappearing. */}
                            <span className="geoPromptMeta">
                                {isPending(row)
                                    ? (row.track_status === "INIT" ? "Scheduled" : "Processing")
                                    : row.track_status === "FAIL"
                                        ? "Last run failed"
                                        : (row.tracked_at || "")}
                            </span>
                        </div>
                    </div>
                );
                return (
                    <Tooltip classes={{ tooltip: "Tltpsmall text-center pgaudit_MuiTooltip-tooltip" }} placement="top-start"
                        title={row.prompt ? (openable ? row.prompt + " — open this prompt's analysis" : row.prompt) : ""}
                        TransitionComponent={Zoom}>
                        {openable ? (
                            // A real button so the row is reachable by keyboard
                            // too; the row's own click handler covers the mouse.
                            <button
                                type="button"
                                className="geoPromptButton"
                                aria-label={"Open analysis for: " + (row.prompt || "this prompt")}
                                style={{ background: "none", border: 0, padding: 0, textAlign: "left", width: "100%", minWidth: 0, cursor: "pointer", color: "inherit" }}
                                onClick={(e) => { e.stopPropagation(); openRow(row); }}
                            >
                                {body}
                            </button>
                        ) : body}
                    </Tooltip>
                );
            }
        },
        {
            id: 'signal',
            name: 'SIGNAL',
            style: { display: "grid", minWidth: "10%", justifyContent: "center" },
            sortable: false,
            maxWidth: '10%',
            minWidth: '10%',
            center: true,
            selector: row => row.mentioned_count || 0,
            cell: (row) => {
                if (isPending(row)) {
                    return <span className="lightTextColour">NA</span>;
                }
                if (isFailed(row)) {
                    return (
                        <Tooltip classes={{ tooltip: "Tltpsmall text-center pgaudit_MuiTooltip-tooltip" }} placement="top"
                            title={row.track_message || "The last run failed, so there is nothing measured for this prompt."}>
                            <span className="lightTextColour geoRowHit" data-tag="allowRowEvents">—</span>
                        </Tooltip>
                    );
                }
                // Brand-safety-first sentiment colour; grey when not mentioned.
                const s = row.overall_sentiment;
                const mentioned = (row.mentioned_count || 0) > 0;
                const dot = !mentioned ? "var(--ink-3)"
                    : s === "positive" ? "var(--up)"
                    : s === "negative" ? "var(--down)"
                    : "var(--ink-3)";
                // The sentiment is a lexicon score over the whole answer, so the
                // tooltip says that rather than implying it is a reading of how
                // the brand itself was described.
                return (
                    <Tooltip classes={{ tooltip: "Tltpsmall text-center pgaudit_MuiTooltip-tooltip" }} placement="top"
                        title={mentioned
                            ? `Named by ${row.mentioned_count} of ${row.models_ran || 0} models that answered · overall tone of those answers: ${s}`
                            : `Not named by any of the ${row.models_ran || 0} models that answered`}>
                        <div className="d-flex align-items-center justify-content-center gap-1 geoRowHit" data-tag="allowRowEvents">
                            <span style={{ width: 8, height: 8, borderRadius: "50%", background: dot, flex: "0 0 auto" }} />
                            <span className="fM" style={{ fontSize: 12 }}>{row.mentioned_count || 0}/{row.models_ran || 0}</span>
                        </div>
                    </Tooltip>
                );
            }
        },
        ...providers.map(mentionCol),
        {
            // Status and last-run date were two columns saying one thing: a DONE
            // row's status is "it ran, here is when". Merging them drops a whole
            // column's worth of width off a table that did not fit the screen.
            id: 'tracked_at',
            name: 'LAST RUN',
            style: { display: "grid", minWidth: "16%", justifyContent: "center" },
            sortable: true,
            maxWidth: '16%',
            minWidth: '16%',
            center: true,
            selector: row => row.tracked_at || "",
            cell: (row) => {
                if (isPending(row)) {
                    return (
                        <div className="d-flex justify-content-center geoRowHit" data-tag="allowRowEvents">
                            <Badge variant="default">{row.track_status === "INIT" ? "Scheduled" : "Processing"}</Badge>
                        </div>
                    );
                }
                if (row.track_status === "FAIL") {
                    return (
                        <Tooltip classes={{ tooltip: "Tltpsmall text-center pgaudit_MuiTooltip-tooltip" }} placement="top-start"
                            title={row.track_message || "Our engine couldn't process your request. Please try again."}
                            TransitionComponent={Zoom}>
                            <div className="d-flex justify-content-center align-items-center geoRowHit" data-tag="allowRowEvents">
                                {/* --warn, not the shared blue InfoIcon: a failure is a
                                    state to notice, and --accent means "act on this". */}
                                <span className="geoFailChip">Failed</span>
                            </div>
                        </Tooltip>
                    );
                }
                return (
                    <div className="d-flex justify-content-center align-items-center geoRowHit" data-tag="allowRowEvents">
                        <span className="fM text-center">
                            {row.tracked_at ? row.tracked_at : <span className="lightTextColour">NA</span>}
                        </span>
                    </div>
                );
            }
        },

    ], [data, providers])

    // A finished prompt opens from anywhere on its row, not only from a control
    // in the last column of a table that is wider than the screen.
    //
    // react-data-table-component only fires onRowClicked when the click's
    // event.target itself carries data-tag="allowRowEvents", which a custom
    // `cell` renderer's own markup never does. The wrappers below carry the tag
    // and `.geoRowHit` makes their children pointer-transparent, so a click
    // anywhere inside them lands on the tagged element rather than on a span.
    const conditionalRowStyles = [
        { when: (row) => isOpenable(row), classNames: ["geoRowOpenable"] },
    ];

    return (
        <>
            <DataTable
                className='pgaudit_datatable'
                keyField="prompt_id"
                data={data}
                columns={columns}
                pagination={true}
                selectableRows={props.canManage}
                selectableRowsHighlight
                onSelectedRowsChange={props.handleRowSelected}
                clearSelectedRows={toggleCleared}
                paginationPerPage={10}
                paginationRowsPerPageOptions={[10, 50]}
                customStyles={customStyles}
                sortIcon={<SortingIcon />}
                selectableRowsComponentProps={{ name: 'prompt_id' }}
                onRowClicked={openRow}
                conditionalRowStyles={conditionalRowStyles}
                highlightOnHover
            />
            <LLMSecondaryKeywordChipModal open={openSecondaryModal} modalClose={() => setOpenSecondaryModal(false)} secondaryKeywords={secondaryKeywords} />
        </>
    )
}

export default LLMDatatable;
