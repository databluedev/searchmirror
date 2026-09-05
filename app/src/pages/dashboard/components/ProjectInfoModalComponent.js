import { Backdrop } from '@mui/material';
import { CloseIconlg } from "../../commonComponents/icons";
import { Modal, Button,Grid,Box,Fade } from "@mui/material";
import { GoLinkIcon,DomainStatusIcon,DomainExpiryIcon,RegisterIcon,WWWIcon,DomainUpdateIcon,CalendarIcon,OrganizationIcon,StateIcon,CountryIcon } from "../../commonComponents/icons";
import {  Para, Title } from "../../commonComponents/parts";
import SiteMark from "../../commonComponents/site_mark";

const modalstyle = {
  position: "absolute",
  width: "100%",
  height: "100%",
  bgcolor: "#FBFDFF",
  outline: "none"
};


function ProjectInfoModalComponent(props) {
  
   function onModalClose(event) {
   props.onCloseModal(event);
   }

   return (
   <div>
   <Modal
      className="full-page-modal"
      open={props.IsModalOpened}
      onClose={onModalClose}
      aria-labelledby="modal-modal-title"
      aria-describedby="modal-modal-description" 
      closeAfterTransition
      BackdropComponent={Backdrop}
      BackdropProps={{
         timeout: 1000,
      }}
   >
   <Fade in={props.IsModalOpened} {...(props.IsModalOpened ? { timeout: 750 } : { timeout: 1000 })}> 
      <Box className="fp-modal-box responsivePadding" sx={modalstyle}> 
         <header className="fp-modal-header">
               <div className="d-flex align-items-center justify-content-between px-2">
               <div className="d-flex gap-3">
                  <div className="whiteBox projectFavIcon d-flex align-items-center justify-content-center">
                     <SiteMark domain={props.prjData.domainUrl} width={30} height={30} className="img-br" />
                  </div>
                  <div>
                  <Title class="mb-0 lineHAuto">{props.prjData.domainName}</Title>
                  <Para class="mb-0 d-flex">
                     <a href={props.prjData.domainUrl} target="_blank" className="d-flex" rel="noreferrer noopener">
                     <span className='modalDomain text-truncate'>{props.prjData.domainUrl}</span>
                     <div className="m-l5 d-flex align-items-center">
                     <GoLinkIcon/>
                     </div>
                     </a>
                  </Para>
               </div>
               </div>
               <div style={{ flex: "0 0 auto" }}>
                  <Button onClick={e => onModalClose(e)} className="wd-CloseButton">
                     <CloseIconlg color="#0a0a0a" />
                  </Button>
               </div>
            </div>
         </header>
         <section className="p20x">
            <div className="px-2">
            <Grid container spacing={5} className="projectInfo">
               <Grid item xs={12} sm={6} md={6} lg={4} xl={4}>
               <div className="d-flex align-items-center gap-3 m-b20 boxes">

                  {props.prjData.domainStatus === "Active" ?
                  <div className="box one">
                     <DomainStatusIcon width="24" height="21.41"/>
                  </div>
                  :
                  <div className="box nine">
                     <DomainExpiryIcon width="24" height="21.41"/>
                  </div>
                  }
                  <div className="boxContent">
                     <Title class=" fR lightTxtClr f18px">Domain Status</Title>
                     <Title class="fB f18px pClr"> {props.prjData.domainStatus} </Title>
                  </div>
               </div>
               </Grid>
               <Grid item xs={12} sm={6} md={6} lg={4} xl={4}>
               <div className="d-flex align-items-center gap-3 m-b20">
                  <div className="box two">
                     <RegisterIcon width="28" height="21"/>
                  </div>
                  <div className="boxContent">
                  <Title class=" fR lightTxtClr f18px">Register</Title>
                     <Title class="fB f18px"> {props.prjData.register} </Title>
                  </div>
               </div>
               </Grid>
               <Grid item xs={12} sm={6} md={6} lg={4} xl={4}>
               <div className="d-flex align-items-center gap-3 m-b20">
                  <div className="box three">
                     <WWWIcon width="34" height="7.93"/>
                  </div>
                  <div className="boxContent">
                     <Title class=" fR lightTxtClr f18px">Domain created</Title>
                     <Title class="fB f18px"> {props.prjData.domainCreated} </Title>
                  </div>
               </div>
               </Grid>
               <Grid item xs={12} sm={6} md={6} lg={4} xl={4}>
               <div className="d-flex align-items-center gap-3 m-b20">
                  <div className="box four">
                  <DomainUpdateIcon width="22.11" height="27.02"/>
                  </div>
                  <div className="boxContent">
                  <Title class=" fR lightTxtClr f18px">Domain Update</Title>
                  <Title class="fB f18px"> {props.prjData.domainUpdate} </Title>
                  </div>
               </div>
               </Grid>
               <Grid item xs={12} sm={6} md={6} lg={4} xl={4}>
               <div className="d-flex align-items-center gap-3 m-b20">
                  <div className="box five">
                  <CalendarIcon width="28" height="27.99"/>
                  </div>
                  <div className="boxContent">
                  <Title class=" fR lightTxtClr f18px">Domain Expiry</Title>
                  <Title class="fB f18px"> {props.prjData.domainExpiry} </Title>
                  </div>
               </div>
               </Grid>
               <Grid item xs={12} sm={6} md={6} lg={4} xl={4}>
               <div className="d-flex align-items-center gap-3 m-b20">
                  <div className="box six">
                     <OrganizationIcon width="28.02" height="26.81"/>
                  </div>
                  <div className="boxContent">
                  <Title class=" fR lightTxtClr f18px">Organization</Title>
                     <Title class="fB f18px">{props.prjData.organization}</Title>
                  </div>
               </div>
               </Grid>
               <Grid item xs={12} sm={6} md={6} lg={4} xl={4}>
               <div className="d-flex align-items-center gap-3">
                  <div className="box seven">
                  <StateIcon width="28" height="34.22"/>
                  </div>
                  <div className="boxContent">
                  <Title class=" fR lightTxtClr f18px">State</Title>
                     <Title class="fB f18px">{props.prjData.state}</Title>
                  </div>
               </div>
               </Grid>
               <Grid item xs={12} sm={6} md={6} lg={4} xl={4}>
               <div className="d-flex align-items-center gap-3">
                  <div className="box eight">
                     <CountryIcon  width="28" height="28"/>
                  </div>
                  <div className="boxContent">
                  <Title class=" fR lightTxtClr f18px">Country</Title>
                     <Title class="fB f18px">{props.prjData.country}</Title>
                  </div>
               </div>
               </Grid>
            </Grid>
         </div>
         </section>
         </Box>
      </Fade>
   </Modal>
   </div>
   );
}

export default ProjectInfoModalComponent;