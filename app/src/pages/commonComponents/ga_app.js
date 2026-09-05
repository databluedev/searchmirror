import { Box, Grid } from "@mui/material"
import { ConfirmDialog, ModalBox, PropertyModalBox } from "./Modals"
import { AppButton, Para, ParaLg, SmallText } from "./parts"
import { Google } from "./icons"
import Cookies from "universal-cookie";
import axios from "axios";
import { toast } from "react-toastify";
import { useGoogleLogin } from "@react-oauth/google";
import { useState } from "react";
import PropertyModel from "../addProject/components/property_model";

function GAApp(props) {
    const [data, setData] = useState(null)
    const [editPrjtMdlVsble, setEdtPrjtMdlVsble] = useState(false)
    const handlePlatCheck=()=>{
        if (props.platform!==''){
            handleGoogleSignin()
        }else{
            toast.warn("Select your desired domain platform")
        }
    }

    const handleGoogleSignin = useGoogleLogin({
        onSuccess: async response => {
            const { code } = response;
            const data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": global.gaClientId,
                "client_secret": global.gaSecretId,
                "redirect_uri": global.gscRedirectURL,
                'scope': 'https://www.googleapis.com/auth/analytics.readonly',
            };
            await axios.post("https://oauth2.googleapis.com/token", data)
                .then(response => {
                    console.log(response)
                    if (response.status === 200) {
                        props.setGAToken(response.data.refresh_token)
                        fetchData(response)
                        setEdtPrjtMdlVsble(true)
                    } else {
                        toast.error('Something went wrong')
                        console.log(response)
                    }
                }).catch((error) => {
                    console.log(error)
                    toast.error("Unable to connect to Google Analytics")
                });
        },
        onError: (error) => console.log(error),
        scope: "https://www.googleapis.com/auth/analytics.readonly",
        flow: 'auth-code',
        redirect_uri: global.gscRedirectURL,
        access_type: 'offline',
    });

    const fetchData = async (res) => {
        const url = 'https://analyticsadmin.googleapis.com/v1alpha/accountSummaries';
        let nextPageToken = null; 
        
        const headers = {
            Authorization: 'Bearer ' + res.data.access_token, 
            'Content-Type': 'application/json'
        };

        var params = { 
            pageSize: 200,  // Maximum allowed page size 
            pageToken: nextPageToken // For pagination
        };

        await axios.get(url, { headers, params }).then(res => { 
            return res
        }).then(res => {
            if (res.status === 200) {
                if (res.hasOwnProperty('data')) {
                    setData(res.data)
                } else {
                    setData({})
                }
            } else {
               toast.error("Connection error")  
            }
        }).catch(error => {
            toast.error("Something went wrong")
        }) 
    }

    const handlePropertySelect = async (property_data) => {
        props.setProperty(property_data.property)
        setData(null)
        setEdtPrjtMdlVsble(false)
        const cookies = new Cookies()
        const usertoken = cookies.get('session_token')
        const userid = cookies.get('session_userid')
        const grpid = cookies.get('activegrp')
        const data = {
            'userid': userid,
            'grpid': grpid,
            'ga_property': property_data.property,
            'ga_token': props.gaToken,
        }
        await axios.post(global.apiurl + '/ga_connect', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(res => {
            return res.data
        }).then(res => {
            if (res.st === 1) {
                toast.success(res.dt)
                props.setStatus(true)
            } else {
                toast.error(res.dt)
            }
        }).catch(error => {
            toast.error('Something went wrong')
            console.log(error)
        })
    }
    return (
        <>
            <PropertyModalBox title="Select Property" onClose={() => {setEdtPrjtMdlVsble(!editPrjtMdlVsble); setData(null)}} open={editPrjtMdlVsble} >
                <PropertyModel data={data} handlePropertySelect={handlePropertySelect} />
            </PropertyModalBox>

            <Grid item xs={12} md={12} lg={12} xl={12}>
                <section className="projectCard">
                    <div className="d-flex align-items-center justify-content-between m-b15">
                        <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                            {props.title}
                        </ParaLg>
                    </div>
                    <div>
                        <Box className="text-justify"  >
                            <Para class='p-r5'>
                                {props.content}
                            </Para>
                        </Box>
                    </div>
                    <div className="d-flex justify-content-end">
                        {(!props.gaToken || !props.property) && <Box className="text-justify" sx={{ minWidth: "145px", maxWidth: "165px", flex: "0 0 auto" }} >
                            <AppButton noIcon="d-none" class="borderBtn pgaudit_connect" value="Connect GA" color="white" type="submit" Icon={<Google />} onclick={handlePlatCheck} />
                        </Box>}

                        {(props.gaToken && props.property) && <Box className="text-justify" sx={{ minWidth: "145px", maxWidth: "165px", flex: "0 0 auto" }} >
                            <AppButton value="Revoke GA" class="wd-btn-add p-l0 p-r0" onclick={() => props.setGARevokeModal(true)}>
                            </AppButton>
                        </Box>}
                    </div>
                    <div className="d-flex justify-content-end m-t5 align-items-center">
                        <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width={props.dimension || "11"}
                        height={props.dimension || "11"}
                        viewBox="0 0 11 11"
                        className="m-r5"
                        >
                        <path
                            id="Path_49"
                            data-name="Path 49"
                            d="M7.5,2A5.5,5.5,0,1,0,13,7.5,5.5,5.5,0,0,0,7.5,2Zm0,8.25a.552.552,0,0,1-.55-.55V7.5a.55.55,0,1,1,1.1,0V9.7A.552.552,0,0,1,7.5,10.25Zm.55-4.4H6.95V4.75h1.1Z"
                            transform="translate(-2 -2)"
                            fill={props.color || "#b4aebe"}
                        />
                        </svg>
                        <SmallText class='m-0'> Upon successful connection, we will require 5 to 10 minutes to process your data for generating the reports.</SmallText>
                    </div>
                    <ModalBox title="" open={props.revokeGAModal} onClose={() => { props.setGARevokeModal(false) }}>
                        <ConfirmDialog
                            title={props.dialog_title}
                            cancelTitle="Cancel"
                            confirmTitle="Revoke"
                            modalCancel={() => { props.setGARevokeModal(false) }}
                            modalConfirm={props.revokeConfirmed}
                            content="Do you want to revoke access to the linked GA account?"
                        />
                    </ModalBox>
                </section>
            </Grid>
        </>
    )
}
export default GAApp