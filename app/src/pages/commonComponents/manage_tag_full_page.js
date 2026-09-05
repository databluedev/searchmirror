import React, { useState } from 'react';
// import "../style.scss";
import { Fade, Backdrop, Box, Modal, Button } from '@mui/material';
import { TagIcon, CloseIconlg } from "./icons";
import { Para, Title, AppButton } from "./parts";
import { FullPageTagInput } from "./manage_tag";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';

const style = {
   position: "absolute",
   top: "50%",
   left: "50%",
   transform: "translate(-50%, -50%)",
   width: "min(520px, calc(100vw - 32px))",
   maxHeight: "calc(100vh - 64px)",
   bgcolor: "var(--surface)",
   border: "1px solid var(--line)",
   borderRadius: "var(--r-md)",
   boxShadow: "var(--elev-2)",
   display: "flex",
   flexDirection: "column",
   outline: "none"
};

function ManageTagFullPage({ managetagopenFunc, ...props }) {


   const [kwIds, setKwIds] = useState([]);
   // const [prevkwIds, setPrevkwIds] = useState([]);
   const [selectedtags, setSelectedtags] = useState([]);
   const [alltags, setAlltags] = useState([]);
   // const [commontg, setCommontg] = useState([]);
   const [commontags, setCommontags] = useState([]);
   const [othertg, setOthertg] = useState([]);
   const [btnloading, setBtnloading] = useState(false);



   React.useEffect(() => {
      if (props.type === "listtable") {
         managetagopenFunc.current = handleOpen
      } else if (props.type === "kwoverview") {
         managetagopenFunc.current = getCommonTag
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [])


   const [open, setOpen] = useState(false);
   const handleOpen = (selectedRowIds, selectedtag, alltgs) => {
      setKwIds(selectedRowIds || [])
      if (selectedtag && alltgs) {
         setSelectedtags(selectedtag || []);
         setAlltags(alltgs || []);
         var othertag = alltgs.filter((tag) => !selectedtag.includes(tag));
         setOthertg(othertag || []);
      }
      setOpen(true);
   }

   const updateTag = () => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      const grpid = cookies.get('activegrp');

      if (userid) {
         // }else if(userid && (selectedtags.length > 0 || commontags.length > 0)){
         setBtnloading(true);
         const data = {
            'userid': userid,
            'grpid': grpid,
            'tags': selectedtags,
            'commontags': commontags,
            'ids': kwIds,
         };
         axios.post(global.apiurl + '/update_tags', data, {
            // headers: {'Authorization': global.token}
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            const msg = res.message;
            if (res.status !== "true") {
               toast.error(msg)
               // this.setState({skeletonload : false,})
            } else {
               toast.success(msg)
               setOpen(false);

               if (props.type === "listtable") {
                  if (kwIds.length > 1) {
                     var data = props.lstresult.map((item, i) =>
                        kwIds.includes(item.key)
                           ? { ...item, tg: [...(item.tg || []), ...selectedtags] }
                           : item
                     );
                  }
                  else {
                     var data = props.lstresult.map((item, i) => kwIds.includes(item.key) ? { ...item, 'tg': selectedtags } : item)
                  }
                  props.tabledataUpdate(data);
               } else if (props.type === "gridtable") {
                  props.tableUpdate();
               } else if (props.type === "kwoverview") {
                  props.tagUpdate([...selectedtags, ...commontags]);
               }
               setBtnloading(false);
               props.resetSelectedRowIds()
               setSelectedtags([])
               // setTimeout(() => {
               //    // this.componentDidMount();
               // }, 1500); 
            }
         }).catch((error) => {
            setBtnloading(false);
            // history.push("/")
         });
      }
   }

   const getCommonTag = (selectedkwIds) => {
      const cookies = new Cookies();
      const usertoken = cookies.get('session_token')
      const userid = cookies.get('session_userid')
      const grpid = cookies.get('activegrp');

      if (JSON.stringify(selectedkwIds) !== JSON.stringify(kwIds) && selectedkwIds.length > 0) {
         setKwIds(selectedkwIds);
         setOpen(true);
         // this.setState({ prevcheckedListAll: [...checkedListAll], managetagloader: true, selectedtags: [], commontags: [], })
         const data = {
            'userid': userid,
            'grpid': grpid,
            'sltids': selectedkwIds,
         };
         axios.post(global.apiurl + '/getlabels', data, {
            // headers: {'Authorization': global.token}
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {

            if (res.status === "true" && res.result.length > 0) {
               setAlltags([...res.result[0]['o_tg'], ...res.result[0]['c_tg'], ...res.result[0]['s_tg']]);
               setOthertg(res.result[0]['o_tg']);
               if (selectedkwIds.length === 1) {
                  setSelectedtags([...res.result[0]['s_tg'], ...res.result[0]['c_tg']]);
               } else {
                  setCommontags(res.result[0]['c_tg']);
                  // setCommontg(res.result[0]['c_tg']);
                  setSelectedtags(res.result[0]['s_tg']);
               }

               // this.setState({
               //     othertags:res.result[0]['o_tg'] ,
               //     commontags: res.result[0]['c_tg'],
               //     commontagslabel: res.result[0]['c_tg'],
               //     selectedtags: res.result[0]['s_tg'],
               //     managetagloader: false
               // })   
            }
         }).catch((error) => {
            // history.push("/")
         });
      } else {
         setOpen(true);
      }
   }

   // const handleOpen = () => {
   //    setOpen(true);
   // }
   const handleClose = () => { setSelectedtags([]); setOpen(false) };

   return (
      <>
         {props.type === "gridtable" ?
            <div className="manageTag cursorP" onClick={() => getCommonTag(props.selectedRowIds)}>
               <span className="m-r5">
                  <TagIcon width="18" height="15" color="currentColor" />
               </span>
               Manage tag
            </div>
            : null}
         {/*<div className={props.className} onClick={handleOpen}>
            ADD
         </div>
         */}

         <Modal
            className="Managetag tagDialog"
            open={open}
            onClose={handleClose}
            aria-labelledby="tag-dialog-title"
            closeAfterTransition
            BackdropComponent={Backdrop}
            BackdropProps={{
               timeout: 1000,
            }}
         >
            <Fade in={open} {...(open ? { timeout: 750 } : { timeout: 1000 })}>
               {/* Capture phase: the tag field swallows Escape before MUI sees it. */}
               <Box
                  className="tagDialog__box"
                  sx={style}
                  onKeyDownCapture={(event) => {
                     if (event.key === "Escape") {
                        handleClose();
                     }
                  }}
               >
                  <header className="tagDialog__head">
                     <div>
                        <Title id="tag-dialog-title" class="tagDialog__title">{"Manage tags"}</Title>
                        <Para class="tagDialog__meta mb-0">
                           {(kwIds.length || 1) + (kwIds.length === 1 || kwIds.length === 0 ? " keyword selected" : " keywords selected")}
                        </Para>
                     </div>

                     <Button onClick={handleClose} className="tagDialog__close" aria-label="Close manage tags">
                        <CloseIconlg color="currentColor" />
                     </Button>
                  </header>

                  <section className="tagDialog__body">
                     <FullPageTagInput selectedtags={selectedtags} tagupdatefun={(tag) => setSelectedtags(tag)} othertg={othertg} othertagupdatefun={(tag) => setOthertg(tag)} othertags={alltags} cmntags={commontags} cmntagupdatefun={(tag) => setCommontags(tag)} />
                  </section>

                  <footer className="tagDialog__foot">
                     <AppButton
                        onclick={handleClose}
                        value="Cancel"
                        color="white"
                        class="borderBtn"
                        noIcon="d-none"
                     ></AppButton>
                     <AppButton loading={btnloading} disabled={btnloading} onclick={updateTag} value="Save" class="wd-btn-add" noIcon="d-none"></AppButton>
                  </footer>

               </Box>
            </Fade>
         </Modal>
      </>
   )
}

export default ManageTagFullPage;