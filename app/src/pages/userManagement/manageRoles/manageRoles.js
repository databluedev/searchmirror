import React, { useContext, useMemo } from "react";
import { AppButton, Csk, ParaLg, Tsk } from "../../commonComponents/parts";
import { capitalize, IconButton, Tooltip, Zoom } from "@mui/material";
import DataTable from "react-data-table-component";
import { DataEmptyIcon, DeleteIcon, SettingsIcon, SortingIcon } from "../../commonComponents/icons";
import { CoverModal } from "../fullPageModal";
import AddRoles from "./rolesPr";
import { TeamContext } from "..";
import { ConfirmDeleteModal } from "../components/parts";
import axios from "axios";
import Cookies from "universal-cookie";
import { toast } from "react-toastify";

const dummyRoles = [
    { 'id': 'rlname', 'rlnm': 'Chief' },
    { 'id': 'rlname', 'rlnm': 'Manager' },
    { 'id': 'rlname', 'rlnm': 'Lead' },
    { 'id': 'rlname', 'rlnm': 'Analyst' },
]
const style = {
    position: "absolute",
    width: "100%",
    height: "100%",
    bgcolor: "var(--surface)",
    paddingLeft: '60px',
    outline: "none",
    overflow: 'scroll'
};

function ManageRoles() {
    const { addRolOpn, rolDelOpn, setRoles, alRls, rlskelete, rlId, rlDelLod, handleRolesInitializer, teamData } = useContext(TeamContext)

    const handleSelectRoleDelete = (isOpn, rl_id) => {

        let existTeam = teamData.filter(item => item.rl_id === rl_id)

        if (existTeam.length === 0) {
            setRoles(r => ({ ...r, rolDelOpn: isOpn, rlId: rl_id }))
        } else {
            toast.warn(`${existTeam.length} members has been assigned to this role.`)
        }
    }

    const handleRoleDelete = () => {
        setRoles(r => ({ ...r, rlDelLod: true }))
        const cookies = new Cookies()
        axios.post(global.apiurl + '/rl_delete', { 'userid': cookies.get('session_userid'), 'rl_id': rlId }, {
            headers: { 'Authorization': 'Token ' + cookies.get('session_token'), 'Content-Type': 'application/json' }
        }).then(response => {
            return response.data
        }).then(res => {
            if (res.st === 1) {
                toast.success(res.dt)
                setRoles(r => ({ ...r, rlDelLod: false, rolDelOpn: false }))
                handleRolesInitializer()
            } else if (res.st === 0) {
                toast.error(res.dt)
                setRoles(r => ({ ...r, rlDelLod: false, rolDelOpn: false }))
            } else {
                // console.log(res.dt)
                setRoles(r => ({ ...r, rlDelLod: false, rolDelOpn: false }))
            }
        }).catch(err => {
            // console.log(err)
            setRoles(r => ({ ...r, rlDelLod: false, rolDelOpn: false }))
        })
    }
    const rolesColumn = useMemo(() => [
        {
            id: 'id',
            name: <div>{'#'}</div>,
            maxWidth: '10%',
            cell: (row, index) => (
                <div>
                    {index + 1}
                </div>
            )
        },
        {
            id: 'rlname',
            name: <div>{'ROLE NAME'}</div>,
            center: false,
            maxWidth: "90%",
            sortable: true,
            selector: (row) => row.rl,
            cell: (row, index, column, id) => (
                rlskelete ?
                    <Csk width={160} />
                    :
                    <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={row.rl} TransitionComponent={Zoom}>
                        <div className="f-14x">
                            {capitalize(row.rl)}
                        </div>
                    </Tooltip>
            )
        },
        {
            id: 'actions',
            name: <div>{'ACTIONS'}</div>,
            maxWidth: "10%",
            // sortable: true,
            center: true,
            selector: (row) => row.rl,
            cell: (row, index, column, id) => (
                rlskelete ?
                    // <Csk width={160} />
                    <div className="d-flex gap-1">
                        <Tsk width={30} height={30} />
                        <Tsk width={30} height={30} />
                    </div>
                    :
                    <div className="p-2 d-flex align-items-center justify-content-between gap-2">
                        <IconButton aria-label={`Edit ${row.rl} role`} title="Edit role" className="actionIcon" onClick={e => setRoles(r => ({ ...r, addRolOpn: true, rlId: row.rl_id, rlEdNm: row.rl, rlEdDesc: row.desc, rlEdPrvlgs: row.mdles }))}><SettingsIcon height={17} width={17} /></IconButton>
                        <IconButton aria-label={`Delete ${row.rl} role`} title="Delete role" className="actionIcon" onClick={e => handleSelectRoleDelete(true, row.rl_id)}><DeleteIcon height={14} width={14} /></IconButton>
                    </div>
            )
        },
    ])
    return (
        <>
            <section className="drp-form p-b20">
                <div className="p-t10">
                    <div>
                        <div className="d-flex align-items-center justify-content-between py-3">
                            <div>
                                <ParaLg class="fB">All Roles</ParaLg>
                            </div>
                            {/*<div>
                                 <TextField type="search" className="search"/> */}
                            {/* <Input class="search"/> 
                                <ClientTableSearch />
                            </div>*/}
                            <div className="maxW200x">
                                {/* <AppButton noIcon={'d-none'} value="Add Roles" onclick={e=>setRoles(r=>({...r, addRolOpn:true}))} /> */}
                                <AppButton noIcon={'d-none'} class="" value="Add New Role" onclick={e => setRoles(r => ({ ...r, addRolOpn: true, rlId: '', rlEdNm: "", rlEdDesc: "", rlEdPrvlgs: { 'Prjcts': [], 'Widgets': [], 'Keyword': [] } }))} />
                            </div>
                        </div>
                        <div>
                            {alRls.length > 0 ?
                                <div id="listtable" className="table-responsive SR-Listtable">
                                <DataTable
                                    fullWidth
                                    className="clientTable"
                                    columns={rolesColumn}
                                    sortIcon={<div className="d-flex"><SortingIcon /></div>}
                                    data={alRls}
                                    pagination={alRls.length > 10 ? true : false}
                                    paginationPerPage={10}
                                    paginationRowsPerPageOptions={[10, 50]}
                                    paginationTotalRows={alRls.length}
                                />
                                </div>
                                :
                                <div className="empty_list_table d-flex align-items-center text-center justify-content-center">
                                    <div>
                                        <DataEmptyIcon />
                                        <div className="ls-table-empty">Roles</div>
                                        <p className="ls-table-empty-body">No role has been defined on this account yet.</p>
                                    </div>
                                </div>
                            }
                        </div>
                    </div>
                </div>
            </section>
            <ConfirmDeleteModal delLoad={rlDelLod} onSubmit={handleRoleDelete} mnhdr="Delete role?" subhdr="This role will be permanently removed." modalClose={e => setRoles(r => ({ ...r, rolDelOpn: false }))} open={rolDelOpn} />
            <CoverModal handleClose={e => setRoles(r => ({ ...r, addRolOpn: false, rlEdNm: "" }))} open={addRolOpn} mnhdr="Roles & Privileges" subhdr="Choose the product areas and actions this role can use.">
                <AddRoles />
            </CoverModal>
        </>
    )
}
export default ManageRoles
