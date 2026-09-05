import { AppButton, AppSmallButton, SmallText } from "../../commonComponents/parts"
import axios from "axios";
import { useGoogleLogin } from "@react-oauth/google";
import Cookies from "universal-cookie";
import { toast } from "react-toastify";

function GA_connection(props) {

    const handlePlatCheck=()=>{
        if (props.platform!==''){
            handleGoogleSignin()
        }else{
            props.setDmPlatformErr('Select your domain platform')
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
                        props.setGARfrshTkn(response.data.refresh_token)
                        fetchData(response)
                        props.setEdtPrjtMdlVsble(true)
                        toast.success("Your GA account has been successfully connected.")
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
        const data = {
            'pageSize': 50
        }
        const headers = {
            Authorization: 'Bearer ' + res.data.access_token,
            'Content-Type': 'application/json',
        };
        await axios.get('https://analyticsadmin.googleapis.com/v1alpha/accountSummaries', { data, headers }).then(res => {
            return res
        }).then(res => {
            if (res.status === 200) {
                console.log(res)
                if (res.hasOwnProperty('data')) {
                    props.setData(res.data)
                } else {
                    props.setData({})
                }
            } else {
                toast.error('Something went wrong')
                console.log('Something went wrong')
            }
        }).catch(error => {
            console.log(error)
        })
    }

    return (
        <>
            {!props.gaToken || !props.property ?
                <div>
                    <div className="keyWrd" style={{ minWidth: "170px", maxWidth: "170px", flex: "0 0 auto" }}>
                        <AppSmallButton value="Connect GA" class="wd-btn-add " onclick={handlePlatCheck}>
                        </AppSmallButton>
                    </div>
                </div> :
                <div>
                    <div className="keyWrd" style={{ minWidth: "170px", maxWidth: "170px", flex: "0 0 auto" }}>
                        <AppSmallButton value="Revoke GA" class="wd-btn-add " onclick={() => props.setRevokeGA(true)}>
                        </AppSmallButton>
                    </div>
                    <SmallText class='m-t5'>({props.property})</SmallText>
                </div>
            }
        </>
    )
}
export default GA_connection