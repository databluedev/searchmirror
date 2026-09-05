import React, { useState } from 'react';
import { Box, Modal, Button } from "@mui/material";
import "../style.scss";
import { Fade, Backdrop } from '@mui/material';
import { EmailNotificationIcon, CloseIconlg } from "../../commonComponents/icons";
import { Para, Title, AppIconButton } from "../../commonComponents/parts";
import MailNotifications from "../../commonComponents/mail_notifications";
import Cookies from 'universal-cookie';


function EmailSetting({ children, ...props }) {
   
   const style = {
      position: "absolute",
      width: "100%",
      height: "100%",
      bgcolor: "var(--paper)",
      paddingLeft: '60px',
      outline: "none"
   }; 

   const cookies = new Cookies();
   const grpid = cookies.get('activegrp')

   // const Improved = (
   //    <div>
   //       <Text class="fB m-b5">What is declined?</Text>
   //       <Para>
   //          Reference site about Lorem Ipsum, giving information on its origins, as
   //          well as a random Lipsum generator
   //       </Para>
   //       <p className="mb-0 m-t10 fB pClr">More info</p>
   //    </div>
   // ); 
   
   const [open, setOpen] = useState(false);
   const handleOpen = () => setOpen(true);
   const handleClose = () => setOpen(false);

   return (
      <>
         <div>
            <AppIconButton
               onclick={handleOpen}
               class="messageIcon"
               Icon={ <EmailNotificationIcon />}
            />    
         </div>
 
         <Modal
            className="full-page-modal"
            open={open}
            onClose={handleClose}
            aria-labelledby="modal-modal-title"
            aria-describedby="modal-modal-description" 
            closeAfterTransition
            BackdropComponent={Backdrop}
            BackdropProps={{
               timeout: 1000,
            }}
         >
            <Fade in={open} {...(open ? { timeout: 750 } : { timeout: 1000 })}> 
               <Box className="fp-modal-box" sx={style}> 
                  <header className="fp-modal-header">
                     <div className="d-flex align-items-center justify-content-between px-2">
                        <div>
                           <Title class="fp-modal-title">
                              {"E-mail notification"}
                              {/* <div className="toolTipIcon m-l5">
                                 <AppTooltip parentClassName="z9999" place="bottom-start" title={Improved} />
                              </div> */}
                           </Title> 
                           <Para class="fp-modal-sub-title mb-0">{"Email notifications can be either enabled or disabled as per your needs."}</Para> 
                        </div> 


                        <div style={{ flex: "0 0 auto" }}>
                           <Button onClick={handleClose} className="wd-CloseButton">
                              <CloseIconlg color="var(--ink)" />
                           </Button>
                        </div>
                     </div>
                  </header>

                  <MailNotifications className="p20x" childclassName="px-2" groupId={grpid} />

               </Box>
             </Fade>
         </Modal>
      </> 
   )
}

export default EmailSetting; 