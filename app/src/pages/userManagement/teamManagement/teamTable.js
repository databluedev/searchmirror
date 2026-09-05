import DataTable from "react-data-table-component";
import { DataEmptyIcon, DeleteIcon, EditIcon, SettingsIcon, SortingIcon } from "../../commonComponents/icons";
import { useContext, useMemo } from "react";
import { Csk, Rsk } from "../../commonComponents/parts";
import { capitalize, IconButton, Tooltip, Zoom } from "@mui/material";
import { ClickAwayI } from "../../commonComponents/click_away";
// import { TeamContext } from "./teamManagement";
import { TeamContext } from "..";
import SiteMark from "../../commonComponents/site_mark";

function TeamTable(props) {
    let { tmskelete, teamData, setTeam, tmTbleLod } = useContext(TeamContext)
    // console.log(tmskelete, teamData)
    const columns = useMemo(() => [
        {
            id: 'clname',
            name: <div>{'NAME'}</div>,
            center: false,
            maxWidth: "15%",
            sortable: true,
            selector: (row) => row.nm,
            cell: (row, index, column, id) => (
                tmskelete ?
                    <Csk width={160} />
                    :
                    <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={row.nm} TransitionComponent={Zoom}>
                        <div className="f-14x">
                            {capitalize(row.nm)}
                        </div>
                    </Tooltip>
            )
        },
        {
            id: 'clmail',
            name: <div>{'E-MAIL'}</div>,
            center: false,
            maxWidth: "25%",
            sortable: true,
            selector: (row) => row.clml,
            cell: (row, index, column, id) => (
                tmskelete ?
                    <Csk width={300} />
                    :
                    <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={row.clml} TransitionComponent={Zoom}>
                        <div className="f-14x">
                            {row.clml}
                        </div>
                    </Tooltip>
            )
        },
        {
            id: 'clrole',
            name: <div>{'ROLE'}</div>,
            center: false,
            maxWidth: "15%",
            sortable: true,
            selector: (row) => row.rl,
            cell: (row, index, column, id) => (
                tmskelete ?
                    <Csk width={300} />
                    :
                    <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={row.rl} TransitionComponent={Zoom}>
                        <div className="f-14x">
                            {row.rl}
                        </div>
                    </Tooltip>
            )
        },
        {
            id: 'prjcts',
            name: <div>{'PROJECTS'}</div>,
            maxWidth: "30%",
            center: true,
            selector: (row) => row.prjcts,
            cell: (row, index, column, id) => (
                tmskelete ?
                    <div className="d-flex gap-1">
                        <Rsk className="rounded-circle" width={30} height={30} />
                        <Rsk className="rounded-circle" width={30} height={30} />
                        <Rsk className="rounded-circle" width={30} height={30} />
                        <Rsk className="rounded-circle" width={30} height={30} />
                    </div>
                    :
                    <div className="d-flex">
                        {row.prjcts.length !== 0 ?
                            row.prjcts.slice(0, 6).map(item => (
                                props.projectList.map((pr_item, index) => {
                                    if (pr_item.GY === item) {
                                        return (
                                            <div key={index}>
                                                <div className="border m-r5 p-1 rounded-circle bg-white">
                                                    <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={pr_item.NM} TransitionComponent={Zoom}>
                                                        <span className="d-flex"><SiteMark domain={pr_item.DN} width={26} height={26} className="m-0 rounded" /></span>
                                                    </Tooltip>
                                                </div>
                                            </div>
                                        )
                                    }
                                })
                            )) :
                            <div>
                                {/* <div style={{ color: "#d7d7d9" }} className=" m-r5 p-1 rounded-circle bg-white text-center">
                                    <div className="p-b5">
                                        <DataEmptyIcon height={26} width={26} />
                                    </div>
                                    <SmallText class="m-0 f10x">
                                        <span style={{ color: '#d7d7d9' }}>
                                            No projects were assigned
                                        </span>
                                    </SmallText>
                                </div>*/}
                                <span style={{ color: "#d7d7d9" }}>
                                    -
                                </span>
                            </div>
                        }
                        {row.prjcts.length > 6 ?
                            <>
                                <div className="border rounded-circle" style={{ left: '30px', backgroundColor: 'rgb(137 89 207)' }}>
                                    <ClickAwayI row={row}>
                                        {row.prjcts.slice(6).map(item => (
                                            props.projectList.map((pr_item, index) => {
                                                if (pr_item.GY === item) {
                                                    return (
                                                        <div key={index} className="cursorP d-flex align-items-center text-truncate p-2 rounded-circle" style={{ color: "var(--ink)" }}>
                                                            <SiteMark domain={pr_item.DN} className="rounded-circle" width={26} height={26} />
                                                            <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={pr_item.NM} TransitionComponent={Zoom}>
                                                                <span className="p-l5 d-inline-block">{pr_item.NM}</span>
                                                            </Tooltip>
                                                        </div>
                                                    )
                                                }
                                            })
                                        ))}
                                    </ClickAwayI>
                                </div>
                            </>
                            :
                            null
                        }
                    </div>
            )
        }, {
            id: 'manage',
            name: <div>{'ACTIONS'}</div>,
            center: true,
            maxWidth: '15%',
            cell: (row, index, column, id) => (
                tmskelete ?
                    <div className="d-flex gap-1">
                        <Rsk className="" width={30} height={30} />
                        <Rsk className="" width={30} height={30} />
                        <Rsk className="" width={30} height={30} />
                    </div>
                    :
                    <div className="p-2 d-flex align-items-center justify-content-between gap-2">
                        <IconButton aria-label={`Manage projects for ${row.nm}`} title="Manage projects" className="actionIcon" onClick={e => { setTeam(prev => ({ ...prev, tmmngOpn: true, tmmngCl: row.clml })) }}><SettingsIcon height={17} width={17} /></IconButton>
                        <IconButton aria-label={`Edit ${row.nm}`} title="Edit member" className="actionIcon" onClick={e => { setTeam(prev => ({ ...prev, tmEdOpn: true, tmEdNm: row.nm, tmmngCl: row.clml })) }}><EditIcon /></IconButton>
                        <IconButton aria-label={`Delete ${row.nm}`} title="Delete member" className="actionIcon" onClick={e => { setTeam(r => ({ ...r, tmfinder: row.clml, delPopUp: true })) }}><DeleteIcon height={14} width={14} /></IconButton>
                    </div>
            )
        }
    ], [tmskelete])
    return (
        <>
            <div className="position-relative">
                {teamData.length > 0 ?
                    <>
                        <div id="listtable" className="table-responsive SR-Listtable">
                        <DataTable
                            className={tmTbleLod ? "clientTable modDesctd" : "clientTable"}
                            fullWidth
                            sortIcon={<div className="d-flex"><SortingIcon /></div>}
                            data={teamData}
                            columns={columns}
                            // selectableRows
                            pagination={teamData.length > 10 ? true : false}
                            paginationPerPage={10}
                            paginationRowsPerPageOptions={[10, 50]}
                            paginationTotalRows={teamData.length}
                        // selectableRowDisabled={row => !row.isSelectorDisabled}
                        // onSelectedRowsChange={handleRowSelected}
                        />
                        </div>
                    </>
                    :
                    <div className="empty_list_table d-flex align-items-center text-center justify-content-center">
                        <div>
                            <DataEmptyIcon />
                            <div className="ls-table-empty">Team</div>
                            <p className="ls-table-empty-body">No team member has been added to this account yet.</p>
                        </div>
                    </div>
                }
            </div>
        </>
    )
}

export default TeamTable
