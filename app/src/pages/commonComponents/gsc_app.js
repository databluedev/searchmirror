import { Box, Grid } from "@mui/material"
import { ConfirmDialog, ModalBox } from "./Modals"
import { AppButton, Para, ParaLg } from "./parts"
import { Google } from "./icons"
import Cookies from "universal-cookie";
import axios from "axios";
import { toast } from "react-toastify";
import { useGoogleLogin } from "@react-oauth/google";
import { SmallText } from "../commonComponents/parts"

function GSCApp(props) {
    console.log(props.platform)
    const handlePlatCheck = () => {
        if (props.platform !== '') {
            handleGoogleSignin()
        } else {
            toast.warn("Select your desired domain platform")
        }
    }
    const handleGoogleSignin = useGoogleLogin({
        onSuccess: async response => {
            const { code } = response;
            const cookies = new Cookies();
            const userid = cookies.get('session_userid')
            const grpid = cookies.get('activegrp');
            if (!grpid) { return; }   // no project: nothing to ask about
            const usertoken = cookies.get('session_token');
            const data = {
                'userid': userid,
                'grpid': grpid,
                'gcode': code,
                'type': "connect",
            };
            await axios.post(global.apiurl + '/gsctoken', data, {
                headers: { 'Authorization': 'Token ' + usertoken }
            }).then(response => {
                return response.data;
            }).then(res => {
                if (res.status === "true") {
                    props.setGSCToken(res.gsc_refresh_token)
                    props.setGSCProperties(res.gsc_properties)
                    props.setGSCPrtyMdlVsble(true)
                }
                else {
                    const msg = res.message;
                    toast.error(msg)
                }
            }).catch((error) => {
                console.log(error)
                toast.error("Unable to connect to Google Search Console")
            });
        },
        onError: (error) => console.log(error),
        scope: "https://www.googleapis.com/auth/webmasters.readonly",
        flow: 'auth-code',
        redirect_uri: global.gscRedirectURL,
        access_type: 'offline',
    });
    return (
        <>
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
                        {!props.gscProperty && <Box className="text-justify" sx={{ minWidth: "145px", maxWidth: "165px", flex: "0 0 auto" }} >
                            <AppButton noIcon="d-none" class="borderBtn pgaudit_connect" value="Connect GSC" color="white" type="submit" Icon={<Google />} onclick={handlePlatCheck} />
                        </Box>}

                        {props.gscProperty && <Box className="text-justify" sx={{ minWidth: "145px", maxWidth: "165px", flex: "0 0 auto" }} >
                            <AppButton value="Revoke GSC" class="wd-btn-add p-l0 p-r0" onclick={() => props.setGSCRevokeModal(true)}>
                            </AppButton>
                        </Box>}
                    </div>
                    <div className="d-flex justify-content-end">
                        {props.gscProperty && <SmallText class='m-t5'>({props.gscProperty})</SmallText>}
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
                        <SmallText class="m-0"> Upon successful connection, we will require 5 to 10 minutes to process your data for generating the reports.</SmallText>
                    </div>
                    <ModalBox title="" open={props.revokeGSCModal} onClose={() => { props.setGSCRevokeModal(false) }}>
                        <ConfirmDialog
                            title={props.dialog_title}
                            cancelTitle="Cancel"
                            confirmTitle="Revoke"
                            modalCancel={() => { props.setGSCRevokeModal(false) }}
                            modalConfirm={props.revokeConfirmed}
                            content="Do you want to revoke access to the linked GSC account?"
                        />
                    </ModalBox>
                </section>
            </Grid>
        </>
    )
}
export default GSCApp