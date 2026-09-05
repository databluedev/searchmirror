import React, { useEffect, useState, useRef } from "react"; 
import "../style.scss";
import "../styles/notes.scss";

import { Tooltip, Zoom, CircularProgress, Modal, Fade, Backdrop, Grid } from "@mui/material";
import { CloseIconlg } from "../../commonComponents/icons";
import { TextLg, Para, ParaLg, Title, AppTooltip, Tsk } from "../../commonComponents/parts";
import { Button } from "@/components/ui/button";
import {fstLtrCapitalfun} from "../../common_fun";
import Badge from '@mui/material/Badge';

import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';
import {ModalBox} from "../../commonComponents/Modals";

import dayjs from 'dayjs';

import ViewNotes from "./kw_notes_view";
import {  ViewIcon, DeleteIcon } from "./icons";

import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { LocalizationProvider } from "@mui/x-date-pickers/LocalizationProvider";
import { StaticDatePicker } from "@mui/x-date-pickers/StaticDatePicker";
import { PickersDay } from '@mui/x-date-pickers/PickersDay';

import DataTable from "react-data-table-component";

const todayDate = dayjs();   

/* docs/DESIGN.md, Empty state: micro-label, one sentence of body, one primary
   action, no art. This was the line-art folder plus "NO KEYWORD NOTES FOUND"
   in 11px caps and nothing else -- a screen that told you it was empty without
   telling you what a note is or how to write one, while the button that writes
   one sat unexplained in the page header. */
const NoData = () => { 
  return (
     <div className="rdt_TableHead"> 
        <div className="emptyState"> 
           <p className="emptyState__label">No notes yet</p>
           <p className="emptyState__body">
              Notes mark a date on this keyword&rsquo;s rank history &mdash; a redesign, a
              title change, an algorithm update &mdash; so a later move has a cause
              beside it. Use Add Notes above to write the first one.
           </p>
        </div>
     </div>
  );
}; 

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

/// EMPTY SKELETON ROWS
function SkeletonRows(props=10) {
   var reportdata = { "ky": 0  }
   var ss = Array(props).fill(reportdata);
   return ss
}

export const ConfirmModal = (props) => {
  return (
    <div className="px-4 keyword-delete">
        <div className="f15x lh22x text-justify pb-1"> {props.content} </div>
        {/* /// */}
        <div className="pb-4 d-flex flex-wrap justify-content-end">
            <div className="addButton pt-3 m-r15 min-w-[100px] max-w-[300px] flex-[0_0_auto] text-ink-3">
            <Button type="button" variant="secondary" className="w-full Btn h38x" onClick={props.modalCancel}>{props.cancelTitle}</Button>
            </div>
            <div className="addButton pt-3 min-w-[100px] max-w-[300px] flex-[0_0_auto]">
            <Button type="button" variant="primary" className="w-full Btn h38x" onClick={props.modalConfirm} disabled={props.loading}>{props.loading ? <span className="loading" /> : props.confirmTitle}</Button>
            </div>
        </div>
    </div>
  )
}

/// NOTE VIEW POPUP 
export function NoteViewPopup(props) {
   return (
      <>
         <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={"View Note"}  TransitionComponent={Zoom}> 
            <div className="cursorP" onClick={()=> props.noteViewUpdate(props.row.nd)} >
               <ViewIcon className="mt-1" kwData={props.kwData} /> 
            </div>
         </Tooltip>
     
      </>
   );
}

/// NOTE DELETE
export function NoteDelete(props) { 
   // const [noteDeleteProgress, setNoteDeleteProgress] = useState({});
   const noteDeleteProgress = {}; 

   return (
      <>
         <div>
            {noteDeleteProgress[props.row.ky] ?
               <>
                  <CircularProgress size={14} />
               </>
            :
               <>
                  {/* /// DELETE ICON AND ITS ACTIONS */}
                  <Tooltip classes={{ tooltip: "Tltpsmall" }} placement="top" title={"Delete"}  TransitionComponent={Zoom}> 
                     <div className="cursorP" onClick={()=> props.keyUpdate(props.row)}>
                        <DeleteIcon className="kr_fnt" />
                     </div>
                  </Tooltip>
               </>
            }
         </div>
      </>
   );
}

