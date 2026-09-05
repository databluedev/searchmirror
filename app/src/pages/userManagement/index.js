import { capitalize, IconButton, Tab, Tooltip, Zoom } from "@mui/material";
import React, { createContext, useEffect, useMemo, useState } from "react";
import { Csk, Rsk, TextLg } from "../commonComponents/parts";
import DataTable from "react-data-table-component";
import { DataEmptyIcon, DeleteIcon, EditIcon, SettingsIcon, SortingIcon } from "../commonComponents/icons";
import { CoverModal } from "./fullPageModal";
import { Box } from "@mui/system";
import axios from "axios";
import Cookies from "universal-cookie";
import PageHeader from "./components/pageHeader";
import { TabContext, TabList, TabPanel } from "@mui/lab";
import './style.scss'
import { ClickAwayI } from "../commonComponents/click_away";
// The real implementations, not the "Coming Soon" stubs that were sitting
// in components/. Every TeamContext value they consume is still
// provided below, and every endpoint they call answers.
import TeamManagement from "./teamManagement/teamManagement";
import { toast } from "react-toastify";
import ManageRoles from "./manageRoles/manageRoles";
import SiteMark from "../commonComponents/site_mark";

const style = {
    position: "absolute",
    width: "100%",
    height: "100%",
    bgcolor: "var(--surface)",
    paddingLeft: '60px',
    outline: "none",
    overflow: 'scroll'
};
export const TeamContext = createContext()

