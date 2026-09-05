import React, { useState } from "react";
import { toast } from 'react-toastify';
import { AddCompetitorIcon } from "../../commonComponents/icons";
import Backdrop from '@mui/material/Backdrop';
import Fade from '@mui/material/Fade'; 
import { Modal } from "@mui/material";
import { AppButton } from "../../commonComponents/parts";
import { GoOverviewPageIcon } from "../../commonComponents/icons";
import CompetitorsList from "./competitor_list";

function TopAllCompettors(props) {
   const [open, setOpen] = useState(false);
   if (props.canAdd === false) return null;

   const handleOpen = () => {
      if(props.addlm <= 0){
         toast.error("Sorry! You have reached your limit.")  
      }else{
         setOpen(true);
      }
   }
   const handleClose = () => setOpen(false);
   return (
      <>
      {props.pageurl && props.pageurl === "dashboard"?
         <button type="button" className="viewLink cursorP p-r20" onClick={handleOpen}>
            Add Competitor
            <span className="arrow"> 
            <GoOverviewPageIcon/>
            </span>
         </button>
         // <span onClick={handleOpen}>Add Competitor</span> 
      :
      <div onClick={handleOpen}>
         <AppButton 
         value="Add Competitor" 
         class="wd-btn-add p-l0 p-r0" 
         Icon={<AddCompetitorIcon />} />
      </div>
      }
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
            <div>
               <CompetitorsList tcc={props.tcc} pageUpdate={props.pageUpdate} dataUpdate={props.dataUpdate} close={handleClose} />
            </div>
         </Fade>
      </Modal>
      </>
   );
}

export default TopAllCompettors;
