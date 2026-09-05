import React, { useEffect, useMemo, useState } from 'react';
import DataTable from 'react-data-table-component';
import { RefreshIcon, GoLinkIcon, TagIcon, GoOverviewPageIcon, InfoIcon } from '../../commonComponents/icons';
import { Tsk } from '../../commonComponents/parts';
import { SortingIcon } from '../../commonComponents/icons';
import '../style.scss';
import { Zoom, Tooltip } from "@mui/material";
import { useHistory } from 'react-router-dom';
import { fstLtrCapitalfun } from "../../common_fun";
import { CEditSecondaryKeywordChipModal } from "../cedit_secondary_keyword_modal";

function CEditDatatable({ ...props }) {
    const [data, setData] = useState([])
    const [toggleCleared, setToggleCleared] = useState(false);
    const history = useHistory()
    const [openSecondaryModal, setOpenSecondaryModal] = useState(false);
    const [secondaryKeywords, setSecondaryKeywords] = useState([]);

    useEffect(() => {
        setData(props.data)
    }, [props.data])

    const createContent = (linkId = 1) => {
        history.push("/contentplanner/editor/" + linkId);
    }

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

    const columns = useMemo(() => [
        {
            id: 'primary_keyword',
            name: 'PRIMARY KEYWORD',
            style: { display: "grid", minWidth: "20%", justifyContent: "start" },
            sortable: true,
            maxWidth: '20%',
            minWidth: '20%',
            selector: row => row.primary_keyword,
            cell: (row) => (
                <div className="d-flex overflow-hidden" >
                    <Tooltip classes={{ tooltip: "Tltpsmall text-center pgaudit_MuiTooltip-tooltip" }} placement="top-start" title={row.primary_keyword && row.primary_keyword} TransitionComponent={Zoom}>
                        <div className="text-truncate maxW85x">
                            {row.primary_keyword ? <span className="fM text-right w60pg">{row.primary_keyword}</span> : <Tsk width={100} />}
                        </div>
                    </Tooltip>
                </div>
            )
        },
        {
            id: 'secondary_keyword',
            name: 'SECONDARY KEYWORDS',
            style: { display: "grid", minWidth: "20%", justifyContent: "center" },
            sortable: true,
            maxWidth: '20%',
            minWidth: '20%',
            center: true,
            selector: row => row.secondary_keywords,
            cell: (row) => (
                <div className="d-flex overflow-hidden">
                    <Tooltip classes={{ tooltip: "Tltpsmall text-center pgaudit_MuiTooltip-tooltip" }} placement="top-start" title={row.secondary_keywords.length > 0 ? row.secondary_keywords[0] : []} TransitionComponent={Zoom}>
                        <div className="text-truncate maxW85x">
                            {row.secondary_keywords.length > 0 && <span className="fM text-right w60pg" onClick={() => { setOpenSecondaryModal(true); setSecondaryKeywords(row.secondary_keywords) }}>{row.secondary_keywords.length > 0 ? row.secondary_keywords[0] : []}</span>}
                            {row.secondary_keywords.length > 0 && ("...")}
                        </div>
                    </Tooltip>
                </div>
            )
        },
        {
            id: 'country_name',
            name: 'COUNTRY',
            style: { display: "grid", minWidth: "15%", justifyContent: "center" },
            sortable: true,
            maxWidth: '15%',
            minWidth: '15%',
            center: true,
            selector: row => row.country_name,
            cell: (row) => (
                <div className="d-flex overflow-hidden">
                    {row.country_name}
                </div>
            )
        },

        {
            id: 'score',
            name: 'SCORE',
            style: { display: "grid", minWidth: "10%", justifyContent: "center" },
            sortable: false,
            maxWidth: '10%',
            minWidth: '10%',
            center: true,
            selector: row => row.score,
            cell: (row) => (
                <>
                    {
                        row.score != "0" ?
                            <div className="d-flex overflow-hidden">
                                {row.score}
                                <span className="lightTextColour">
                                    {"/100"}
                                </span>
                            </div> :
                            <div className="d-flex overflow-hidden">
                                <span className="lightTextColour">
                                    {"NA"}
                                </span>
                            </div>
                    }
                </>
            )
        },
        {
            id: 'updated_at',
            name: 'LAST UPDATED AT',
            style: { display: "grid", minWidth: "15%", justifyContent: "center" },
            sortable: false,
            maxWidth: '15%',
            minWidth: '15%',
            center: true,
            selector: row => row.modified_date,
            cell: (row) => (
                <div className="d-flex overflow-hidden">
                    {row.modified_date}
                </div>
            )
        },
        {
            id: 'action',
            name: 'ACTION',
            style: { display: "grid", minWidth: "15%", justifyContent: "center" },
            sortable: true,
            maxWidth: '15%',
            minWidth: '15%',
            center: true,
            selector: row => row.track_status,
            cell: (row) => (
                <>
                    {row.track_status === "FAIL" ? (
                        <Tooltip classes={{ tooltip: "Tltpsmall text-center pgaudit_MuiTooltip-tooltip" }} placement="top-start" title="Content generation failed. Open a new plan and try again." TransitionComponent={Zoom}>
                            <div className="d-flex justify-content-center">
                                <div className="pgaudit_circleArrow">
                                    <InfoIcon />
                                </div>
                            </div>
                        </Tooltip>
                    ) : (
                        <div className="d-flex justify-content-center">
                            <button
                                type="button"
                                className="pgaudit_circleArrow cursorP"
                                aria-label={`Open ${row.primary_keyword} editor`}
                                onClick={() => createContent(row.content_id)}
                            >
                                <GoOverviewPageIcon />
                            </button>
                        </div>
                    )}
                </>
            )
        },

    ], [data])

    return (
        <>
            <DataTable
                className='pgaudit_datatable'
                keyField="content_id"
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
            />
            <CEditSecondaryKeywordChipModal open={openSecondaryModal} modalClose={() => setOpenSecondaryModal(false)} secondaryKeywords={secondaryKeywords} />
        </>
    )
}

export default CEditDatatable;
