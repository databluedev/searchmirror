import { FilledInput, Grid, InputAdornment, TextField } from "@mui/material";
import React, { useContext, useEffect, useMemo, useRef, useState } from "react";
import { AppButton, ParaLg, RefInput } from "../../commonComponents/parts";
import { toast } from "react-toastify";
import { TeamContext } from "..";
import Visibility from '../../../assets/images/invisible.svg'
import InVisibility from '../../../assets/images/visible.svg'
import Cookies from "universal-cookie";
import axios from "axios";

function TeamAccountManage(props) {
    const { tmmngCl, tmEdNm, setTeam, handleTmInitialize } = useContext(TeamContext)
    const nmRef = useRef(null)
    const emRef = useRef(null)
    const pssRef = useRef(null)
    const cnPssRef = useRef(null)
    const [edNmErr, setEdNmErr] = useState('')
    const [pssErr, setPssErr] = useState('')
    const [cnPssErr, setCnPssErr] = useState('')
    const [nmLoader, setNmLoader] = useState(false)
    const [pssLoader, setPssLoader] = useState(false)
    useEffect(() => {
        if (nmRef.current && emRef.current) {
            nmRef.current.value = tmEdNm
            emRef.current.value = tmmngCl
        }
        setPssErr("")
        setEdNmErr("")
        setCnPssErr("")
    }, [tmEdNm, tmmngCl])
    // console.log(tmmngCl, tmEdNm)
    const handlePassChange = () => {
        if (!pssRef.current.value) {
            setPssErr('Enter password to continue')
            setCnPssErr('')
            return false
        } else if (pssRef.current.value.length < 4) {
            setPssErr('Password should contain atleast 4 letters')
            setCnPssErr('')
            return false
        } else if (!cnPssRef.current.value) {
            setCnPssErr('Enter confirm password')
            setPssErr('')
            return false
        } else if (cnPssRef.current.value !== pssRef.current.value) {
            setCnPssErr('Password and Confirm password are not same.')
            setPssErr('')
            return false
        } else {
            setPssErr('')
            setCnPssErr('')
            setPssLoader(true)
            const cookies = new Cookies()
            axios.put(global.apiurl + '/team_mng', {'userid':cookies.get('session_userid'), 'pass':pssRef.current.value, 'nm':nmRef.current.value, 'type':'pass', 'email':emRef.current.value}, {
                headers:{'Authorization': 'Token '+ cookies.get('session_token')}
            }).then(response=>{
                return response.data
            }).then(res=>{
                if (res.st===1){
                    toast.success(res.dt)
                    setPssLoader(false)
                    pssRef.current.value = ""
                    cnPssRef.current.value = ""
                }else if (res.st===0){
                    toast.error(res.dt)
                    setPssLoader(false)
                }else{
                    setPssLoader(false)
                }
            }).catch(err=>{
                setPssLoader(false)
            })
        }
    }
    const handleNameChange = () => {
        if (!nmRef.current.value) {
            setEdNmErr('Enter valid name')
            return false
        } else if (nmRef.current.value.length < 3) {
            setEdNmErr('Name should contain at least 3 characters at your name')
            return false
        } else {
            setEdNmErr("")
            setNmLoader(true)
            const cookies = new Cookies()
            axios.put(global.apiurl + '/team_mng', {'userid':cookies.get('session_userid'), 'pass':pssRef.current.value, 'nm':nmRef.current.value, 'type':'nm', 'email':emRef.current.value}, {
                headers:{'Authorization': 'Token '+ cookies.get('session_token')}
            }).then(response=>{
                return response.data
            }).then(res=>{
                if (res.st===1){
                    handleTmInitialize()
                    toast.success(res.dt)
                    setNmLoader(false)
                }else if (res.st===0){
                    toast.error(res.dt)
                    setNmLoader(false)
                }else{
                    setNmLoader(false)
                }
            }).catch(err=>{
                setNmLoader(false)
            })
        }
    }
    function Adornment() {
        const [showPassword, setShowPassword] = useState()
        const handleClickShowPassword = () => {
            setShowPassword(!showPassword)
        }
        return (
            <InputAdornment position="end" className="eyeIcon">
                <span
                    style={{ width: "14px", height: "19px" }}
                    onClick={handleClickShowPassword}
                // onMouseDown={handleMouseDownPassword}
                >
                    {showPassword ? (
                        <img src={InVisibility} alt="" />
                    ) : (
                        <img src={Visibility} alt="" />
                    )}
                </span>
            </InputAdornment>
        )
    }
    return (
        <>
            <div className="m-t20 m-l25 m-r25 m-b70">
                <Grid container spacing={4}>
                    <Grid item lg={12}>
                        <section className="projectCard">
                            <div className="d-flex justify-content-between align-items-center m-b15">
                                {/* <TextLg>Change Name</TextLg> */}
                                <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                    Change Name
                                </ParaLg>
                            </div>
                            <Grid container spacing={2}>
                                <Grid item lg={12}>
                                    <div className="maxW350x">
                                        {/* <Input label={'Name'} value={tmEdNm} onchange={e => setTeam(r => ({ ...r, tmEdNm: e.target.value }))} /> */}
                                        <RefInput label={'Full Name: '} span={'*'} spanclassname="redClr p-l5">
                                            <TextField inputRef={nmRef} error={edNmErr.length > 0} helperText={edNmErr} fullWidth />
                                        </RefInput>
                                    </div>
                                </Grid>
                                <Grid item lg={12}>
                                    <div className="maxW350x">
                                        {/* <Input disabled={true} label={'E-mail'} value={tmmngCl} /> */}
                                        <RefInput label={'E-Mail:'}>
                                            <TextField inputRef={emRef} disabled={true} fullWidth />
                                        </RefInput>
                                    </div>
                                </Grid>
                                <Grid item lg={12}>
                                    <div className="d-flex align-items-center justify-content-end">
                                        <AppButton loading={nmLoader} noIcon="d-none" value={'Save'} class="maxW150x" onclick={handleNameChange} />
                                    </div>
                                </Grid>
                            </Grid>
                        </section>
                    </Grid>
                    <Grid item lg={12}>
                        <section className="projectCard">
                            <div className="d-flex justify-content-between align-items-center m-b15">
                                {/* <TextLg>Change Name</TextLg> */}
                                <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                    Change Password
                                </ParaLg>
                            </div>
                            <Grid container spacing={2}>
                                <Grid item lg={12}>
                                    <div className="maxW350x">
                                        {/* <PasswordInput error={pssErr.length && true} helperText={pssErr} label={'Password: '} /> */}
                                        <RefInput label={'Password:'} span={'*'} spanclassname="redClr p-l5">
                                            <FilledInput className="passwordInput" disableUnderline={true} id="filled-adornment-password" type="password" inputRef={pssRef} error={pssErr.length > 0} fullWidth />
                                            {pssErr.length && true ?
                                                <label className="error-msg">{pssErr}</label>
                                                : null}
                                        </RefInput>
                                    </div>
                                </Grid>
                                <Grid item lg={12}>
                                    <div className="maxW350x">
                                        {/* <PasswordInput error={cnPssErr.length && true} helperText={cnPssErr} label={'Confirm Password: '} /> */}
                                        <RefInput label={'Confirm Password:'} span={'*'} spanclassname="redClr p-l5">
                                            {/* <TextField type="password" inputRef={cnPssRef} error={cnPssErr.length && true} helperText={cnPssErr} fullWidth /> */}
                                            <FilledInput className="passwordInput" disableUnderline={true} id="filled-adornment-password" type="password" inputRef={cnPssRef} error={cnPssErr.length > 0} fullWidth />
                                            {cnPssErr.length && true ?
                                                <label className="error-msg">{cnPssErr}</label>
                                                : null}
                                        </RefInput>
                                    </div>
                                </Grid>
                                <Grid item lg={12}>
                                    <div className="d-flex align-items-center justify-content-end">
                                        <AppButton loading={pssLoader} noIcon="d-none" value={'Save'} class="maxW150x" onclick={handlePassChange} />
                                    </div>
                                </Grid>
                            </Grid>
                        </section>
                    </Grid>
                </Grid>
            </div>
        </>
    )
}
export default TeamAccountManage;