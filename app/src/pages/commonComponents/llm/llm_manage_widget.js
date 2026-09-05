import React, { useState, useEffect } from 'react';
import { Box, Modal, Button } from "@mui/material";
// import { Link } from "react-router-dom";
import { Para, Title, AppTooltip } from "../parts";
import { Button as AppUIButton } from "@/components/ui/button";

import Fade from '@mui/material/Fade';
import Backdrop from '@mui/material/Backdrop';
import Skeleton from '@mui/material/Skeleton';
import CEditOnboardInfo from "./llm_onboard_info";

function LLMManageWidget(props) {
   const SkeletonColor = "var(--surface-2)";
   const [ref, setRef] = useState("");
   const [open, setOpen] = useState(false);
   const style = {
      position: "absolute",
      width: "100%",
      height: "100%",
      bgcolor: "var(--surface)",
      paddingLeft: '60px',
      outline: "none"
   };

   const Improved = (
      <div>
         <Para>
            You can manage your widgets for individual projects by enabling and disabling each widget as per your need.
         </Para>
      </div>
   );
   return (
      <>
         <div>
            {/* Adds prompts -- it opens the same form the first-run screen uses
                and spends nothing, so it is a secondary control. Only "Run
                analysis", which calls the providers, is primary on this header.
                It was labelled "New Analysis", which described the button next
                to it rather than itself. */}
            <Box className="mngWdgt" sx={{ flex: "0 0 auto" }}>
               <AppUIButton variant="secondary" className="w-full" onClick={() => setOpen(true)}>
                  <svg
                     xmlns="http://www.w3.org/2000/svg"
                     width="16"
                     height="16"
                     viewBox="0 0 16 16"
                  >
                     <path
                        id="Path_384"
                        data-name="Path 384"
                        d="M7.025.5H1.274A.774.774,0,0,0,.5,1.274V7.025a.774.774,0,0,0,.774.774H7.025A.774.774,0,0,0,7.8,7.025V1.274A.774.774,0,0,0,7.025.5ZM6.251,6.251h-4.2v-4.2h4.2v4.2ZM15.726.5H9.975a.774.774,0,0,0-.774.774V7.025a.774.774,0,0,0,.774.774h5.751a.774.774,0,0,0,.774-.774V1.274A.774.774,0,0,0,15.726.5Zm-.774,5.751h-4.2v-4.2h4.2ZM7.025,9.2H1.274A.774.774,0,0,0,.5,9.975v5.751a.774.774,0,0,0,.774.774H7.025a.774.774,0,0,0,.774-.774V9.975A.774.774,0,0,0,7.025,9.2Zm-.774,5.751h-4.2v-4.2h4.2v4.2Zm9.475-2.876h-2.1v-2.1a.774.774,0,1,0-1.548,0v2.1h-2.1a.774.774,0,1,0,0,1.548h2.1v2.1a.774.774,0,1,0,1.548,0v-2.1h2.1a.774.774,0,0,0,0-1.548Z"
                        transform="translate(-0.5 -0.5)"
                        fill="currentColor"
                     />
                  </svg>
                  Add prompts
               </AppUIButton>
            </Box>
         </div>

         <Modal
            className="wd-graph-modal"
            open={open}
            onClose={() => setOpen(false)}
            aria-labelledby="modal-modal-title"
            aria-describedby="modal-modal-description"
            closeAfterTransition
         >
            <Fade in={open} {...(open ? { timeout: 750 } : { timeout: 1000 })}>
               <Box className="wd-modal-box mng-modal-box" sx={style}>
                  <header className="wd-history-header">
                     <div className="d-flex align-items-center justify-content-between px-2">
                        <div>
                           <Title class="wd-history-title"></Title>
                        </div>
                        <div style={{ flex: "0 0 auto" }}>
                           {ref !== "close" ?
                              <Button onClick={() => setOpen(false)} className="wd-CloseButton">

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
                              :
                              <Skeleton variant="rectangular" width={64} height={43} sx={{ bgcolor: SkeletonColor }} />
                           }
                        </div>
                     </div>
                  </header>
                  <CEditOnboardInfo
                     projectList={props.projectList}
                     regionData={props.regionData}
                     kwdSearchDetails={props.kwdSearchDetails}
                     refetchLLMPrompts={props.refetchLLMPrompts}
                     onCreated={() => setOpen(false)}
                  />
               </Box>
            </Fade>
         </Modal>
      </>
   )
}

export default LLMManageWidget;
