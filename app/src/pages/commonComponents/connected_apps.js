import React, { useEffect, useState, } from "react";
import { useHistory } from 'react-router-dom';
import { Para, ParaLg, Tsk, AppButton, SelectMenu, AppTooltip } from "../commonComponents/parts";
import { Grid, Switch, Box } from "@mui/material";
import { styled } from "@mui/material/styles";
import { toast } from 'react-toastify';
import Cookies from 'universal-cookie';
import axios from 'axios';
import { Google } from "../commonComponents/icons";
import { GoogleOAuthProvider, useGoogleLogin } from '@react-oauth/google';
import { ConfirmDialog, ModalBox, PropertyModalBox } from "../commonComponents/Modals";
import GSCApp from "./gsc_app";
import GAApp from "./ga_app";
import GSCPropertyModel from "../commonComponents/gsc_property_model"
import ComingSoon from "./coming_soon";

const TrackingInfo = (
    <div>
        <Para class="m-0">
            Each week, tracking will occur on the chosen day
        </Para>
    </div>
);

function ConnectedApp(props) {
    const history = useHistory();
    const [gscToken, setGSCToken] = useState("");
    const [revokeGSCModal, setGSCRevokeModal] = React.useState(false);

    const [gaToken, setGAToken] = useState("")
    const [revokeGAModal, setGARevokeModal] = useState(false);
    const [property, setProperty] = useState("")

    const grpid = props.groupId;

    const [gscProperty, setGSCProperty] = useState("")
    const [gscProperties, setGSCProperties] = useState([]);
    const [gscPrtyMdlVsble, setGSCPrtyMdlVsble] = React.useState(false);
    const [trackDay, setTrackDay] = React.useState(['Monday']);
    const [pltForm, setPltForm] = useState('')
    const [cnPltForm, setCnPltForm] = useState('')
    const [weekDays, setWeekDays] = React.useState(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]);
    const [cnfm, setCnfm] = useState(false)
    const [pltChnge, setPltChnge] = useState(false)
    const [status, setStatus] = useState(false)
    const [pltLod, setPltLod] = useState(false)

    useEffect(() => {
        GSCConnected()
        GAConnected()
    }, []);

    const handleGSCPropertySelect = (property) => {
        const cookies = new Cookies();
        const userid = cookies.get('session_userid')
        const grpid = cookies.get('activegrp');
        const usertoken = cookies.get('session_token');
        console.log(property)
        const data = {
            'userid': userid,
            'grpid': grpid,
            'gsc_property': property,
            'gsc_refresh_token': gscToken,
            'type': "connect",
        };
        axios.post(global.apiurl + '/connectgsc', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data;
        }).then(res => {
            if (res.status === "true") {
                setGSCProperty(property)
                setStatus(true)
            }
            else {
                const msg = res.message;
                toast.error(msg)
            }
            setGSCPrtyMdlVsble(false)
        }).catch((error) => {
            console.log(error)
            toast.error("Unable to connect to Google Search Console")
        });
    }



    const revokeConfirmed = () => {
        const cookies = new Cookies();
        const userid = cookies.get('session_userid')
        const grpid = cookies.get('activegrp');
        const usertoken = cookies.get('session_token');
        const data = {
            'userid': userid,
            'grpid': grpid,
            'gcode': '',
            'type': "revoke",
        };
        axios.post(global.apiurl + '/connectgsc', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data;
        }).then(res => {
            if (res.status === "true") {
                toast.success("GSC Account Revoked")
                setGSCRevokeModal(false);
                setGSCToken("")
                setGSCProperty("")
                if (!property) {
                    setStatus(false)
                }
            }
            else {
                const msg = res.message;
                toast.error(msg)
            }
        }).catch((error) => {
            console.log(error)
            toast.error("Unable to connect to Google Search Console")
        });
    }
    const revokeGAConfirmed = () => {
        const cookies = new Cookies();
        const userid = cookies.get('session_userid')
        const grpid = cookies.get('activegrp');
        const usertoken = cookies.get('session_token');
        const data = {
            'userid': userid,
            'grpid': grpid,
            'gcode': '',
            'type': "revoke",
        };
        axios.post(global.apiurl + '/connectga', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data;
        }).then(res => {
            if (res.status === "true") {
                toast.success("GA Account Revoked")
                setGARevokeModal(false);
                setGAToken("")
                setProperty("")
                // setStatus(false)
                if (!gscProperty) {
                    setStatus(false)
                }
            }
            else {
                const msg = res.message;
                toast.error(msg)
            }
        }).catch((error) => {
            console.log(error)
            toast.error("Unable to connect to Google Analytics")
        });
    }

    const GSCConnected = () => {
        const cookies = new Cookies();
        const userid = cookies.get('session_userid')
        const grpid = cookies.get('activegrp');
        const usertoken = cookies.get('session_token');
        const data = {
            'userid': userid,
            'grpid': grpid,
            'gcode': '',
            'type': "verify",
        };
        axios.post(global.apiurl + '/connectgsc', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data;
        }).then(res => {
            if (res.status) {
                setGSCToken(res.gsc_refresh_token)
                setGSCProperty(res.gsc_property)
                setStatus(true)
            }
            else {
                setGSCToken("")
                setGSCProperty("")
            }
        }).catch((error) => {
            console.log(error)
            toast.error("Unable to connect to Google Search Console")
        });
    }
    const GAConnected = () => {
        const cookies = new Cookies()
        const userid = cookies.get('session_userid')
        const grpid = cookies.get('activegrp');
        const usertoken = cookies.get('session_token');
        const data = {
            'userid': userid,
            'grpid': grpid,
            'gcode': '',
            'type': "verify",
        };
        axios.post(global.apiurl + '/connectga', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data;
        }).then(res => {
            if (res.status) {
                setGAToken(res.status)
                setProperty(res.status)
                setStatus(true)
            }
            else {
                setGAToken("")
            }
            setTrackDay([res.dt])
            // if (res.pltform){
            setPltForm(res.pltform)
            setCnPltForm(res.pltform)
            // }else{
            // setPltForm(false)
            // }
        }).catch((error) => {
            console.log(error)
            toast.error("Unable to connect to Google Analytics")
        });
    }

    const handleTrackDay = (event) => {
        const { target: { value }, } = event;
        setTrackDay(typeof value === "string" ? value.split(",") : value[0]);
    };
    const handlePlatForm = (event) => {
        const { target: { value }, } = event;
        console.log(value)
        setPltForm(value)
    }

    const handleReset = async (e) => {
        // console.log('TEST')
        setCnfm(false)
        const cookies = new Cookies()
        const usertoken = cookies.get('session_token')
        const userid = cookies.get('session_userid')
        const grpid = cookies.get('activegrp')
        const params = {
            'userid': userid,
            'grpid': grpid,
            'trackday': trackDay[0]
        }
        await axios.post(global.apiurl + '/reset_track_day', params, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data
        }).then(res => {
            console.log('Done')
        }).catch(err => {
            console.log(err)
        })
    }
    const ResetPltApi = async (reset) => {
        setPltLod(true)
        const cookies = new Cookies()
        const usertoken = cookies.get('session_token')
        const userid = cookies.get('session_userid')
        const grpid = cookies.get('activegrp')
        const params = {
            'userid': userid,
            'grpid': grpid,
            'pltform': pltForm,
            'resetType': reset
        }
        await axios.post(global.apiurl + '/reset_platform', params, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data
        }).then(res => {
            if (res.st === 1) {
                setCnPltForm(res.dt)
                toast.success(res.msg)
            }
        }).catch(err => {
            console.log(err)
        })
        setPltLod(false)
    }
    const handlePltChange = async () => {
        await ResetPltApi(true)
        setPltChnge(false)
    }
    const handleChangePlatform = async (e) => {
        if (pltForm === '') {
            toast.error('Choose platform')
        } else if (pltForm === cnPltForm) {
            // toast.warn('Change to new platform')
            console.log('Change to new Platform')
        }
        else {
            if (cnPltForm !== '' && status) {
                setPltChnge(true)
            }
            else {
                ResetPltApi(false)
            }
        }
        // setPltChnge(false)
    }

    return (
        <>
            <section className={props.className}>
                <div className={props.childclassName}>
                    <Grid container spacing={3} className="">
                        <Grid item xs={12} md={12} lg={12} xl={12}>
                            <section className="projectCard">
                                <div className="d-flex align-items-center justify-content-between m-b15">
                                    <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                        Tracking Schedule
                                        <span className="m-l5">
                                            <AppTooltip place="bottom-start" title={TrackingInfo} />
                                        </span>
                                    </ParaLg>
                                </div>
                                <div>
                                    {/* The control below writes GroupSetting.week_track_day
                                        (serp/keyword.py Reset_track_day), which is the weekday the
                                        weekly Search Console and Analytics pull runs on for this
                                        project -- nothing more. The paragraph that used to sit here
                                        was Search Console marketing copy: it explained what GSC is,
                                        invited the reader to connect it, and said nothing about the
                                        dropdown it was introducing. */}
                                    <Box className="text-justify"  >
                                        <Para class='p-r5'>
                                            Pick the day of the week this project pulls its Search Console and Analytics figures. The pull covers the seven days ending on that day, so changing it moves the window as well as the day. Daily rank tracking is unaffected.
                                        </Para>
                                    </Box>
                                    {!props.canManage ? <Para class="secondaryClr">Read-only access.</Para> : null}
                                    <div className="p-b10 w-25"><SelectMenu disabled={!props.canManage} value={trackDay} menulist={weekDays} placeholder="Select" onchange={handleTrackDay} /></div>
                                    {props.canManage ? <div className="d-flex justify-content-end">
                                        <Box className="text-justify" sx={{ minWidth: "145px", maxWidth: "165px", flex: "0 0 auto" }}>
                                            <AppButton noIcon="d-none" value="Submit" onclick={e => setCnfm(true)} />
                                        </Box>
                                    </div> : null}
                                </div>
                            </section>
                        </Grid>
                        <Grid item xs={12} md={12} lg={12} xl={12}>
                            <section className="projectCard">
                                <div className="d-flex align-items-center justify-content-between m-b15">
                                    <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                        Choose Your Platform
                                        <span className="m-l5">
                                            <AppTooltip place="bottom-start" title={TrackingInfo} />
                                        </span>
                                    </ParaLg>
                                </div>
                                <div>
                                    <Box className="text-justify"  >
                                        <Para class='p-r5'>
                                            {/* Connect your Google Search Console with Tracker to access detailed traffic insights such as impressions, clicks, and keyword rankings. This integration empowers you to optimize your online presence effectively. With the flexibility to connect or revoke at any time, you maintain full control over your preferences. Integrate Google Search Console to unlock the full potential of our features and experience a significant impact on your online strategies. If you're already connected but can't find new projects, consider revoking access and reconnecting for smooth synchronization and access to the latest additions. */}
                                            Select the platform of your website to access detailed performance insights. By choosing your platform, you can retrieve analytics data from Google Analytics (GA) and Google Search Console (GSC). Gain valuable insights into user behavior, traffic patterns, and search visibility. Make data-driven decisions to optimize your platform's success.
                                        </Para>
                                    </Box>
                                    {/* <div>
                                        <Box className="text-justify" sx={{ minWidth: "145px", maxWidth: "165px", flex: "0 0 auto" }}>
                                            <AppButton value="E-commerce" color='white'/>
                                        </Box>
                                    </div> */}
                                    {/* <div className="p-b10"><SelectMenu value={pltForm} menulist={['E-Commerce', 'Non E-Commerce']} placeholder="Select" onchange={handlePlatForm}/></div> */}
                                    <Box
                                        sx={{
                                            display: "flex",
                                            flexWrap: "wrap",
                                            alignItems: "center",
                                            gap: "12px 32px",
                                            margin: "16px 0 8px",
                                        }}
                                    >
                                        <div className='customRadio'>
                                            <label className='labl'>
                                                <input type='radio' name='radioname' value={'E-commerce'}
                                                    checked={pltForm === 'E-commerce'}
                                                    onChange={handlePlatForm}
                                                    disabled={!props.canManage}
                                                />
                                                <div>
                                                    <span className='border' />
                                                    <span className='f14x'>E-commerce</span>
                                                </div>
                                            </label>
                                        </div>
                                        <div className='customRadio'>
                                            <label className='labl'>
                                                <input type='radio' name='radioname' value={'Non E-commerce'}
                                                    checked={pltForm === 'Non E-commerce'}
                                                    onChange={handlePlatForm}
                                                    disabled={!props.canManage}
                                                />
                                                <div>
                                                    <span className='border' />
                                                    <span className='f14x'>Non E-commerce</span>
                                                </div>
                                            </label>
                                        </div>
                                    </Box>

                                    {/* <div className="p-b10"><SelectMenu value={trackDay} menulist={weekDays} placeholder="Select" onchange={handleTrackDay}/></div> */}
                                    {props.canManage ? <div className="d-flex justify-content-end">
                                        <Box className="text-justify" sx={{ minWidth: "145px", maxWidth: "165px", flex: "0 0 auto" }}>
                                            <AppButton noIcon="d-none" loading={pltLod} value="Submit" onclick={handleChangePlatform} />
                                        </Box>
                                    </div> : null}
                                </div>
                            </section>
                        </Grid>
                        {/* GoogleOAuthProvider throws "Missing required parameter
                            client_id" when handed an empty string, and an
                            unconfigured instance has exactly that -- which took
                            the whole settings page blank. So nothing that can
                            throw is rendered here.

                            What replaced it is NOT the old card. That one told
                            the user to register an OAuth client and set two
                            environment variables: an operator's job, described
                            to somebody with no shell. The instructions now live
                            in docs/DEPLOYMENT.md and the user gets the one fact
                            that concerns them. */}
                        {!global.gscClientId ? (
                            <Grid item xs={12}>
                                <ComingSoon title="Google Search Console and Analytics">
                                    Connect your Search Console and Analytics data to see clicks and
                                    impressions beside your rankings. Not available yet — it needs a
                                    server-side sign-in flow, which is being built.
                                </ComingSoon>
                            </Grid>
                        ) : !props.canManage ? (
                            <Grid item xs={12}>
                                <section className="projectCard">
                                    <ParaLg class="fB m-b5">Google Search Console and Analytics</ParaLg>
                                    <Para class="secondaryClr m-b0">
                                        Read-only access. {gscProperty ? `GSC: ${gscProperty}. ` : "GSC is not connected. "}
                                        {property ? `GA: ${property}.` : "GA is not connected."}
                                    </Para>
                                </section>
                            </Grid>
                        ) : (
                        <>
                        <GoogleOAuthProvider clientId={global.gscClientId}>
                            <GSCApp
                                title={"Revoke GSC Access"}
                                setGSCToken={setGSCToken}
                                revokeGSCModal={revokeGSCModal}
                                gscToken={gscToken}
                                revokeConfirmed={revokeConfirmed}
                                setGSCRevokeModal={setGSCRevokeModal}
                                dialog_title="GSC Integration"
                                content="Connect your Google Search Console with SearchMirror to access detailed traffic insights such as impressions, clicks, and keyword rankings. This integration empowers you to optimize your online presence effectively. With the flexibility to connect or revoke at any time, you maintain full control over your preferences. Integrate Google Search Console to unlock the full potential of our features and experience a significant impact on your online strategies. If you're already connected but can't find new projects, consider revoking access and reconnecting for smooth synchronization and access to the latest additions."
                                setGSCProperties={setGSCProperties}
                                setGSCPrtyMdlVsble={setGSCPrtyMdlVsble}
                                gscProperty={gscProperty}
                                platform={cnPltForm}
                            />
                        </GoogleOAuthProvider>
                        <GoogleOAuthProvider clientId={global.gaClientId}>
                            <GAApp
                                title={"Revoke GA Access"}
                                setGAToken={setGAToken}
                                revokeGAModal={revokeGAModal}
                                gaToken={gaToken}
                                revokeConfirmed={revokeGAConfirmed}
                                setGARevokeModal={setGARevokeModal}
                                property={property}
                                setProperty={setProperty}
                                dialog_title="GA Integration"
                                content="Connect your Google Analytics with SearchMirror to access detailed traffic insights such as sessions, active users. This integration empowers you to optimize your online presence effectively. With the flexibility to connect or revoke at any time, you maintain full control over your preferences. Integrate Google Analytics to unlock the full potential of our features and experience a significant impact on your online strategies. If you're already connected but can't find new projects, consider revoking access and reconnecting for smooth synchronization and access to the latest additions."
                                platform={cnPltForm}
                                setStatus={setStatus}
                            />
                        </GoogleOAuthProvider>
                        </>
                        )}
                    </Grid>
                </div>
            </section>
            {props.canManage ? <PropertyModalBox title="Choose a Property" onClose={() => setGSCPrtyMdlVsble(!gscPrtyMdlVsble)} open={gscPrtyMdlVsble} >
                <GSCPropertyModel gscdata={gscProperties} handleGSCPropertySelect={handleGSCPropertySelect} />
            </PropertyModalBox> : null}
            {props.canManage ? <ModalBox title="Confirmation" open={cnfm} onClose={e => { setCnfm(false) }}>
                <ConfirmDialog
                    modalClose={e => setCnfm(false)}
                    cancelTitle="Cancel"
                    confirmTitle="Reset"
                    modalCancel={() => setCnfm(false)}
                    modalConfirm={handleReset}
                    content="Are you sure you want to revoke the track day? This action will permanently remove the existing weekly records."
                />
            </ModalBox> : null}
            {props.canManage ? <ModalBox title='Confirmation' open={pltChnge} onClose={e => setPltChnge(false)}>
                <ConfirmDialog
                    modalClose={e => setPltChnge(false)}
                    cancelTitle="Cancel"
                    confirmTitle="Reset"
                    modalCancel={e => setPltChnge(false)}
                    modalConfirm={handlePltChange}
                    content="Are you sure you want to change the domain platform? This action will permanently remove the existing weekly, monthly and yearly records."
                />
            </ModalBox> : null}
        </>
    );
}

export default ConnectedApp;
