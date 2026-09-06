import React, { useState } from "react";
import { ParaLg, SmallText } from "../../commonComponents/parts";
import Skeleton from '@mui/material/Skeleton';

import ClickAway from "../../commonComponents/click_away";
import { SelectDownArrow } from "../../commonComponents/icons";

import MenuItem from '@mui/material/MenuItem';

import useSkeletonRows from "../../commonComponents/skeleton_rows";

import EcomWidgetTable from "../ecomTable/ecom_widget_table";
import { ConfirmDialog, ModalBox } from "../../commonComponents/Modals";

import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from "react-toastify";
import ElementMaker from "./element_maker";

function EcomWidget({ children, ...props }) {
    const SkeletonColor = "var(--surface-2)"

    const [dataRows] = useState(useSkeletonRows());
    const [confirmDelete, setConfirmDelete] = useState(false);
    const [deleting, setDeleting] = useState(false);

    var duration = props.report ? props.report.hasOwnProperty('bt_date') ? (props.report)['bt_date'] : null : null
    var sheetNumber = props.report ? props.report['sheet_id'] : ''
    var reportName = props.report ? Object.keys(props.report)[0] : ''
    var reportRows = props.report && Array.isArray(props.report[reportName]) ? props.report[reportName] : []

    /* Every report rendered fully expanded, so a project with several of them
       was one long scroll and no two report names were ever on screen at the
       same time.

       Default is the first report open and the rest closed. All-open is the
       scroll that was reported; all-closed hides the data the page exists to
       show and leaves the reader guessing which card to open. First-open puts
       a real table in front of them straight away and costs one line per
       further report.

       An explicit collapse or expand is remembered per report, so the choice
       survives leaving the page. The default only decides for a report the
       reader has never touched. The card is keyed by sheet_id upstream
       (report_widget.js), so this state is created fresh for the real report
       when it replaces the placeholder. */
    const panelId = "report-panel-" + (sheetNumber || "loading-" + props.index)
    const collapseKey = sheetNumber ? "sm.report.collapsed." + sheetNumber : null

    const [collapsed, setCollapsed] = useState(() => {
        if (collapseKey) {
            try {
                const stored = window.localStorage.getItem(collapseKey)
                if (stored !== null) {
                    return stored === "1"
                }
            } catch (e) {
                // Storage blocked (private window, site data off). Not a
                // failure -- the default below is still correct.
            }
        }
        return props.index > 0
    })

    const toggleCollapsed = () => {
        const next = !collapsed
        setCollapsed(next)
        if (collapseKey) {
            try {
                window.localStorage.setItem(collapseKey, next ? "1" : "0")
            } catch (e) {
                // The card still collapses; only the memory of it is lost.
            }
        }
    }

    /// COMMENT
    const customStyles = {
        table: {
            style: {
                backgroundColor: "var(--surface)",
                fontFamily: "SemiBold",
            },
        },
        rows: {
            style: {
                backgroundColor: "var(--surface)",
                fontSize: "14px",
                color: "var(--ink)",
                maxHeight: "45px",
                minHeight: "45px",
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
                maxHeight: "45px",
                minHeight: "45px",

            },
        },
        headRow: {
            style: {
                minHeight: "45px",
                borderBottom: "1px solid var(--line)",
            },
        },
        headCells: {
            style: {
                backgroundColor: "var(--surface-2)",
                fontSize: "11px",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
                color: "var(--ink-3)",
                lineHeight: "16px",
                fontFamily: "SemiBold",
                padding: "0px 5px 0px 5px !important",
            },
        },
        pagination: {
            style: {
                backgroundColor: "var(--surface)",
                border: "none !important",
                minHeight: "60px !important",
                padding: "0px 5px !important",
                fontSize: "12px !important",
                color: "var(--ink-3) !important",
            },
        },
        noData: {
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

    // Delete used to fire on the first click of a menu item, with no
    // confirmation, and swallowed both the server's refusal and the network
    // error -- the menu closed and the report was still there, unexplained.
    const handleRprtDelete = async () => {
        if (deleting) return
        setDeleting(true)

        const cookies = new Cookies();
        const usertoken = cookies.get('session_token');
        const userid = cookies.get('session_userid');
        const grpid = cookies.get('activegrp');
        if (!grpid) { return; }   // no project: nothing to ask about

        const data = { 'userid': userid, 'grpid': grpid, 'report_name': reportName, 'sheet_number': sheetNumber }
        await axios.post(global.apiurl + '/rpt_dlte', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data
        }).then(res => {
            if (res.st) {
                toast.success(res.dt || "Report deleted.")
                setConfirmDelete(false)
                props.handleInitialise(props.projectList)
            } else {
                toast.error(res.dt || "The report could not be deleted.")
            }
        }).catch(error => {
            const status = error && error.response && error.response.status
            toast.error(status === 403
                ? "You do not have permission to delete reports."
                : "The report could not be deleted. Please try again.")
        })
        setDeleting(false)
    }
    return (
        <>
            <section className={collapsed ? "projectTableCard isCollapsed" : "projectTableCard"}>
                <div className="projectTableHeader">
                    <div className="d-flex justify-content-between align-items-center m-0 p-b5">
                        {/* The name is itself a control (ElementMaker renames in
                            place), so the chevron is its own button beside it --
                            a button cannot contain a button, and making the whole
                            header the toggle would swallow the rename click. */}
                        <div className="reportCardTitle">
                            <button
                                type="button"
                                className="reportCollapseToggle"
                                aria-expanded={!collapsed}
                                aria-controls={panelId}
                                aria-label={(collapsed ? "Expand " : "Collapse ") + reportName}
                                onClick={toggleCollapsed}
                            >
                                <SelectDownArrow />
                            </button>
                            {props.loading ?
                                <ParaLg class="fB mb-0 wd-colTitleRow ">
                                    <>

                                        {props.canRename
                                            ? <ElementMaker value={reportName} sheetNumber={sheetNumber} />
                                            : <span>{reportName}</span>}
                                        {/* bt_date is only set on GA overview sheets, so every
                                            ranking report rendered an empty span here. */}
                                        {duration ? <SmallText class="fM reportCardWindow">{duration}</SmallText> : null}
                                    </>
                                </ParaLg>
                                :
                                <Skeleton variant="rectangular" width={250} height={23} sx={{ bgcolor: SkeletonColor }} />
                            }
                        </div>
                        <div className="reportCardActions">
                            {/* Closed, the card is one line. It still has to say
                                what is behind it, or collapsing turns the page
                                into a list of names with no sense of size. */}
                            {collapsed && props.loading ?
                                <span className="reportCardRowCount">
                                    {reportRows.length} {reportRows.length === 1 ? "row" : "rows"}
                                </span>
                                : null}
                            {sheetNumber && props.canDelete ?
                                <ClickAway label={"Actions for " + reportName}>
                                    <MenuItem className="primaryHover" onClick={() => setConfirmDelete(true)}>Delete report</MenuItem>
                                </ClickAway>
                                :
                                null
                            }
                        </div>
                    </div>
                </div>

                {/* hidden, not unmounted: the table keeps its sort column and
                    page while the card is closed, and the id aria-controls
                    points at stays in the document. */}
                <div id={panelId} className="reportCardBody" hidden={collapsed}>
                {(Object.values(props.report)).length > 0 ?
                    <EcomWidgetTable sheet_type={props.report.hasOwnProperty('sheet_type') && props.report['sheet_type']} metrics={props.report.hasOwnProperty('metrics') && props.report['metrics']} colcnt={props.report.hasOwnProperty('change_units') && props.report['change_units']} reportData={Object.values(props.report)} index={props.index} loading={props.loading} useRows={dataRows} customStyles={customStyles} />
                    :
                    // "No Pages Found" named a Search Console concept on a
                    // keyword-ranking report and told the reader nothing about
                    // what to do next.
                    <div className="d-flex justify-content-center align-items-center text-center reportEmptyRows">
                        <div>
                            <div className="ls-table-empty">No rows</div>
                            <p className="ls-table-empty-body">
                                This report has no rows yet. Its next scheduled run will fill it in.
                            </p>
                        </div>
                    </div>
                }
                </div>
            </section>

            {/* The shared ModalBox defaults to the dark panel, which renders the
                confirm as unshelled text on black -- the destructive action was
                the least button-looking thing in the dialog. */}
            <ModalBox className="light reportDeleteConfirm" title="Delete report" open={confirmDelete} handleClose={() => setConfirmDelete(false)} onClose={() => setConfirmDelete(false)}>
                <ConfirmDialog
                    cancelTitle="Keep it"
                    confirmTitle={deleting ? "Deleting..." : "Delete report"}
                    modalCancel={() => setConfirmDelete(false)}
                    modalConfirm={handleRprtDelete}
                    content={'"' + reportName + '" and every row it has collected will be removed. This cannot be undone.'}
                />
            </ModalBox>
        </>
    )
}

export default React.memo(EcomWidget);
