import React, { useState, useEffect } from "react";
import axios from 'axios';
import { toast } from "react-toastify";
import { useGoogleLogin } from '@react-oauth/google';
import { AppButton, } from "../commonComponents/parts";
import Cookies from 'universal-cookie';
import { useHistory } from "react-router-dom";
import { Google } from "../commonComponents/icons";

const SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

function GSConnect(props) {
    const history = useHistory();
    const [accessToken, setAccessToken] = useState('');
    const [revokeOption, setRevokeOption] = useState('');

    useEffect(() => {
        setAccessToken(props.gsctoken)
        setRevokeOption(props.revokeOption)
    }, [props])

    const login = useGoogleLogin({
        onSuccess: async response => {
            const { code } = response;
            const cookies = new Cookies();
            const usertoken = cookies.get('session_token')
            const userid = cookies.get('session_userid')
            const grpid = cookies.get('activegrp');
            if (!grpid) { return; }   // no project: nothing to ask about
            if (!usertoken || !userid) {
                history.push("/login");
            }
            var data = {
                'userid': userid,
                'grpid': grpid,
                'code': code
            };
            
            await axios.post(global.apiurl + '/pageaudit/gsclogin', data, {
                headers: { 'Authorization': 'Token ' + usertoken }
            }).then(response => {
                return response.data;
            }).then(res => {
                if (res.status === 'true') {
                    if (res.acc_tkn) {
                        setAccessToken(res.acc_tkn);
                        props.updateAcsToken(res.acc_tkn)
                        toast.success("GSC connection established, revoke anytime from Account Settings.")
                    } else {
                        toast.error("Unable to connect to Google Search Console.")
                    }
                }
                else {
                    const msg = res.message;
                    toast.error(msg)
                }
            }).catch((error) => {
                history.push("/contentaudit")
            });
        },
        onError: (error) => console.log(error),
        scope: SCOPE,
        flow: 'auth-code',
        redirect_uri: 'https://api.tracker.example/pageaudit/gsclogin',  
        access_type: 'offline',
    });
    return (
        <>
            {/* {accessToken !== '' ?
                <AppButton noIcon="d-none" class="wd-btn-add pgaudit_revoke" value="Revoke GSC" color="primary" type="submit" Icon={<Google />} onclick={props.handleOpen} />
                :
                <AppButton noIcon="d-none" class="borderBtn pgaudit_connect" value="Connect GSC" color="white" type="submit" Icon={<Google />} onclick={login} />
            } */}

            {!accessToken && <AppButton noIcon="d-none" class="borderBtn pgaudit_connect" value="Connect GSC" color="white" type="submit" Icon={<Google />} onclick={login} />
            }

            {(accessToken && revokeOption ==="1") ? <AppButton noIcon="d-none" class="wd-btn-add pgaudit_revoke" value="Revoke GSC" color="primary" type="submit" Icon={<Google />} onclick={props.handleOpen} /> : <></>
            }
        </>
    )
}
export default GSConnect;
