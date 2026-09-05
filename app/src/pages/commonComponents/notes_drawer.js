import React, { useState, useEffect } from 'react';
// import "../style.scss";

import moment from 'moment';
import {Text, TextLg, Tsk} from "./parts";
import {Drawer} from "@mui/material";


import Cookies from 'universal-cookie';
// import { toast } from 'react-toastify';
import axios from 'axios';

function NotesDrawer({ notesFunc, kwdates, notetype, keyid }) {

   const [notedate, setNotedate] = useState(moment().format("MM-DD-YYYY"));
   const [allnotes, setAllnotes] = useState(null);


   useEffect(() => {
      notesFunc.current = notesopenfun

      if(kwdates.length > 0){
         setNotedate(moment(kwdates[0]).format("MM-DD-YYYY"))
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [kwdates])


   const [open, setOpen] = React.useState(false);
   const toggleDrawer = (event) => {
      // if (event.type === "keydown" && (event.key === "Tab" || event.key === "Shift")) {
      //    return;
      // }

      setOpen(!open);
   };

   const notesopenfun = (event, chartContext, dataPointIndex) => {
      // setOpen(!open);
      var date = kwdates[dataPointIndex]
      if(notedate !== date){
         setNotedate(moment(date).format("MM-DD-YYYY"))
         setOpen(!open);

         const cookies = new Cookies();
         const grpid = cookies.get('activegrp');
         const userid = cookies.get('session_userid');
         const usertoken = cookies.get('session_token')

         if(userid && grpid && keyid) {
            setAllnotes(null);
            var data = {
               'userid': userid,
               'grpid': grpid,
               'kwid': keyid,
               'sld': moment(date).format("YY-MM-DD"),
            };
            if(notetype === "month"){
               data = {...data, 'ed': moment(date).endOf('month').format("YY-MM-DD")};
            }
            axios.post(global.apiurl + '/kwnotes', data, {
               headers: {'Authorization': 'Token '+ usertoken }
            }).then(response => {
               return response.data;
            }).then(res => {
               if(res.status === "true") {
                  setAllnotes(res.nts);
               } else {
                  // toast.error(res.message)
               }
            }).catch((error) => {
               // history.push("/")
            });
         }

          // this.setState({
          //     notestabVsble: "2",
          //     notesloading: true,
          //     notedate: this.state.kwdates.slice(0).reverse()[dataPointIndex],
          //     daynotes: [],
          // }, this.selectdatenotesget(this.state.kwdates.slice(0).reverse()[dataPointIndex]))
      }else{
         setOpen(!open);
      }
   }

	return (
      <div> 
         <Drawer
           className="customSmallDrawer"
           anchor="right"
           open={open}
           onClose={toggleDrawer}
         >
            <div className="p-4">
               <div className="d-flex justify-content-between align-items-center mb-4">
                  <TextLg class="fB mb-0">{ notetype === "month" ? moment(notedate).format('MMMM, YYYY') : moment(notedate).format('MMM Do, YYYY')}</TextLg>
                  <span className="cursorPointer" onClick={toggleDrawer}><svg id="Component_69_46" data-name="Component 69 – 46" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16"><path id="Path_410" data-name="Path 410" d="M13.4,12l6.3-6.3a.99.99,0,0,0-1.4-1.4L12,10.6,5.7,4.3A.99.99,0,0,0,4.3,5.7L10.6,12,4.3,18.3A.908.908,0,0,0,4,19a.945.945,0,0,0,1,1,.908.908,0,0,0,.7-.3L12,13.4l6.3,6.3a.967.967,0,0,0,1.4,0,.967.967,0,0,0,0-1.4Z" transform="translate(-4 -4)" fill="#0a0a0a"></path></svg></span>
               </div>

               { allnotes && allnotes.length > 0 ? 
                  allnotes.map((nts,i) =>
                     <div className="brownBox mb-3" key={i.toString()}>
                        <Text class="fB mb-2">{nts.tl}</Text>
                        <Text class="mb-0 text-justify">{nts.nt}</Text>
                     </div>
                  )
               : allnotes && allnotes.length === 0 ? 
                  <div className="d-flex align-items-center justify-content-center minH240x lightTxtClr fB">
                     No notes found for the keyword
                  </div>
               : 
                  [1,2].map((nts,i) => 
                     <div className="brownBox mb-3" key={i.toString()}>
                        <Text class="fB lh18x mb-2"><Tsk width={100} /></Text>
                        <Text class="mb-0 text-justify"><Tsk width={"100%"} height={40} /></Text>
                     </div>
                  )
               }
             
           </div>
         </Drawer>
      </div>
	)
}

export default NotesDrawer;