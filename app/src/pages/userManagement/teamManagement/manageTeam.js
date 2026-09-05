import { Button, Grid } from "@mui/material";
// Button (Select / Delete) stays MUI: the .smallBtn / .danger classes carry its look.
import React, { useEffect, useState } from "react";
import { AppButton, Para, Text, TextLg } from "../../commonComponents/parts";
import Cookies from "universal-cookie";
import axios from "axios";
import { toast } from "react-toastify";
import { url_to_host } from "../../common_fun";
import { GoLinkIcon } from "../../commonComponents/icons";
import SiteMark from "../../commonComponents/site_mark";


function ManageTeam(props) {
    const [mngdDtls, setMngdDtls] = useState({
        email: "",
        prjcts: [],
        isUpdtd: false
    })
    const [prBtnLoader, setPrBtnLoader] = useState(false);
    const { email, prjcts, isUpdtd } = mngdDtls

    useEffect(() => {
        props.clientData.forEach(item => {
            if (item.clml === props.mngCl) {
                setMngdDtls(prev => ({ ...prev, email: item.clml, prjcts: item.prjcts }))
            }
        })
    }, [props.clientData, props.mngCl])
    // console.log(email, prjcts)

    const handleProjectReSubmit = async () => {
        var finder = ""
        if (isUpdtd) {
            finder = email
        } else {
            finder = props.mngCl
            setPrBtnLoader(true)
            const cookies = new Cookies()
            var userid = cookies.get('session_userid')
            var token = cookies.get('session_token')
            var data = { 'userid': userid, 'em': finder, 'prjcts': prjcts, 'type': 'projects' }
            await axios.post(global.apiurl + "/mng_tm_prjcts", data, {
                headers: { "Authorization": "Token " + token }
            }).then(r => {
                return r.data
            }).then(async res => {
                if (res.st === 1) {
                    setPrBtnLoader(false)
                    toast.success(res.dt)
                    await props.handleTmInitialize()
                    props.onClose()
                } else if (res.st === 0) {
                    toast.error(res.dt)
                    setPrBtnLoader(false)
                } else {
                    setPrBtnLoader(false)
                }
            }).catch(err => {
                setPrBtnLoader(false)
            })
        }
    }

    const handleProject = (item) => {
        setMngdDtls(r => ({ ...r, prjcts: [...prjcts, item] }))
    }

    const handleOnDelete = (item) => {
        setMngdDtls(r => ({ ...r, prjcts: prjcts.filter(project => project !== item) }))
    }

    return (
        <>
            <section className="drp-form">
                <div className="px-2">
                    <Grid container columnSpacing={2}>
                        <Grid item xs={12} md={6} lg={8}>
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={12} lg={12}>
                                    <div>
                                        <TextLg class="lineHAuto m-0 fB">Choose Projects</TextLg>
                                    </div>
                                </Grid>
                                {props.projectList.map((item, index) => (
                                        <Grid key={item.GY} item xs={12} md={12} lg={6}>
                                            <div className="border bdr-5x p-3 bg-white grid grid-cols-[50px_4fr_1fr]">
                                                <div>
                                                    <div className="border m-r10 p-1 bdr-5x">
                                                        <SiteMark domain={item.DN} width={30} height={30} className="m-0 rounded" />
                                                    </div>
                                                </div>
                                                <div className="d-grid gap-2">
                                                    <div>
                                                        <Text class={'fM pClr f16x'}>{item.NM}</Text>
                                                        <a href={item.DN} target="_blank" rel="noopener noreferrer" className="goLink" >
                                                            <Para class="m-b5 lineHAuto d-flex align-items-center linknvrColor">
                                                                <span className={"text-truncate " + (url_to_host(item.DN).length > 20 ? "prjctDomain" : "")}>{url_to_host(item.DN)}</span><GoLinkIcon height={10} width={10} className={"m-l5"} /></Para>
                                                        </a>
                                                    </div>
                                                    <div>
                                                        <div>
                                                            <Para class="m-b5 lineHAuto d-flex align-items-center">{"Total Keywords"}</Para>
                                                        </div>
                                                        <div>
                                                            <TextLg class={'m-0 fB'}>{item.kw_c}</TextLg>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="d-flex align-items-center">
                                                    <Button disabled={prjcts.includes(item.GY)} onClick={e => handleProject(item.GY)} variant="contained" size="small" className="smallBtn">{'Select'}</Button>
                                                </div>
                                            </div>
                                        </Grid>
                                ))}
                            </Grid>
                        </Grid>
                        <Grid item xs={12} md={12} lg={4}>
                            <Grid container spacing={2}>
                                <Grid item xs={12} md={12} lg={12}>
                                    <div>
                                        <TextLg class="lineHAuto m-0 fB">Selected Projects</TextLg>
                                    </div>
                                </Grid>
                                {prjcts.length !== 0 ?
                                    prjcts.map(item => (
                                        props.projectList.map((pr_item, index) => {
                                            if (Number(pr_item.GY) === Number(item)) {
                                                return (
                                                    <Grid key={index} item xs={12} md={12} lg={12}>
                                                        <div className="border bdr-5x p-3 bg-white grid grid-cols-[50px_4fr_1fr]">
                                                            <div>
                                                                <div className="border m-r10 p-1 bdr-5x">
                                                                    <SiteMark domain={pr_item.DN} width={30} height={30} className="m-0 rounded" />
                                                                </div>
                                                            </div>
                                                            <div className="d-grid gap-2">
                                                                <div>
                                                                    <Text class={'fM pClr f16x'}>{pr_item.NM}</Text>
                                                                    <a href={pr_item.DN} target="_blank" rel="noopener noreferrer" className="goLink" >
                                                                        <Para class="m-b5 lineHAuto d-flex align-items-center linknvrColor">
                                                                            <span className={"text-truncate " + (url_to_host(pr_item.DN).length > 20 ? "prjctDomain" : "")}>{url_to_host(pr_item.DN)}</span><GoLinkIcon height={10} width={10} className={"m-l5"} /></Para>
                                                                    </a>
                                                                </div>
                                                                <div>
                                                                    <div>
                                                                        <Para class="m-b5 lineHAuto d-flex align-items-center">{"Total Keywords"}</Para>
                                                                    </div>
                                                                    <div>
                                                                        <TextLg class={'m-0 fB'}>{pr_item.kw_c}</TextLg>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                            <div className="d-flex align-items-center">
                                                                <Button variant="contained" size="small" onClick={e => handleOnDelete(pr_item.GY)} className="smallBtn danger">{'Delete'}</Button>
                                                            </div>
                                                        </div>
                                                    </Grid>
                                                )
                                            }
                                        })
                                    ))
                                    :
                                    <Grid item xs={12} md={12} lg={12}>
                                        <div className="border bdr-5x p-3 bg-white">
                                            <div className="d-flex align-items-center justify-content-center">
                                                <Para class="m-0">No Projects Selected</Para>
                                            </div>
                                        </div>
                                    </Grid>
                                }
                            </Grid>
                        </Grid>
                    </Grid>
                </div>
            </section>
            <div className=" position-sticky bottom-0 p-3 bg-white">
                <div className="d-flex justify-content-end">
                    <AppButton loading={prBtnLoader} class="maxW165x" value={`Save (${prjcts.length} / ${props.projectList.length})`} onclick={handleProjectReSubmit} />
                </div>
            </div>
        </>
    )
}
export default ManageTeam;
