import { AppButton, AppSmallButton } from "../../commonComponents/parts"
import axios from "axios";
import { useGoogleLogin } from "@react-oauth/google";
import Cookies from "universal-cookie";
import { toast } from "react-toastify";
import { SmallText } from "../../commonComponents/parts"

function GSC_connection(props) {

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
         const cookies = new Cookies();
         const userid = cookies.get('session_userid')
         const usertoken = cookies.get('session_token');
         const data = {
            'userid': userid,
            'gcode': code
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
         {!props.gscProperty ?
            <div>
               <div className="keyWrd" style={{ minWidth: "170px", maxWidth: "170px", flex: "0 0 auto" }}>
                  <AppSmallButton value="Connect GSC" class="wd-btn-add " onclick={handlePlatCheck}>
                  </AppSmallButton>
               </div>
            </div> :
            <div>
               <div className="keyWrd" style={{ minWidth: "170px", maxWidth: "170px", flex: "0 0 auto" }}>
                  <AppSmallButton value="Revoke GSC" class="wd-btn-add " onclick={() => props.setGSCRevokeModal(true)}>
                  </AppSmallButton>
               </div>
               <SmallText class='m-t5'>({props.gscProperty})</SmallText>
            </div>
         }
      </>
   )
}
export default GSC_connection