function UserManagement(props) {
    var cookies = new Cookies()
    var crntUsr = cookies.get('session_userid')

    let initialState = {
        accMngMdl: false,
        btnLoader: false,
        tmskelete: true,
        teamData: [],
        tmfinder: "",
        delPopUp: false,
        tmdelLoad: false,
        tmmngOpn: false,
        tmmngCl: "",
        tmEdNm: "",
        tmEdOpn: false,
        tmTbleLod: false,
        menuList: [],
        prjLst: []

    }

    let rolesInitialState = {
        addRolOpn: false,
        rolDelOpn: false,
        alRls: [],
        rlskelete: true,
        rlId: '',
        rlDelLod: false,
        rlEdNm: "",
        rlEdDesc: "",
        rlEdPrvlgs: {},
        adRlLod: false,
    }

    const [client, setClient] = useState({
        clOpn: false,
        mngOpn: false,
        reload: false,
        selRows: [],
        // '2' is Team Login. Tab '1' was Client Login and no longer exists;
        // leaving it here made MUI warn that the selected value matched no tab.
        activeTab: '2',
        skelete: true,
        finder: "",
        delLoad: false,
        clEdOpn: false,
        clEdNm: "",
    })
    const [Team, setTeam] = useState(initialState)
    const [roles, setRoles] = useState(rolesInitialState)
    const [filterMenu, setFilterMenu] = useState('crCl')
    const [mngCl, setMngCl] = useState("")
    const [open, setOpen] = useState(false)

    const { clOpn, mngOpn, reload, selRows, activeTab, skelete, finder, delLoad, clEdOpn } = client
    const { menuList, accMngMdl, nm, eml, pass, cnPass, nmErr, emlErr, pssErr, cnPssErr, btnLoader, tmskelete, teamData, tmfinder, delPopUp, tmdelLoad, tmmngOpn, tmmngCl, tmEdOpn, tmEdNm, tmTbleLod } = Team
    const { addRolOpn, rolDelOpn, alRls, rlskelete, rlId, rlDelLod, rlEdNm, rlEdDesc, rlEdPrvlgs, adRlLod } = roles


    const handleTmInitialize = async () => {
        const cookies = new Cookies()
        const config = {
            headers: {
                'Authorization': 'Token ' + cookies.get('session_token'),
            }
        };
        await axios.post(global.apiurl + '/get_team', { 'userid': cookies.get('session_userid') }, config).then(r => {
            return r.data
        }).then(res => {
            // console.log(res)
            if (res.st === 1) {
                setTeam(r => ({ ...r, teamData: res.dt, tmskelete: false }))
            } else {
                setTeam(r => ({ ...r, tmskelete: false }))
            }
        }).catch(err => {
            // console.log(err)
            setTeam(r => ({ ...r, tmskelete: false }))
        })
    }

    const handleRolesInitializer = async () => {
        const cookies = new Cookies()
        await axios({
            method: 'GET',
            url: global.apiurl + '/my_view/',
            params: { 'userid': cookies.get('session_userid') },
            headers: { 'Authorization': 'Token ' + cookies.get('session_token') }
        }).then(response => {
            return response.data
        }).then(res => {
            if (res.st === 1) {
                setRoles(r => ({ ...r, alRls: res.dt, rlskelete: false }))
                setTeam(r => ({ ...r, menuList: res.dt }))
            }
        }).catch(err => {
            // console.log(err)
        })
    }



    useEffect(() => {
        const initialize = async () => {
            await Promise.all([handleTmInitialize(), handleRolesInitializer()])
        }
        initialize()
    }, [])

    const columns = useMemo(() => [
        {
            id: 'clname',
            name: <div>{'CLIENT NAME'}</div>,
            center: false,
            maxWidth: "20%",
            sortable: true,
            selector: (row) => row.nm,
            cell: (row, index, column, id) => (
                skelete ?
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
            name: <div>{'CLIENT E-MAIL'}</div>,
            center: false,
            maxWidth: "25%",
            sortable: true,
            selector: (row) => row.clml,
            cell: (row, index, column, id) => (
                skelete ?
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
            id: 'prjcts',
            name: <div>{'PROJECTS'}</div>,
            maxWidth: "40%",
            center: true,
            selector: (row) => row.prjcts,
            cell: (row, index, column, id) => (
                skelete ?
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
                                prjLst.map((pr_item, index) => {
                                    if (pr_item.GY === item) {
                                        return (
                                            <div key={index}>
                                                <div className="border m-r5 p-1 rounded-circle bg-white">
                                                    <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={pr_item.NM} TransitionComponent={Zoom}>
                                                        <SiteMark domain={pr_item.DN} width={26} height={26} className="m-0 rounded" />
                                                    </Tooltip>
                                                </div>
                                            </div>
                                        )
                                    }
                                })
                            )) :
                            <div>
                                {/*<div style={{ color: "#d7d7d9" }} className=" m-r5 p-1 rounded-circle bg-white text-center">
                                    <div className="p-b5">
                                        <DataEmptyIcon height={26} width={26} />
                                    </div>
                                    <SmallText class="m-0 f10x">
                                        <span style={{ color: '#d7d7d9' }}>
                                            No projects were assigned
                                        </span>
                                    </SmallText>
                                </div>*/}
                                <span style={{ color: '#d7d7d9' }}>
                                    -
                                </span>
                            </div>
                        }
                        {row.prjcts.length > 6 ?
                            <>
                                <div className="border rounded-circle" style={{ left: '30px', backgroundColor: 'rgb(137 89 207)' }}>
                                    <ClickAwayI row={row}>
                                        {row.prjcts.slice(6).map(item => (
                                            prjLst.map((pr_item, index) => {
                                                if (pr_item.GY === item) {
                                                    return (
                                                        <div key={index} className="cursorP d-flex align-items-center text-truncate p-2 rounded-circle" style={{ color: "var(--ink)" }}>
                                                            <SiteMark domain={pr_item.DN} className="rounded-circle" width={26} height={26} />
                                                            <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top-start" title={pr_item.NM} TransitionComponent={Zoom}>
                                                                <span className="p-l5">{pr_item.NM}</span>
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
                skelete ?
                    <div className="d-flex gap-1">
                        <Rsk className="" width={30} height={30} />
                        <Rsk className="" width={30} height={30} />
                        <Rsk className="" width={30} height={30} />
                    </div>
                    :
                    <div className="p-2 d-flex align-items-center justify-content-between gap-2">
                        <IconButton className="actionIcon" onClick={e => handleManage(row.clml)}><SettingsIcon height={17} width={17} /></IconButton>
                        <IconButton className="actionIcon" onClick={e => { setMngCl(row.clml); setClient(r => ({ ...r, clEdOpn: true, clEdNm: row.nm })) }} ><EditIcon /></IconButton>
                        <IconButton className="actionIcon" onClick={e => { setOpen(true); setClient(r => ({ ...r, finder: row.clml })) }}><DeleteIcon height={14} width={14} /></IconButton>
                    </div>
            )
        }
    ], [skelete])

    const handleManage = (client) => {
        setClient(prev => ({ ...prev, mngOpn: true }))
        setMngCl(client)
    }

    const handleMngClose = () => {
        setClient(prev => ({ ...prev, mngOpn: false }))
    }

    const handleTabChange = (event, newValue) => {
        setClient(accountData => ({ ...accountData, activeTab: newValue, }))
    };

    // `embedded` renders the Team and Roles panels without this page's own
    // shell, so the consolidated Settings page can host them as one of its tabs
    // rather than sending the operator off to a second settings page.
    const Shell = props.embedded
        ? ({ children }) => <>{children}</>
        : ({ children }) => <section className="layout">{children}</section>;

    return (
        <>
            <Shell>
                <TeamContext.Provider value={{ menuList, accMngMdl, nm, eml, pass, cnPass, nmErr, emlErr, pssErr, cnPssErr, btnLoader, tmskelete, teamData, tmfinder, delPopUp, tmdelLoad, tmmngOpn, tmmngCl, tmEdOpn, setTeam, handleTmInitialize, tmEdNm, tmTbleLod, setClient, addRolOpn, setRoles, rolDelOpn, alRls, rlskelete, rlId, rlDelLod, handleRolesInitializer, rlEdNm, rlEdDesc, rlEdPrvlgs, adRlLod }}>
                    {props.embedded ? null : (
                        <PageHeader projectList={props.projectList} title={'User Management'} />
                    )}
                    <div className="keywordDetail prjtsettingstab">
                        <Box sx={{ width: '100%', typography: 'body1' }}>
                            <TabContext value={activeTab}>
                                <div className="tabStrip">
                                    <TabList
                                        onChange={handleTabChange}
                                        variant={'scrollable'}
                                        scrollButtons={false}
                                        aria-label="scrollable prevent tabs example"
                                    >
                                        <Tab label="Team Login" value="2" />
                                        <Tab label="Roles" value="4" />
                                    </TabList>
                                </div>
                                <TabPanel value="2">
                                    <div>
                                        {/* <TeamContext.Provider value={{ menuList, accMngMdl, nm, eml, pass, cnPass, nmErr, emlErr, pssErr, cnPssErr, btnLoader, tmskelete, teamData, tmfinder, delPopUp, tmdelLoad, tmmngOpn, tmmngCl, tmEdOpn, setTeam, handleTmInitialize, tmEdNm, tmTbleLod, setClient }}> */}
                                            <TeamManagement projectList={props.projectList} />
                                        {/* </TeamContext.Provider> */}
                                    </div>
                                </TabPanel>
                                <TabPanel value="4">
                                    <div>
                                        {/* <TeamContext.Provider value={{ addRolOpn, setRoles, rolDelOpn, alRls, rlskelete, rlId, rlDelLod, handleRolesInitializer, rlEdNm, rlEdDesc, rlEdPrvlgs, adRlLod, teamData }}> */}
                                            <ManageRoles />
                                        {/* </TeamContext.Provider> */}
                                    </div>
                                </TabPanel>
                            </TabContext>
                        </Box>
                    </div>
                </TeamContext.Provider>
            </Shell>
        </>
    )
}
export default UserManagement
