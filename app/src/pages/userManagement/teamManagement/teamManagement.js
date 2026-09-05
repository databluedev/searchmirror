import React, { useContext, useRef, useState } from "react";
import { AppButton, CustomSelect, RefInput, TextLg } from "../../commonComponents/parts";
import { Grid, TextField } from "@mui/material";
import { CoverModal } from "../fullPageModal";
import AccessManagement from "./accessManagement";
import { toast } from "react-toastify";
import TeamTable from "./teamTable";
import { ConfirmDeleteModal } from "../components/parts";
import Cookies from "universal-cookie";
import axios from "axios";
import ManageTeam from "./manageTeam";
import { TeamContext } from "..";
import TeamAccountManage from "./teamAccountManagement";

const style = {
    position: "absolute",
    width: "100%",
    height: "100%",
    bgcolor: "var(--surface)",
    paddingLeft: '60px',
    outline: "none",
    overflow: 'scroll'
};



const emailRegex = /^(([^<>()[\]\\.,;:\s@\]"]+(\.[^<>()[\]\\.,;:\s@\]"]+)*)|(\]".+\]"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;

function TeamManagement(props) {
    let initialState = {
        nm: "",
        eml: "",
        pass: "",
        cnPass: "",
        nmErr: "",
        emlErr: "",
        pssErr: "",
        cnPssErr: "",
        role: "",
        rlId: "",
    }

    const [teamForm, setTeamForm] = useState(initialState)

    const nameRef = useRef(null)
    const emailRef = useRef(null)
    const passRef = useRef(null)
    const cnPassRef = useRef(null)
    const { nm, eml, pass, cnPass, nmErr, emlErr, pssErr, cnPssErr, role, rlId } = teamForm
    const { menuList, accMngMdl, btnLoader, tmskelete, teamData, tmfinder, delPopUp, tmdelLoad, tmmngOpn, tmmngCl, setTeam, handleTmInitialize, tmEdOpn, tmEdNm, setClient } = useContext(TeamContext)

    const handleAccessOpen = () => {
        setTeam(prev => ({ ...prev, accMngMdl: true }))
    }
    const handleAccessClose = () => {
        setTeam(prev => ({ ...prev, accMngMdl: false }))
    }

    const handleClientSubmit = async () => {
        if (!nameRef.current.value) {
            setTeamForm(r => ({ ...r, nmErr: "Enter name", emlErr: '', pssErr: '', cnPssErr: '' }))
            return false
        } else if (nameRef.current.value.length < 3) {
            setTeamForm(r => ({ ...r, nmErr: "Name Should contain at least 3 characters at your name.", emlErr: '', pssErr: '', cnPssErr: '' }))
            return false
        } else if (!emailRef.current.value) {
            setTeamForm(r => ({ ...r, emlErr: "Enter Email", nmErr: '', pssErr: '', cnPssErr: '' }))
            return false
        } else if (!emailRegex.test(emailRef.current.value)) {
            setTeamForm(r => ({ ...r, emlErr: "Enter Valid Email", nmErr: '', pssErr: '', cnPssErr: '' }))
            return false
        } else if (!passRef.current.value) {
            setTeamForm(r => ({ ...r, pssErr: "Enter Password", emlErr: '', nmErr: '', cnPssErr: '' }))
            return false
        } else if (passRef.current.value.length < 8) {
            setTeamForm(r => ({ ...r, pssErr: "Password should contain at least 8 characters.", emlErr: '', nmErr: '', cnPssErr: '' }))
            return false
        } else if (!cnPassRef.current.value) {
            setTeamForm(r => ({ ...r, cnPssErr: "Enter Confirm Password.", emlErr: '', nmErr: '', pssErr: '' }))
            return false
        } else if (cnPassRef.current.value !== passRef.current.value) {
            setTeamForm(r => ({ ...r, cnPssErr: "Password and Confirm Password are not same.", emlErr: '', nmErr: '', pssErr: '' }))
            return false
        } else if (!rlId || !role) {
            toast.error('Select role')
            return false
        } else {
            setTeam(r => ({ ...r, btnLoader: true }))
            setTeamForm(r=>({...r, nmErr: "", emlErr: "", pssErr: "", cnPssErr: ""}))
            const cookies = new Cookies()
            try {
                const response = await axios.post(global.apiurl + '/teams', {
                    'userid': cookies.get('session_userid'),
                    'nm': nameRef.current.value,
                    'eml': emailRef.current.value,
                    'pass': passRef.current.value,
                    'role': role,
                    'rl_id': rlId,
                }, {
                    headers: { 'Authorization': 'Token ' + cookies.get('session_token') }
                })
                const res = response.data
                if (res.st === 1) {
                    toast.success(res.dt)
                    setTeam(r => ({ ...r, tmTbleLod: true }))
                    await handleTmInitialize()
                    setTeam(r => ({ ...r, btnLoader: false, tmTbleLod: false }))
                } else if (res.st === 0) {
                    toast.error(res.dt)
                    setTeam(r => ({ ...r, btnLoader: false }))
                } else {
                    setTeam(r => ({ ...r, btnLoader: false }))
                }
            } catch (err) {
                setTeam(r => ({ ...r, btnLoader: false }))
            }
        }
        ;[nameRef, emailRef, passRef, cnPassRef].forEach((ref) => {
            if (ref.current) ref.current.value = ""
        })
        setTeamForm(r => ({ ...r, role: "", rlId: "" }))
    }

    const handleDeleteProject = async () => {
        setTeam(r => ({ ...r, tmdelLoad: true }))
        const cookies = new Cookies()
        try {
            const response = await axios.post(global.apiurl + '/del_team', { 'userid': cookies.get('session_userid'), email: tmfinder }, {
                headers: { 'Authorization': 'Token ' + cookies.get('session_token') }
            })
            const res = response.data
            if (res.st === 1) {
                toast.success(res.dt)
                setTeam(r => ({ ...r, delPopUp: false, tmdelLoad: false, tmTbleLod: true }))
                await handleTmInitialize()
                setTeam(r => ({ ...r, tmTbleLod: false }))
            } else if (res.st === 0) {
                toast.error(res.dt)
                setTeam(r => ({ ...r, delPopUp: false, tmdelLoad: false }))
            } else {
                setTeam(r => ({ ...r, delPopUp: false, tmdelLoad: false }))
            }
        } catch (err) {
            setTeam(r => ({ ...r, delPopUp: false, tmdelLoad: false }))
        }
    }
    const handleManage = (client) => {
        setTeam(prev => ({ ...prev, tmmngOpn: true, tmmngCl: client }))
    }

    const handleRoleChange = (e) => {
        var { target: { value }, } = e;
        if (value) {
            const selectedRole = menuList.find(item => item.rl_id === value)
            if (selectedRole) {
                setTeamForm(data => ({
                    ...data,
                    role: selectedRole.rl,
                    rlId: value
                }))
            }
        }
    };

    const handleMoveRole = () => {
        setClient(accountData => ({ ...accountData, activeTab: '4', }))
    }

    return (
        <>
            <section className="drp-form p-b20 TeamForm">
                <div>
                    <Grid container>
                        <Grid item lg={6} md={12} xs={12}>
                            <Grid container spacing={2}>
                                <Grid item lg={6} md={12} xs={12}>
                                    <div>
                                        <RefInput label={'Full name:'} span={'*'} spanclassname="redClr p-l5" >
                                            <TextField inputRef={nameRef} type="text" error={nmErr.length > 0} helperText={nmErr} placeholder="Enter name" fullWidth />
                                        </RefInput>
                                    </div>
                                </Grid>
                                <Grid item lg={6} md={12} xs={12}>
                                    <div>
                                        <RefInput label={'E-Mail:'} span={'*'} spanclassname="redClr p-l5" >
                                            <TextField inputRef={emailRef} type="text" error={emlErr.length > 0} helperText={emlErr} placeholder="abc123@gmail.com" fullWidth />
                                        </RefInput>
                                    </div>
                                </Grid>
                                <Grid item lg={6} md={12} xs={12}>
                                    <div>
                                        <RefInput label={'Password:'} span={'*'} spanclassname="redClr p-l5">
                                            <TextField inputRef={passRef} type="password" error={pssErr.length > 0} helperText={pssErr} placeholder="" fullWidth />
                                        </RefInput>
                                    </div>
                                </Grid>
                                <Grid item lg={6} md={12} xs={12}>
                                    <div>
                                        <RefInput label={'Confirm Password:'} span={'*'} spanclassname="redClr p-l5" >
                                            <TextField inputRef={cnPassRef} type="password" error={cnPssErr.length > 0} helperText={cnPssErr} placeholder="" fullWidth />
                                        </RefInput>
                                    </div>
                                </Grid>
                            </Grid>
                        </Grid>
                    </Grid>
                    <div className="align-items-center gap-3 p-t15" style={{ display: 'grid', gridTemplateColumns: '286px 1fr' }}>
                        <div>
                            <CustomSelect handleTab={handleMoveRole} nonSelect={'Create Role first'} label={'Role:'} span={'*'} menulist={menuList} value={rlId} placeholder="Select" onchange={handleRoleChange} />
                        </div>
                    </div>
                    <div className="d-flex justify-content-end maxW180x p-t15">
                        <AppButton class=""
                            noIcon="d-none"
                            loading={btnLoader}
                            value="Create"
                            onclick={handleClientSubmit}
                        />
                    </div>
                </div>
            </section>
            <div className="p-t20">
                <TextLg class="lineHAuto m-b15 fB">Teams</TextLg>
            </div>
            <div>
                <TeamTable projectList={props.projectList} />
            </div>
            <CoverModal mnhdr={'Team Profile Settings'} subhdr={'Submitting an application to manage team member credentials.'} open={tmEdOpn} handleClose={e => setTeam(r => ({ ...r, tmEdOpn: false }))} style={style}>
                <TeamAccountManage tmEdNm={tmEdNm} tmmngCl={tmmngCl} />
            </CoverModal>
            <CoverModal mnhdr={'Access Management'} subhdr={'Submitting an application to manage apps.'} handleClose={handleAccessClose} open={accMngMdl} style={style}>
                <AccessManagement />
            </CoverModal>
            <ConfirmDeleteModal mnhdr="Delete team member?" subhdr="This team login and its project assignments will be permanently removed." open={delPopUp} modalClose={e => setTeam(r => ({ ...r, delPopUp: false }))} onSubmit={handleDeleteProject} delLoad={tmdelLoad} />
            <CoverModal mnhdr="Manage Team" subhdr="Choose which projects this member can access." handleClose={e => setTeam(r => ({ ...r, tmmngOpn: false }))} open={tmmngOpn}>
                <ManageTeam onClose={() => setTeam(r => ({ ...r, tmmngOpn: false }))} handleTmInitialize={handleTmInitialize} clientData={teamData} mngCl={tmmngCl} projectList={props.projectList} />
            </CoverModal>
        </>
    )
}
export default TeamManagement
