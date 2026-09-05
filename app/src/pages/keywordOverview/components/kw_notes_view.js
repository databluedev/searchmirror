import React, { useEffect, useState } from "react";
import "../style.scss";
import Cookies from 'universal-cookie';
import axios from 'axios';
import dayjs from 'dayjs';
import { toast } from 'react-toastify';
// import moment from 'moment';
import { Text, Para, Tsk } from "../../commonComponents/parts";
import { Button } from "@/components/ui/button";

import AddNotes from "./kw_notes_modify";
import {ModalBox} from "../../commonComponents/Modals";

//

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

/// VIEW NOTES
export default function ViewNotes({ shownotes, shownotesfun, kwdata, currentdate, keyid, tabledataUpdate, emptyEditnote, canManage }) {
   const [allnotes, setAllnotes] = useState(null);
   const [noteid, setNoteid] = useState(null);
   const [editnote, setEditnote] = useState(null);
   const [notedeleteMdlVsble, setNtDltMdlVsble] = React.useState(false);
   const [confirmLoading, setConfirmLoading] = React.useState(false);  

   useEffect (() => {
      emptyEditnote.current = emptyEditnotefun
      allnotesget(currentdate);
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [currentdate]);

   const noteDeleteMdlClose = () => {
      setNtDltMdlVsble(false);
   }

   const notesDeleteMdlfun = (ntid) => {
      setNoteid(ntid);
      setNtDltMdlVsble(true);
   }

   const emptyEditnotefun = () => {
      setEditnote(null);
   }

   const notesUpdate = (data, countFlag) => {
      setAllnotes(data);
      // shownotesfun();
      if(countFlag === "add") {
         tabledataUpdate([{...kwdata, nt: kwdata.nt + 1 }], countFlag);
      } else if(countFlag === "delete") {
         tabledataUpdate([{...kwdata, nt: kwdata.nt - 1 }], countFlag); 
      } else {
         tabledataUpdate([], countFlag);  
      }
   }

   const allnotesget = (sld) => {
      const cookies = new Cookies();
      const grpid = cookies.get('activegrp');
      const userid = cookies.get('session_userid');
      const usertoken = cookies.get('session_token')
      
      if(userid && grpid && keyid && sld) { 
         setAllnotes(null);
         var data = {
            'userid': userid,
            'grpid': grpid,
            'kwid': keyid, 
            // 'sld': moment(sld).format("YY-MM-DD"),
            'sld': dayjs.unix(sld/1000).format("YY-MM-DD"),
         };
         axios.post(global.apiurl + '/kwnotes', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if(res.status === "true") {
               setAllnotes(res.nts);
            } else {
               toast.error(res.message)
            }
         }).catch((error) => {
            // history.push("/")
         });
      }
   }

   const notesEditfun = (note) => {
      setEditnote(note);
      shownotesfun()
   }

   const notesDeletefun = () => {
      const cookies = new Cookies();
      const grpid = cookies.get('activegrp');
      const userid = cookies.get('session_userid');
      const usertoken = cookies.get('session_token')

      if(userid && grpid && noteid){
         setConfirmLoading(true) 
         var data = {
            'userid': userid,
            'grpid': grpid,
            'kwid': keyid,
            'ntid': noteid,
            // 'sld': moment(currentdate).format("YY-MM-DD"),
            'sld': currentdate.format("YY-MM-DD"), 
         };
         axios.post(global.apiurl + '/kwnotedelete', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
               if(res.status === "true") {  
                  // setAllnotes(res.nts)
                  notesUpdate(res.nts, "delete");
                  setNoteid(null);
                  setConfirmLoading(false); 
                  setNtDltMdlVsble(false);
                  toast.success("Notes deleted successfully") 
                   // this.props.parentCallback("remove");
               } else {
                  toast.error(res.message)
                  setConfirmLoading(false);
                  setNtDltMdlVsble(false);
               }
            }) 
      }else{
         toast.error('Something went wrong!')
         // history.push('/');
         setNtDltMdlVsble(false);
         setConfirmLoading(false); 
      }
   }

   return (
      <>
      {canManage ? <ModalBox title="" onClose={noteDeleteMdlClose} open={notedeleteMdlVsble} >
        <ConfirmModal 
          modalClose={noteDeleteMdlClose} 
          cancelTitle="Cancel"
          confirmTitle="Confirm" 
          modalCancel={noteDeleteMdlClose} 
          modalConfirm={notesDeletefun} 
          loading={confirmLoading}  
          content="Are you sure you want to delete this note?"
        />
      </ModalBox> : null}
      <div className={shownotes ? "" :"d-none"}>
         { allnotes && allnotes.length > 0 ? 
            allnotes.map((nts,i) => 
               <div className="note-box m-t15" key={i.toString()}>
                  <Text class="fB lh18x m-b10">{nts.tl}</Text>
                  <Text class="lh22x text-justify">
                     {nts.nt}
                  </Text>
                  {canManage ? <div className="d-flex justify-content-end gap-3 m-t15">
                     <div onClick={()=> notesEditfun(nts)}><Para class="mb-0 cursorP">Edit</Para></div>
                     <div onClick={()=> notesDeleteMdlfun(nts.id)}><Para class="mb-0 cursorP">Delete</Para></div>
                  </div> : null}
               </div>
            )
         : allnotes && allnotes.length === 0 ? 
            <div className="d-flex align-items-center justify-content-center minH240x lightTxtClr fB">
               No notes found for the keyword
            </div>
         : 
            [1,2].map((nts,i) => 
               <div className="note-box m-t15" key={i.toString()}>
                  <Text class="fB lh18x m-b15"><Tsk width={100} /></Text>
                  <Text class="lh22x text-justify">
                     <Tsk width={"100%"} height={16} />
                  </Text>
                  <Text class="lh22x text-justify">
                     <Tsk width={"80%"} height={16} />
                  </Text>
                  <div className="d-flex justify-content-end gap-3 m-t15">
                     <Para class="mb-0 cursorP"><Tsk width={40} /></Para>
                     <Para class="mb-0 cursorP"><Tsk width={50} /></Para>
                  </div>
               </div>
            )
         }
      </div>
      { shownotes === false && canManage ?
         <AddNotes shownotesfun={shownotesfun} notesUpdate={notesUpdate} keyid={keyid} currentdate={currentdate} editnote={editnote} />
      : null }
      </>
   );
}
