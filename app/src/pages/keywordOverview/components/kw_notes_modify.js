import React, { useEffect, useState } from "react";
import { useHistory } from "react-router-dom";
import "../style.scss";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';
import dayjs from 'dayjs';

import { Input } from "../../commonComponents/parts";
import { TextareaAutosize } from "@mui/material";
import { Button } from "@/components/ui/button";


//
export default function AddNotes({ shownotesfun, notesUpdate, keyid, currentdate, editnote }) {

   const history = useHistory();
   const [title, setTitle] = useState('');
   const [notedata, setNotedata] = useState('');
   const [btnloading, setBtnloading] = useState(false);

   const cookies = new Cookies();
   const grpid = cookies.get('activegrp');
   const userid = cookies.get('session_userid');
   const usertoken = cookies.get('session_token');

   const notechgfun = (e) => {
      if(e.target.value.length < 251){
         setNotedata(e.target.value);
      }
   }

   const titlechgfun = (e) => {
      if(e.target.value.length < 50){
         setTitle(e.target.value);
      }
   }

   useEffect(() => {
      if(editnote){
         setTitle(editnote.tl);
         setNotedata(editnote.nt);
      }else{
         setTitle('');
         setNotedata('');
      }
      setBtnloading(false);
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [])

   const createnotefun = () => {
      if(userid && grpid && keyid) {
         if(title.length === 0) {
            toast.error("Add a title to your note");
            return false;
         } else if(notedata.length === 0) {
            toast.error("Enter your notes");
            return false;
         } else {
            setBtnloading(true);
            var data = {
               'userid': userid,
               'grpid': grpid,
               'kwid': keyid,
               'tle': title,
               'nt': notedata,
               'sld': currentdate.format("YY-MM-DD"),
            };
            
            axios.post(global.apiurl + '/kwnotecreate', data, {
               headers: {'Authorization': 'Token '+ usertoken }
            }).then(response => {
               return response.data;
            }).then(res => {
               if(res.status === "true") {  
                  toast.success("New note added successfully")
                  setBtnloading(false);
                  notesUpdate(res.nts, "add");
                  shownotesfun();
               } else {
                  toast.error(res.message);
                  setBtnloading(false);
               }
            }).catch((error) => {
               setBtnloading(false);
               // history.push("/")
            }); 
         }
      }else{
         toast.error('Something went wrong!')
         history.push('/')
         setBtnloading(false);
      }
   }

   const updatenote = () => {
      if(userid && grpid && keyid) {
         if(title.length === 0) {
            toast.error("Enter your notes title");
            return false;
         } else if (notedata.length === 0) {
            toast.error("Enter your notes");
            return false;
         } else {
            setBtnloading(true);
            var data = {
               'userid': userid,
               'grpid': grpid,
               'kwid': keyid,
               'ntid': editnote.id,
               'tle': title,
               'nt': notedata,
               'sld': dayjs(editnote.nd).format("YY-MM-DD"),
            };

            axios.post(global.apiurl + '/kwnoteupdate', data, {
               headers: {'Authorization': 'Token '+ usertoken }
            }).then(response => {
               return response.data;
            }).then(res => {
               if(res.status === "true") {  
                  notesUpdate(res.nts, "update"); 
                  shownotesfun();
                  setBtnloading(false);
                  toast.success("Notes updated successfully")
               } else {
                  toast.error(res.message)
                  setBtnloading(false);
               }
            }).catch((error) => {
               setBtnloading(false);
               // history.push("/")
            });
         }
      }else{
         toast.error('Something went wrong!')
         history.push('/')
         setBtnloading(false);
      }
   }

   return (
      <>
         <form className="add-note">
            <div className="m-b20">
               <div className="f14x lh18x m-b10">
                  Title <span className="redClr">*</span>
               </div>
               <Input value={title} onchange={titlechgfun} />
            </div>
            <div className="m-b20">
               <div className="f14x lh18x m-b10">
                  Notes <span className="redClr">*</span>
               </div>
               <TextareaAutosize
                  className="w-100 textareai"
                  aria-label="text-area"
                  minRows={5}
                  maxRows={6}
                  value={notedata}
                  onChange={notechgfun}
               />
               <div className="text-right lightTxtClr lh14x p-t5">{notedata.length}/250</div>
            </div>

           <div className="grid grid-cols-2 gap-[15px]">
             <Button
               type="button"
               variant="secondary"
               className="w-full borderBtn"
               onClick={shownotesfun}
             >
               Cancel
             </Button>

             <Button
               type="button"
               variant="primary"
               className="w-full px-2"
               disabled={btnloading}
               onClick={editnote ? updatenote : createnotefun}
             >
               {btnloading ? <span className="loading" /> : (editnote ? "Update Note" : "Add Note")}
             </Button>
           </div>
         </form>

      </>
   );
}
