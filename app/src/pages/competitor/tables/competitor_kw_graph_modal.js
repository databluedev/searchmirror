import React, { useState } from 'react';
// import "../style.scss";

import {Para, Title, Tsk} from "../../commonComponents/parts";
import { Box, Modal, Button } from "@mui/material";

import CompKeywordHistoryChart from "./competitor_kw_history_graph";
import Fade from '@mui/material/Fade';
import Backdrop from '@mui/material/Backdrop';

function KWGraphModal({ children, ...props }) {
   // const [kwData, setKWData] = useState(props.kwdata);  

   const style = {
      position: "absolute",
      width: "100%",
      height: "100%",
      bgcolor: "var(--surface)",
      paddingLeft: '60px',
      outline: "none"
   }; 

   
   const [open, setOpen] = useState(false);
   const handleOpen = () => setOpen(true);
   const handleClose = () => setOpen(false);

   return (
      <>
         <div className="d-flex">
            <div className="wd-vhButton cursorP d-flex" onClick={handleOpen}>
               {children}
            </div>
         </div>

         <Modal
            className="wd-graph-modal"
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
               <Box className="wd-modal-box" sx={style}> 
                  <header className="wd-history-header">
                     <div className="d-flex align-items-center justify-content-between px-2">
                        <div>
                           <Title class="wd-history-title">
                              {"Keyword rank history"}
                              {/*<div className="toolTipIcon">
                                 <AppTooltip place="bottom-end" title={Improved} />
                              </div>*/}
                           </Title> 
                           <Para class="wd-history-sub-title mb-0">{props.kwdata ? props.kwdata.KW : <Tsk width={120} />}</Para>
                        </div> 


                        <div style={{ flex: "0 0 auto" }}>
                           <Button onClick={handleClose} className="wd-CloseButton">
                           
                              <svg
                                 id="Component_69_46"
                                 data-name="Component 69 – 46"
                                 xmlns="http://www.w3.org/2000/svg"
                                 width="16"
                                 height="16"
                                 viewBox="0 0 16 16"
                              >
                                 <path
                                 id="Path_410"
                                 data-name="Path 410"
                                 d="M13.4,12l6.3-6.3a.99.99,0,0,0-1.4-1.4L12,10.6,5.7,4.3A.99.99,0,0,0,4.3,5.7L10.6,12,4.3,18.3A.908.908,0,0,0,4,19a.945.945,0,0,0,1,1,.908.908,0,0,0,.7-.3L12,13.4l6.3,6.3a.967.967,0,0,0,1.4,0,.967.967,0,0,0,0-1.4Z"
                                 transform="translate(-4 -4)"
                                 fill="#0a0a0a"
                                 />
                              </svg>
                           </Button>
                        </div>
                     </div>
                   </header>

                  <section className="wd-history-modal">
                     <CompKeywordHistoryChart kwdata = {props.kwdata} className="px-2 wd-history-inner-modal" projectbase={props.projectbase} />
                  </section>      
               </Box>
             </Fade>
         </Modal>
      </> 
   )
}

export default KWGraphModal; 