/// NOTES TABLE
export function NotesTable(props) {
   const Improved = (
      <div>
         <Para>
         Adding notes then and there about your SEO impacts comes in handy especially, when plan your SEO strategy.
         </Para>
      </div>
   ); 

   const [open, setOpen] = useState(false);
   const handleOpen = (date) => {
      setCurrentdate(dayjs(date))
      setOpen(true)
   };
   const handleClose = () => setOpen(false);

   const [shownotes, setShownotes] = useState(true);
   const [currentdate, setCurrentdate] = useState(dayjs()); 
   const [highlightedDays, setHighlightedDays] = React.useState([]); 
   const emptyEditnote = useRef(null)

   const [noteActionModalStatus, setNoteActionModalStatus] = React.useState(false); 
   const [tableRows, setTableRows] = useState([]);
   const [actionNote, setActionNote] = useState({
      keywordKey: null,
      noteKey: null,
      confirmLoading: false,
   });

   var {keywordKey, noteKey, confirmLoading} = actionNote;

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

   const noteDeleteModalCall = (row) => { 
      setActionNote({
         ...actionNote,
         keywordKey: row.kk, 
         noteKey: row.ky
      })
      setNoteActionModalStatus(true);
   }
   
   const noteDeleteModalClose = () => {
      setNoteActionModalStatus(false); 
   }

   /* ON CONFIRMATION FROM DELETE POPUP */
   const noteDeleteAction = () => { 
      if (keywordKey && noteKey) {

         const cookies = new Cookies();
         const grpid = cookies.get('activegrp');
         const userid = cookies.get('session_userid');
         const usertoken = cookies.get('session_token'); 

         if(userid && grpid && noteKey && keywordKey) {
            setActionNote({
               ...actionNote,
               confirmLoading: true 
            })

            setTableRows([]);

            var data = {
               'userid': userid,
               'grpid': grpid,
               'kky': keywordKey,
               'nky': noteKey,
            };
            /* ON DELETE API */
            axios.post(global.apiurl + '/ub3RlZGVsNplX39bmdsZVZXRub3Rl', data, {
               headers: {'Authorization': 'Token '+ usertoken }
            }).then(response => {
               return response.data;
            }).then(res => {
               if (res.st === 1) {
                  if (res.dt.length) {
                     props.onUpdate(res.ct, res.dt)
                     setTimeout(() => {
                        setActionNote({
                           ...actionNote,
                           confirmLoading: false  
                        })
                        setNoteActionModalStatus(false); 
                        toast.success(res.ms) 
                     }, 750);
                  } else {
                    // setTableRows(null);  
                    props.onUpdate(res.ct, null)
                    setNoteActionModalStatus(false); 
                    setActionNote({
                       ...actionNote,
                       confirmLoading: false 
                    }) 
                    toast.success(res.ms)   
                  }
               } else { 
                  setNoteActionModalStatus(false);
                  setActionNote({
                     ...actionNote,
                     confirmLoading: false 
                  }) 
                  toast.error(res.ms)
               } 
            }) 
         } 
      }
   }

   const columns = [   
      /* /// NOTE TITLE */
      {
         id: 'title',
         name: 'TITLE',
         minWidth: "250px",
         maxWidth: "250px",
         selector: row => row.tl,
         style : { backgroundColor: "#FAF6FE", color: "#0a0a0a", fontSize:"14px" }, 
         cell: (row, index, column, id) => (
            <>
               {
                  row.tl ?
                     <div className="d-flex">
                        {row.tl}
                     </div>
                  :
                     <Tsk width={200} />
               }
            </>
        ),
      },
      
      /* /// NOTE DESCRIPTION */
      {
         id: 'note',
         name: 'NOTE',
         minWidth: "300px",
         selector: row => row.nt,
         cell: (row, index, column, id) => (
            <>
               {
                  row.nt ? 
                     <div className="d-flex">
                        {row.nt}
                     </div>
                  :
                     <Tsk width={600} />
               }   
            </>
         ),
      },
      
      /* /// NOTE DATE */
      {
         id: 'created',
         name: 'DATE',
         center:true,
         minWidth: "120px",
         maxWidth: "130px",
         selector: row => row.nd, 
         cell: (row, index, column, id) => (
            <>
               {
                  row.nd ? 
                     <>
                        {dayjs(row.nd).format("MMM DD, YYYY")}
                     </>  
                  :
                     <Tsk width={120} /> 
               }   
            </>
         ),

      },
      
      /* /// NOTE ACTIONS */
      {
         id: "actions",
         name: "ACTIONS",
         minWidth: "100px",
         maxWidth: "120px",
         center:true,
         cell: (row, index, column, id) => (
            <>
               <div className="d-flex justify-content-between align-items-center flex-wrap gap-2"> 
                  {
                     row.nd ? 
                        <>                           
                           {/* /// NOTE VIEW ICON */}
                           <NoteViewPopup noteViewUpdate={handleOpen} row={row}/>
                           {/* /// TEST NOTE DELETE ICON */}
                            {props.canManage ? <div><NoteDelete keyUpdate={noteDeleteModalCall} row={row} /></div> : null}
                        </>
                     :
                        <>
                           <Tsk width={25} /> 
                           <Tsk width={25} /> 
                        </>
                  }
               </div>
            </>
         ), 
      },
   ]; 

   /// USE EFFECT
   useEffect(() => {
      setTableRows(props.useRows); 
      setHighlightedDays(props.ntDate); 
   }, [props.useRows, props.ntDate]); 

   /// RETURN STATEMENT
   return (
      <>
          {props.canManage ? <ModalBox title="" onClose={noteDeleteModalClose} open={noteActionModalStatus}>
            <ConfirmModal 
               modalClose={noteDeleteModalClose} 
               cancelTitle="Cancel" 
               confirmTitle="Confirm" 
               modalCancel={noteDeleteModalClose} 
               modalConfirm={noteDeleteAction}    
               loading={confirmLoading}
               content="Are you sure you want to delete this note?"
            />
          </ModalBox> : null}


         {/* /// */}
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
               <div className="fp-modal-box absolute w-full h-full bg-[#FBFDFF] pl-[60px] outline-none">
                  <header className="fp-modal-header">
                     <div className="d-flex align-items-center justify-content-between px-2">
                        <div>
                           <Title class="fp-modal-title">
                               {props.canManage ? "Add Notes" : "Notes"}
                              <div className="toolTipIcon m-l5">
                                 <AppTooltip parentClassName="z9999" place="bottom-start" title={Improved} />
                              </div>
                           </Title> 
                           <Para class="fp-modal-sub-title mb-0">{props.kwData.KW ? fstLtrCapitalfun(props.kwData.KW) : <Tsk width={200} height={14} />}</Para> 
                        </div> 


                        <div style={{ flex: "0 0 auto" }}>
                           <Button type="button" variant="ghost" onClick={handleClose} className="wd-CloseButton">
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
                                 <TextLg class="fB mb-0 lh23x f18x">{props.kwData.KW ? currentdate.format("MMM DD, YYYY") : <Tsk width={120} />}</TextLg> 
                                  { shownotes && props.canManage ?
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
                                  <ViewNotes shownotes={shownotes} shownotesfun={shownotesfun} kwdata={props.kwData} keyid={props.keyId} currentdate={currentdate} tabledataUpdate={props.tabledataUpdate} emptyEditnote={emptyEditnote} canManage={props.canManage} />
                              </div>
                              
                           </Grid> 
                        </Grid>
                     </div>

                  </div>

               </div>
             </Fade>
         </Modal>

         {/* /// */}
         <div className="table-responsive ko-notesTable m-t20 m-b15"> 
            <DataTable
               columns={columns}
               data={tableRows === null ? [] : tableRows.length ? tableRows : SkeletonRows(props.perPage)}  
               // fixedHeader={"true"}
               pagination={true}
               paginationPerPage={10}
               paginationRowsPerPageOptions={[10, 50, 100]}  
               noDataComponent={<NoData />} 
            />
         </div>
      </>
   )
}
 
/// NOTES TAB
export default function NotesTab(props) {
   const [noteData, setNoteData] = useState({
      dataRows: [],
      noteDate: [],
      totalRows: -1
   });  

   var {dataRows, noteDate, totalRows} = noteData; 
   
   const noteUpdate = (tRows, dRows) => {
      setNoteData({
         ...noteData,
         dataRows: dRows,
         totalRows: tRows 
      })
      props.onRefresh(tRows) 
   }

   const tableUpdate = (data, flag) => {
      props.tabledataUpdate(data, flag); 
   }

   useEffect(() => {
      setNoteData(props.notedata); 
   }, [props.notedata]);

   return (
      <>
         <div className="project_overviewCard no-outline m-b30 m-t30">
            <div className="d-flex align-items-center m-t5">
               <ParaLg class="fB mb-0 lineHAuto">
                  {"Notes"}
               </ParaLg>
               
               {/* ///  TOTAL ROWS COUNT */}
               <div className="m-l5 fB mb-0 lineHAuto pClr"> 
                  {totalRows === 0 ?  
                    null
                  : totalRows > 0 ?  
                     <> ({totalRows}) </>
                  : 
                     <Tsk width={30} className="h20x" />
                  } 
               </div> 
            </div>

            <NotesTable ntDate={noteDate} kwData={props.kwdata} keyId={props.keyid} useRows={dataRows} totalRows={totalRows} onUpdate={noteUpdate} tabledataUpdate={tableUpdate} canManage={props.canManageNotes}/>
         </div>
      </>
   ); 


}
