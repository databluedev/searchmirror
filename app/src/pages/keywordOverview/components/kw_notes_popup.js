import React, { useState, useRef } from 'react';
import { Modal, Fade, Backdrop } from "@mui/material";
import "../style.scss";
import { NotesIcon, CloseIconlg } from "../../commonComponents/icons";
import { TextLg, Para, Title, AppTooltip, Tsk } from "../../commonComponents/parts";
import { Button } from "@/components/ui/button";
import {fstLtrCapitalfun} from "../../common_fun";

import { Grid } from "@mui/material";

import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { StaticDatePicker } from "@mui/x-date-pickers/StaticDatePicker";

import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify'; 
import ViewNotes from "./kw_notes_view";

import dayjs from 'dayjs';
import Badge from '@mui/material/Badge';
import { PickersDay } from '@mui/x-date-pickers/PickersDay';

const todayDate = dayjs();   

function ServerDay(props) {
    const { highlightedDays = [], day, outsideCurrentMonth, ...other } = props; 
    const isSelected = highlightedDays.includes(props.day.format("YYYY-MM-DD"));

    return (
      <Badge
         key={props.day.toString()}
         color="secondary" 
         variant={isSelected ? 'dot' : undefined}
         overlap="circular"
      >
        <PickersDay {...other} outsideCurrentMonth={outsideCurrentMonth} day={day} />
      </Badge>
   );
}

/// KEYWORD NOTES POPUP 
function KwNotesPopup({ children, kwdata, keyid, tabledataUpdate}) {
   const Improved = (
      <div>
         <Para>
         Adding notes then and there about your SEO impacts comes in handy especially, when plan your SEO strategy.
         </Para>
      </div>
   ); 
   
   const [open, setOpen] = useState(false);
   const handleOpen = (date) => {
      setOpen(true)
      handleAPI() 
   }; 
   const handleClose = () => setOpen(false);

   const [shownotes, setShownotes] = useState(true);
   const [currentdate, setCurrentdate] = useState(dayjs()); 
   const [highlightedDays, setHighlightedDays] = React.useState([]); 
   const emptyEditnote = useRef(null)

   const shownotesfun = () =>  {
      setShownotes(!shownotes);
   }

    const addnotesfun = () => {
      emptyEditnote.current()
      setShownotes(false);
    }
   
    const dateChangefun = (newValue) => {
      setCurrentdate(newValue);
      if (shownotes === false){
         setShownotes(true);
      }
    }

    const popUpdate = (data, flag) => { 
      if (flag !== "update") {
        handleAPI()
      }
      tabledataUpdate(data, flag)  
    }

    const handleAPI = (limit=10, page=1) => {     
      try {
         const cookies = new Cookies();
         const userToken = cookies.get('session_token')
         const userId = cookies.get('session_userid')
         const grpId = cookies.get('activegrp')
         if (!grpId) { return; }   // no project: nothing to ask about
         const keyId = keyid

         if(userId && grpId && keyId) {
            var data = {
               'userid': userId,
               'grpid': grpId,
               'kid': keyId,
               'type': "cnt",
            };
            
            axios.post(global.apiurl + '/dm90ZlldhbGx19fbmXM', data, {
               headers: {'Authorization': 'Token '+ userToken }
            }).then(response => {
               return response.data;
            }).then(res => {
               if (res.st === 1) { 
                  setHighlightedDays(res.nl)  
               } else {
                  toast.error(res.message)
                  // window.location.reload(); 
               }
            }).catch((error) => {
               toast.error("Request failed, Try again later")
               // window.location.reload(); 
            }); 
         }
      } catch (error) {
         toast.error("Try again later")
         // window.location.reload(); 
      }
   }
   
   return (
      <>
         
          <div className="min-w-[124px] max-w-[140px] flex-[0_0_auto]">
             <Button
                type="button"
                variant="primary"
                className="w-full"
                onClick={handleOpen}
             >
                <span className="d-flex m-r10"><NotesIcon color="#ffffff" /></span>
                <span>{"Add Notes"}</span>
             </Button>
          </div>
       

         <Modal
            className="full-page-modal"
            open={open}
            onClose={handleClose}
            aria-label="Keyword notes"
            closeAfterTransition
            BackdropComponent={Backdrop}
            BackdropProps={{
               timeout: 1000,
            }}
         >
            <Fade in={open} {...(open ? { timeout: 750 } : { timeout: 1000 })}>
               <div className="fp-modal-box absolute w-full h-full bg-[#FBFDFF] pl-[60px] outline-none">
                  <header className="fp-modal-header">
                     <div className="d-flex align-items-center justify-content-between px-2">
                        <div>
                           <Title class="fp-modal-title">
                              {"Add Notes"}
                              <div className="toolTipIcon m-l5">
                                 <AppTooltip parentClassName="z9999" place="bottom-start" title={Improved} />
                              </div>
                           </Title> 
                           <Para class="fp-modal-sub-title mb-0">{kwdata.KW ? fstLtrCapitalfun(kwdata.KW) : <Tsk width={200} height={14} />}</Para> 
                        </div> 


                        <div style={{ flex: "0 0 auto" }}>
                           <Button type="button" variant="ghost" aria-label="Close notes" onClick={handleClose} className="wd-CloseButton">
                              <CloseIconlg color="#0a0a0a" />
                           </Button>
                        </div>
                     </div>
                  </header>

                  <div className="p20x kw-notes">

                     <div className="nt-whiteBox py-0">
                        <Grid container>

                           <Grid item xs={12} md={5} xl={4}>
                              <div className="w-100 notes-datepicker">
                                 <LocalizationProvider dateAdapter={AdapterDayjs} className="hai w-100">
                                   <StaticDatePicker
                                      className="w-100"
                                      orientation="landscape" 
                                      openTo="day"
                                      displayStaticWrapperAs="desktop"
                                      value={currentdate}  
                                      minDate={dayjs('2020-01-01')}
                                      maxDate={todayDate.add(1, 'year')}
                                      onChange={dateChangefun} 
                                      showDaysOutsideCurrentMonth={true}
                                      components={{
                                        day: ServerDay,
                                      }}
                                      componentsProps={{
                                        day: {
                                          highlightedDays,
                                        },
                                      }} 
                                   />
                                 </LocalizationProvider>
                              </div>
                           </Grid>

                           <Grid xs={12} item md={7} xl={8} 
                              sx={{
                                 borderLeft: "1px solid #ececef",
                                 padding: "20px",
                                 "@media (max-width: 767px)": {
                                   borderLeft: "none",
                                   paddingLeft: 0,
                                 },
                              }} 
                            >
                              <div className="d-flex justify-content-between align-items-center m-b25 h30x">
                                 <TextLg class="fB mb-0 lh23x f18x">{kwdata.KW ? currentdate.format("MMM DD, YYYY") : <Tsk width={120} />}</TextLg> 
                                 { shownotes ?
                                    <div className="smallButton w-[100px]">
                                       <Button
                                         type="button"
                                         variant="primary"
                                         className="w-full px-2 w-100"
                                         onClick={addnotesfun}
                                       >
                                         Add Note
                                       </Button>
                                    </div>
                                 : null }
                              </div>

                              <div className="keywordDetail notesDetail">
                                 <ViewNotes shownotes={shownotes} shownotesfun={shownotesfun} kwdata={kwdata} keyid={keyid} currentdate={currentdate} tabledataUpdate={popUpdate} emptyEditnote={emptyEditnote} />
                              </div>
                              
                           </Grid> 
                        </Grid>
                     </div>

                  </div>

               </div>
             </Fade>
         </Modal>
      </> 
   )
}

export default KwNotesPopup;
