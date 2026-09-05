import React, { useState, useEffect } from "react";
import { useHistory } from "react-router-dom";
import { Dialog, DialogContent, DialogActions, Modal, Box, Grow, Button, Backdrop, Fade, TextField } from "@mui/material";
import { CloseIconlg } from "./icons";
import { styled } from "@mui/material/styles";
import { AppButton, Input, Title, Para, PageAuditModalSearch, CGARemapModalSearch, Text } from "./parts";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';
import { revealFormError } from "./form_feedback";
import { FormHelperText, Switch, Tooltip, Zoom } from "@mui/material"
const Transition = React.forwardRef(function Transition(props, ref) {
   // return <Grow direction="left" ref={ref} {...props} onExited={() => { history.goBack(); }} />;
   return <Grow direction="left" ref={ref} {...props} />;
});

const AntSwitch = styled(Switch)(({ theme }) => ({
   width: 28,
   height: 16,
   padding: 0,
   display: "flex",
   "&:active": {
      "& .MuiSwitch-thumb": {
         width: 15,
      },
      "& .MuiSwitch-switchBase.Mui-checked": {
         transform: "translateX(9px)",
      },
   },
   "& .MuiSwitch-switchBase": {
      padding: 2,
      "&.Mui-checked": {
         transform: "translateX(12px)",
         color: "var(--surface)",
         "& + .MuiSwitch-track": {
            opacity: 1,
            backgroundColor: theme.palette.mode === "dark" ? "#177ddc" : "#1890ff",
         },
      },
   },
   "& .MuiSwitch-thumb": {
      boxShadow: "0 2px 4px 0 rgb(0 35 11 / 20%)",
      width: 16,
      height: 16,
      borderRadius: 50,
      transition: theme.transitions.create(["width"], {
         duration: 200,
      }),
   },
   "& .MuiSwitch-track": {
      borderRadius: 16 / 2,
      opacity: 1,
      backgroundColor:
         theme.palette.mode === "dark"
            ? "rgba(255,255,255,.35)"
            : "rgba(0,0,0,.25)",
      boxSizing: "border-box",
   },
}));

//
export const ProjectEdit = (props) => {

   const history = useHistory();
   // A blocked submit focuses the offending field and names the problem, so the
   // button never looks dead.
   const pnameRef = React.useRef(null);
   const [btnloading, setBtnloading] = useState(false);
   const [pname, setPname] = useState(props.pname || '');
   const [pnmerrmsg, setPnmerrmsg] = useState('');

   useEffect(() => {
      setPname(props.pname);
      setBtnloading(false);
   }, [props.pname]);

   const editProjectFun = (pid) => {
      if (!pname.trim()) {
         setPnmerrmsg("Enter project name")
         revealFormError("Enter project name", pnameRef);
         return false
      } else if (!/^[a-zA-Z0-9 ]+$/.test(pname)) {
         setPnmerrmsg("Not allowed special characters");
         revealFormError("Not allowed special characters", pnameRef);
         return false;
      } else {
         setBtnloading(true)
         const cookies = new Cookies();
         const userid = cookies.get('session_userid');
         const ckgrpid = parseInt(cookies.get('activegrp'));
         const usertoken = cookies.get('session_token')

         if (userid && ckgrpid && ckgrpid === parseInt(pid)) {

            const data = {
               'userid': userid,
               'grpid': parseInt(pid),
               'grpname': pname
            };
            axios.post(global.apiurl + '/updategroupservice', data, {
               // headers: {'Authorization': global.token}
               headers: { 'Authorization': 'Token ' + usertoken }
            }).then(response => {
               return response.data;
            }).then(res => {
               if (res.status === "true") {
                  toast.success(res.message)
                  setTimeout(() => {
                     props.modalClose()
                     props.updatefullpage()
                     setBtnloading(false);
                  }, 1000);
               } else {
                  toast.error(res.message)
                  setTimeout(() => {
                     history.push('/');
                     setBtnloading(false);
                  }, 1500);
               }
            }).catch((error) => {
               toast.error('Something went wrong!')
               setTimeout(() => {
                  history.push('/');
                  setBtnloading(false);
               }, 1500);
            });
         }
      }
   }

   const projectNameChgfun = (e) => {
      if ((/^[a-zA-Z0-9 ]+$/.test(e.target.value) || e.target.value === "") && e.target.value.length < 31) {
         setPname(e.target.value);
         setPnmerrmsg("")
      }
   }

   return (
      <div className="px-4 project-rename">
         <div className="pb-2 f24x"> Project name </div>
         <div className="pb-4 f15x lh22x text-justify"> Ensure your new project name before confirming it as it will appear across all path ways in the SearchMirror tool. </div>
         <div className="pb-2" ref={pnameRef}>
            <Input label={"Project name"} span={" *"} spanclassname={"redClr"} placeholder={'SearchMirror'} value={pname} onchange={projectNameChgfun} errmsg={pnmerrmsg} error={pnmerrmsg.length > 0} />
         </div>
         <div className="pb-4 d-flex flex-wrap justify-content-end">
            <Box
               className="addButton pt-3 m-r15"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto", color: 'var(--ink-3)' }}
            >
               <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn h38x" noIcon="d-none"></AppButton>
            </Box>
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto" }}
            >
               <AppButton noIcon="d-none" value="Update" color="primary" onclick={() => editProjectFun(props.pid)} loading={btnloading} disabled={btnloading} class="Btn h38x" />
            </Box>
         </div>
      </div>
   )
}

//
export const ProjectDelete = (props) => {
   const confirmRef = React.useRef(null);

   const history = useHistory();
   const [btnloading, setBtnloading] = useState(false);
   const [confirmInput, setConfirmInput] = useState('');
   const [cfmerrmsg, setCfmerrmsg] = useState('');

   useEffect(() => {
      setConfirmInput("");
      setBtnloading(false);
   }, [props.pid]);

   const deleteProjectFun = (pid) => {
      if (!confirmInput) {
         setCfmerrmsg('Type "1" for confirmation')
         revealFormError('Type "1" for confirmation', confirmRef);
         return false
      } else if (confirmInput !== "1") {
         setCfmerrmsg('Type "1" for confirmation');
         revealFormError('Type "1" for confirmation', confirmRef);
         return false
      } else {
         setBtnloading(true)
         const cookies = new Cookies();
         const userid = cookies.get('session_userid');
         const ckgrpid = parseInt(cookies.get('activegrp'));
         const usertoken = cookies.get('session_token')

         if (userid && ckgrpid && ckgrpid === parseInt(pid)) {
            const data = {
               'userid': userid,
               'grpid': parseInt(pid)
            };
            axios.post(global.apiurl + '/deletegroupservice', data, {
               // headers: {'Authorization': global.token}
               headers: { 'Authorization': 'Token ' + usertoken }
            }).then(response => {
               return response.data;
            }).then(res => {
               if (res.status === "true") {
                  const cookies = new Cookies();
                  // cookies.set('ckgrp', res.groupid, { path: '/', maxAge: global.cookiesexpire });  
                  cookies.set('activegrp', res.groupid, { path: '/', maxAge: global.cookiesexpire });

                  cookies.remove('checkedListAll', { path: '/' });
                  // cookies.set('lastmenuopen', 'sub0', { path: '/', maxAge: global.cookiesexpire });  
                  toast.success(res.message)
                  setTimeout(() => {
                     props.modalClose();
                     props.updatefullpage();
                     setBtnloading(false);
                     // history.push('/');     
                  }, 1000);
               } else {
                  toast.error(res.message)
                  setTimeout(() => {
                     history.push('/');
                     setBtnloading(false);
                  }, 1500);
               }
            }).catch((error) => {
               toast.error('Something went wrong!')
               setTimeout(() => {
                  history.push('/');
                  setBtnloading(false);
               }, 1500);
            });
         }
      }
   }

   return (
      <div className="px-4 project-delete">
         <div className="pb-2 f20x"> All the keywords and its history will be lost. </div>
         <div className="pb-4 f15x lh22x text-justify"> Are you sure you want to delete this project ? </div>
         <div className="pb-2" ref={confirmRef}>
            <Input placeholder={'Type "1" to confirm'} value={confirmInput} onchange={(e) => { setConfirmInput(e.target.value); setCfmerrmsg("") }} errmsg={cfmerrmsg} error={cfmerrmsg.length > 0} />
         </div>
         <div className="pb-4 d-flex flex-wrap justify-content-end">
            <Box
               className="addButton pt-3 m-r15"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto", color: 'var(--ink-3)' }}
            >
               <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn h38x" noIcon="d-none"></AppButton>
            </Box>
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto" }}
            >
               <AppButton noIcon="d-none" value="Confirm" color="primary" onclick={() => deleteProjectFun(props.pid)} loading={btnloading} disabled={btnloading} class="Btn h38x" />
            </Box>
         </div>
      </div>
   )
}

//
export const KeywordDelete = (props) => {

   const history = useHistory();
   const [btnloading, setBtnloading] = useState(false);

   useEffect(() => {
      setBtnloading(false);
   }, [props.pid]);

   // Delete Single and Multiple Keywords API
   const kwDeleteFun = () => {
      const cookies = new Cookies();
      const userid = cookies.get('session_userid');
      const usertoken = cookies.get('session_token')
      const grpid = cookies.get('activegrp');

      if (userid && props.selectedRowIds.length > 0) {
         setBtnloading(true)
         const data = {
            'userid': userid,
            'grpid': grpid,
            'ids': props.selectedRowIds,
         };
         axios.post(global.apiurl + '/multidelete', data, {
            // headers: {'Authorization': global.token}
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {

            const msg = res.message;
            if (res.status !== "true") {
               toast.error(msg)
               // this.setState({skeletonload : false, grpdeleteLoading: false, prjtDltModelVsble: false})
            } else {

               toast.success(msg)
               // this.setState({ checkedListAll: [], grid_checkedListAll: [], skeletonload : false,exportpdfurl:"", exportcsv:[], exporttxt:[], grpdeleteLoading: false, prjtDltModelVsble: false });
               cookies.remove('checkedListAll', { path: '/' });

               setTimeout(() => {
                  if (res.grpCnt === 0) {
                     cookies.remove('lastmenuopen', { path: '/' });
                     cookies.remove('activegrp', { path: '/' });
                     cookies.remove('ckgrp', { path: '/' });
                     cookies.remove('_ACTGS', { path: '/' });

                     history.push('/');
                  } else {
                     if (res.grpCheck === "ENABLE") {
                        cookies.set('lastmenuopen', 'sub0', { path: '/', maxAge: global.cookiesexpire });
                        cookies.set('activegrp', res.FstOcc, { path: '/', maxAge: global.cookiesexpire });
                        cookies.set('ckgrp', res.FstOcc, { path: '/', maxAge: global.cookiesexpire });
                     }
                     props.updatefullpage();
                     // setTimeout(() => {
                     //     this.UNSAFE_componentWillMount();   
                     //     this.componentDidMount();   
                     // }, 500);
                  }
               }, 1500);
            }
            setBtnloading(false)
            props.modalClose()
         }).catch(err => {
            setBtnloading(false)
            props.modalClose()
         });
      }
   }

   return (
      <div className="px-4 keyword-delete">
         <div className="pb-2 f20x"> {props.content === "typoerror" ? 'This keyword already exists on this project.' : 'This keywords and its history will be lost.'}</div>
         <div className="pb-2 f15x lh22x text-justify"> Are you sure you want to delete this keyword ? </div>
         <div className="pb-4 d-flex flex-wrap justify-content-end">
            <Box
               className="addButton pt-3 m-r15"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto", color: 'var(--ink-3)' }}
            >
               <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn h38x" noIcon="d-none"></AppButton>
            </Box>
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto" }}
            >
               <AppButton noIcon="d-none" value="Confirm" color="primary" onclick={kwDeleteFun} loading={btnloading} disabled={btnloading} class="Btn h38x" />
            </Box>
         </div>
      </div>
   )
}

//
export const ConfirmModal = (props) => {

   // const btnloading = useState(false);

   return (
      <div className="px-4 keyword-delete">
         <div className="f15x lh22x text-justify pb-1"> {props.content} </div>

         <div className="pb-4 d-flex flex-wrap justify-content-end">
            <Box
               className="addButton pt-3 m-r15"
               sx={{ minWidth: "100px", maxWidth: "300px", flex: "0 0 auto", color: 'var(--ink-3)' }}
            >
               <AppButton value={props.cancelTitle} onclick={props.modalCancel} color="white" class="Btn h38x" noIcon="d-none"></AppButton>
            </Box>
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "300px", flex: "0 0 auto" }}
            >
               {/*<AppButton noIcon="d-none" value={props.confirmTitle} color="primary" onclick={props.modalConfirm} loading={btnloading} disabled={btnloading} class="Btn h38x" />*/}
               <AppButton noIcon="d-none" value={props.confirmTitle} color="primary" onclick={props.modalConfirm} class="Btn h38x" />
            </Box>
         </div>
      </div>
   )
}

//
export const ConfirmDialog = (props) => {

   const btnloading = false;

   return (
      <div>
         <div className="px-3 pb-2 f20x"> {props.title && props.title} </div>
         <div className="px-3 pt-2 f15x lh22x text-justify"> {props.content} </div>

         <DialogActions className="px-3 flex-wrap">
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "300px", flex: "0 0 auto", color: 'var(--ink-3)' }}
            >
               <AppButton value={props.cancelTitle} onclick={props.modalCancel} color="white" class="Btn" noIcon="d-none"></AppButton>
            </Box>
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "300px", flex: "0 0 auto" }}
            >
               <AppButton noIcon="d-none" value={props.confirmTitle} color="primary" onclick={props.modalConfirm} loading={btnloading} disabled={btnloading} class="Btn" />
            </Box>
         </DialogActions>
      </div>
   )
}


export const DialogBox = ({ children, ...props }) => {

   const BootstrapDialog = styled(Dialog)(({ theme }) => ({
      '& .MuiDialog-paper': {
         width: '40%',
         background: "var(--ink)",
         color: "var(--surface)",
      },
      '& .MuiButton-containedWhite': {
         color: 'var(--ink-3)',
      },
      '& .MuiDialogContent-root': {
         padding: theme.spacing(2),
      },
      '& input': {
         fontSize: '12px',
         borderRadius: '5px',
         padding: '6px 15px',
         height: '24px',
      },
      '& .closeBtn': {
         backgroundColor: "var(--ink)",
         boxShadow: 'unset',
         height: '32px',
         minWidth: '40px',
         right: '6px'
      },
      '& .Btn': {
         height: '34px'
      },
      // '& .MuiDialogActions-root': {
      //   padding: theme.spacing(1),
      // },
   }));

   return (
      <BootstrapDialog
         open={props.open}
         TransitionComponent={Transition}
         keepMounted
         onClose={props.onClose}
         aria-labelledby="customized-dialog-title"
      >
         <DialogContent>
            <div className="pb-2">
               <div className="d-flex align-items-center justify-content-between">
                  <div className="px-3 f24x">{props.title}</div>
                  <Button className="p-0 closeBtn" onClick={props.onClose}>
                     <CloseIconlg color="#ffffff" />
                  </Button>
               </div>
            </div>
            {children}
         </DialogContent>
      </BootstrapDialog>
   );
};


export const PropertyModalBox = ({ children, ...props }) => {

   const style = {
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      // width: 400,
      // bgcolor: 'background.paper',
      width: '40%',
      bgcolor: '#ffffff !important',
      color: '#0a0a0a !important',
      // border: '2px solid #000',
      boxShadow: 24,
      // p: 4,
   };

   return (
      <Modal
         className="Property-Toggle-Modal"
         keepMounted
         open={props.open}
         onClose={props.handleClose}
         aria-labelledby="modal-modal-title"
         aria-describedby="modal-modal-description"
         closeAfterTransition
         BackdropComponent={Backdrop}
         BackdropProps={{
            timeout: 500,
         }}
      >
         <Fade in={props.open} {...(props.open ? { timeout: 1000 } : { timeout: 500 })}>
            <Box className={"modal-box " + (props.className ? props.className : "dark")} sx={style}>
               <div className="py-2">
                  <div className="d-flex align-items-center justify-content-between">
                     <div className="px-3 f24x">{props.title}</div>
                     <Button className="p-0 closeBtn" onClick={props.onClose}>
                        <CloseIconlg color={'#0a0a0a'} />
                     </Button>
                  </div>
               </div>

               {children}

            </Box>
         </Fade>
      </Modal>
   );
};


export const ModalBox = ({ children, ...props }) => {

   const style = {
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      // width: 400,
      // bgcolor: 'background.paper',
      width: '40%',
      // bgcolor: "var(--ink)",
      // color: "var(--surface)",
      // border: '2px solid #000',
      boxShadow: 24,
      // p: 4,
   };

   return (
      <Modal
         className="Toggle-Modal"
         open={props.open}
         onClose={props.onClose || props.handleClose}
         aria-labelledby="modal-modal-title"
         aria-describedby="modal-modal-description"
         closeAfterTransition
         BackdropComponent={Backdrop}
         BackdropProps={{
            timeout: 500,
         }}
      >
         <Fade in={props.open} {...(props.open ? { timeout: 1000 } : { timeout: 500 })}>
            <Box className={"modal-box " + (props.className ? props.className : "dark")} sx={style}>
               <div className="pb-2">
                  <div className="d-flex align-items-center justify-content-between">
                     <div className="px-3 f24x">{props.title}</div>
                     <Button className="p-0 closeBtn" onClick={props.onClose}>
                        <CloseIconlg />
                     </Button>
                  </div>
               </div>

               {children}

            </Box>
         </Fade>
      </Modal>
   );
};
//Competitor Delete
export const CompetitorDelete = (props) => {
   const confirmRef = React.useRef(null);

   const history = useHistory();
   const [btnloading, setBtnloading] = useState(false);
   const [confirmInput, setConfirmInput] = useState('');
   const [cfmerrmsg, setCfmerrmsg] = useState('');

   useEffect(() => {
      setConfirmInput("");
      setBtnloading(false);
   }, [props.cmpid]);

   const deleteProjectFun = (cmpid) => {
      if (!confirmInput) {
         setCfmerrmsg('Type "1" for confirmation')
         revealFormError('Type "1" for confirmation', confirmRef);
         return false
      } else if (confirmInput !== "1") {
         setCfmerrmsg('Type "1" for confirmation');
         revealFormError('Type "1" for confirmation', confirmRef);
         return false
      } else {
         setBtnloading(true)
         const cookies = new Cookies();
         const userid = cookies.get('session_userid');
         const usertoken = cookies.get('session_token')
         const grpid = cookies.get('activegrp')
         var comp_grpid = 0;
         if (props.pagetype === "competitors") {
            comp_grpid = props.cmpid
         } else {
            comp_grpid = cookies.get('__sp_cgrp__')
         }
         const data = {
            'userid': userid,
            'grpid': grpid,
            'cgrpid': comp_grpid,
         };
         axios.post(global.apiurl + '/compai/deletecompetitor', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            setBtnloading(false)

            if (res.st === 1) {
               setTimeout(() => {
                  setBtnloading(false);
                  toast.success(res.message)
                  if (props.pagetype === "competitors") {
                     props.deleteItem({ id: comp_grpid })
                     props.modalClose()
                  } else {
                     history.push('/competitors')
                  }
                  // history.push('/');     
               }, 1500);
            } else {
               toast.error(res.message)
               setTimeout(() => {
                  props.modalClose();
                  setBtnloading(false);
               }, 1000);
            }
         });

      }
   }

   return (
      <div className="px-4 project-delete">
         <div className="pb-2 f20x"> All the competitor details will be lost. </div>
         <div className="pb-4 f15x lh22x text-justify"> Are you sure you want to delete this competitor ? </div>
         <div className="pb-2" ref={confirmRef}>
            <Input placeholder={'Type "1" to confirm'} value={confirmInput} onchange={(e) => { setConfirmInput(e.target.value); setCfmerrmsg("") }} errmsg={cfmerrmsg} error={cfmerrmsg.length > 0} />
         </div>
         <div className="pb-4 d-flex flex-wrap justify-content-end">
            <Box
               className="addButton pt-3 m-r15"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto", color: 'var(--ink-3)' }}
            >
               <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn h38x" noIcon="d-none"></AppButton>
            </Box>
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto" }}
            >
               <AppButton noIcon="d-none" value="Confirm" color="primary" onclick={() => deleteProjectFun(props.pid)} loading={btnloading} disabled={btnloading} class="Btn h38x" />
            </Box>
         </div>
      </div>
   )
}

//
export const KRKeywordDelete = (props) => {

   const [btnloading, setBtnloading] = useState(false);

   useEffect(() => {
      setBtnloading(false);
      // console.log('...........KRKeywordDelete peops',props)
   }, [props.keyid, props.pid]);

   // Delete Single and Multiple Keywords API
   const kwDeleteFun = () => {
      setBtnloading(true)

      const cookies = new Cookies();
      const userid = cookies.get('session_userid');
      const usertoken = cookies.get('session_token')
      const grpid = cookies.get('activegrp');

      if (userid && props.keyid) {
         setBtnloading(true)
         const data = {
            'userid': userid,
            'grpid': grpid,
            // 'kw_id' : props.keyid,
            'kw_id': 0,
            'cid': props.pid
         };
         axios.post(global.apiurl + '/research/deletelist', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if (res.st !== 1) {
               toast.error(res.message)
               // {'st':0,'message':'Something went wrong'}
            } else {
               toast.success(res.message)
               setTimeout(() => {
                  // history.push("/managelist")
                  props.updatefullpage()
                  setBtnloading(false)
                  props.modalClose()
               }, 1000)
            }
         }).catch((error) => {
            // history.push("/login");  
         });
      }
   }

   return (
      <div className="px-4 keyword-delete">
         <div className="pb-2 f20x"> The entire keywords along with the complete data for this group will be lost. </div>
         <div className="pb-2 f15x lh22x text-justify"> Are you sure you want to delete this group ? </div>
         <div className="pb-4 d-flex flex-wrap justify-content-end">
            <Box
               className="addButton pt-3 m-r15"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto", color: 'var(--ink-3)' }}
            >
               <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn h38x" noIcon="d-none"></AppButton>
            </Box>
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto" }}
            >
               <AppButton noIcon="d-none" value="Confirm" color="primary" onclick={kwDeleteFun} loading={btnloading} disabled={btnloading} class="Btn h38x" />
            </Box>
         </div>
      </div>
   )
}


export const CompetitorEdit = (props) => {
   const cnameRef = React.useRef(null);

   const history = useHistory();
   const [btnloading, setBtnloading] = useState(false);
   const [pname, setPname] = useState(props.cname || '');
   const [pnmerrmsg, setPnmerrmsg] = useState('');

   const cookies = new Cookies();
   const userid = parseInt(cookies.get('session_userid'));
   const ckgrpid = parseInt(cookies.get('activegrp'));
   const usertoken = cookies.get('session_token')

   useEffect(() => {
      setPname(props.cname);
      setBtnloading(false);
   }, [props.cname]);

   const editProjectFun = (cid) => {
      if (!pname.trim()) {
         setPnmerrmsg("Enter competitor name")
         revealFormError("Enter competitor name", cnameRef);
         return false
      } else if (!/^[a-zA-Z0-9 ]+$/.test(pname)) {
         setPnmerrmsg("Not allowed special characters");
         revealFormError("Not allowed special characters", cnameRef);
         return false;
      } else {
         setBtnloading(true)

         if (userid && ckgrpid && cid) {

            const data = {
               'userid': userid,
               'grpid': ckgrpid,
               'cgrpid': cid,
               'grpname': pname
            };
            axios.post(global.apiurl + '/compai/updategrpname', data, {
               headers: { 'Authorization': 'Token ' + usertoken }
            }).then(response => {
               return response.data;
            }).then(res => {
               if (res.st === 1) {
                  toast.success(res.message)
                  // props.updateItem()
                  props.updateItem({ id: cid, cname: pname })
                  setTimeout(() => {
                     props.modalClose()
                     setBtnloading(false);
                  }, 1000);
               } else {
                  toast.error(res.message)
                  setTimeout(() => {
                     history.push('/');
                     setBtnloading(false);
                  }, 1500);
               }
            }).catch((error) => {
               toast.error('Something went wrong!')
               setTimeout(() => {
                  history.push('/');
                  setBtnloading(false);
               }, 1500);
            });
         }
      }
   }

   const compNameChgfun = (e) => {
      if ((/^[a-zA-Z0-9 ]+$/.test(e.target.value) || e.target.value === "") && e.target.value.length < 31) {
         setPname(e.target.value);
         setPnmerrmsg("")
      }
   }

   return (
      <div className="px-4 project-rename">
         <div className="pb-2 f24x"> Competitor name </div>
         <div className="pb-4 f15x lh22x text-justify"> Ensure your new competitor name before confirming it as it will appear across all path ways in the SearchMirror tool. </div>
         <div className="pb-2" ref={cnameRef}>
            <Input label={"Competitor name"} span={" *"} spanclassname={"redClr"} placeholder={'SearchMirror'} value={pname} onchange={compNameChgfun} errmsg={pnmerrmsg} error={pnmerrmsg.length > 0} />
         </div>
         <div className="pb-4 d-flex flex-wrap justify-content-end">
            <Box
               className="addButton pt-3 m-r15"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto", color: 'var(--ink-3)' }}
            >
               <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn h38x" noIcon="d-none"></AppButton>
            </Box>
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto" }}
            >
               <AppButton noIcon="d-none" value="Update" color="primary" onclick={() => editProjectFun(props.cid)} loading={btnloading} disabled={btnloading} class="Btn h38x" />
            </Box>
         </div>
      </div>
   )
}

// PAGE AUDIT STARTS //
export const AuditModal = (props) => {
   const primaryKeywordRef = React.useRef(null);

   const cookies = new Cookies();
   const userid = cookies.get('session_userid');
   const grpid = cookies.get('activegrp');
   const usertoken = cookies.get('session_token')
   const [pageURL, setPageURL] = React.useState('');
   const [pageKeywords, setPageKeywords] = React.useState({});
   const [primaryKeyword, setPrimaryKeyword] = React.useState('');
   const [btnloading, setBtnloading] = useState(false);
   const [keywordErrMsg, setKeywordErrMsg] = useState('');

   const auditMdlClose = () => {
      setPrimaryKeyword('')
      setPageKeywords({})
      props.handleClose();
   };

   useEffect(() => {
      setPageKeywords(props.activePageKeywords)
      setPageURL(props.activePageURL)
      setPrimaryKeyword('')
      setKeywordErrMsg('')
   }, [props.auditMdlClose, props.auditMdlVsble, props.activePageKeywords, props.activePageURL]);

   const selectPrimaryKeyword = (event) => {
      let pkeywordId = event.target.value;
      setPrimaryKeyword(pkeywordId)
   };

   const remapURL = () => {
      if (userid && grpid) {
         if (!primaryKeyword) {
            setKeywordErrMsg("Choose the primary keyword to audit");
            revealFormError("Choose the primary keyword to audit", primaryKeywordRef);
            return false
         }
         else {
            setBtnloading(true);
            setKeywordErrMsg("")
            if (userid && grpid && primaryKeyword) {
               var data = {
                  'userid': userid.toString(),
                  'grpid': grpid.toString(),
                  'kwid': primaryKeyword.toString(),
                  'paurl': pageURL.toString()
               };
               axios.post(global.apiurl + '/pageaudit/create', data, {
                  headers: { 'Authorization': 'Token ' + usertoken }
               }).then(response => {
                  return response.data;
               }).then(res => {
                  setBtnloading(false);
                  let msg = res.message;
                  if (res.status === "false") {
                     setPrimaryKeyword('')
                     setPageKeywords({})
                     toast.error(msg)
                     props.handleClose();
                  } else {
                     toast.success(msg)
                     setPrimaryKeyword('')
                     setPageKeywords({})
                     props.handleClose();
                     props.URLChanged(res.page_url, res.page_keyword)
                  }
               }).catch(err => {
                  setBtnloading(false);
                  setPrimaryKeyword('')
                  setPageKeywords({})
                  toast.error("Something went wrong")
                  props.handleClose();
               });
            }
         }
      }
   }

   const showProjectKeywords = (e) => {
      setBtnloading(true);
      setKeywordErrMsg("")

      if (e.target.checked === true) {
         if (userid && grpid) {
            if (userid && grpid) {
               var data = {
                  'userid': userid.toString(),
                  'grpid': grpid.toString(),
               };
               axios.post(global.apiurl + '/pageaudit/keywords', data, {
                  headers: { 'Authorization': 'Token ' + usertoken }
               }).then(response => {
                  return response.data;
               }).then(res => {
                  setBtnloading(false);
                  if (res.status === "false") {
                     setPrimaryKeyword('')
                     setPageKeywords({})
                  } else {
                     setPrimaryKeyword('')
                     setPageKeywords({})
                     setPageKeywords(res.pkeywords)
                  }
               }).catch(err => {
                  setBtnloading(false);
                  setPrimaryKeyword('')
                  setPageKeywords({})
               });
            }
         }
      }
      else {
         setBtnloading(false);
         setPrimaryKeyword('')
         setPageKeywords(props.activePageKeywords)
      }
   }

   return (
      <Modal className="" open={props.auditMdlVsble} onClose={auditMdlClose} closeAfterTransition
         aria-labelledby="modal-modal-title" aria-describedby="modal-modal-description">
         <Fade in={props.auditMdlVsble} {...(props.auditMdlVsble ? { timeout: 750 } : { timeout: 1000 })}>
            <Box className="wd-modal-box add-popup add-modal-width" >
               <header className="add-modal-width-pad">
                  <div className="popup-button-div">
                     <Button onClick={props.handleClose} className="wd-CloseButton popup-close">
                        <svg id="Component_69_46" data-name="Component 69 – 46" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
                           <path id="Path_410" data-name="Path 410" d="M13.4,12l6.3-6.3a.99.99,0,0,0-1.4-1.4L12,10.6,5.7,4.3A.99.99,0,0,0,4.3,5.7L10.6,12,4.3,18.3A.908.908,0,0,0,4,19a.945.945,0,0,0,1,1,.908.908,0,0,0,.7-.3L12,13.4l6.3,6.3a.967.967,0,0,0,1.4,0,.967.967,0,0,0,0-1.4Z"
                              transform="translate(-4 -4)" fill="#0a0a0a" />
                        </svg>
                     </Button>
                  </div>
                  <div className="d-flex align-items-center justify-content-between popup-head">
                     <div>
                        <Title className="wd-history-title">Add Primary Keyword</Title>
                        <Para className="wd-history-sub-title mb-0">Ensure that you choose the appropriate primary keyword. However, you can always modify this primary keyword later within the page optimization overview page
                        </Para>
                     </div>
                  </div>
                  <form fullWidth className='m-t15' autoComplete="off" >
                     <div className="m-b20 forms intent-input page_audit_div" ref={primaryKeywordRef}>
                        <PageAuditModalSearch className="page_audit_search" skeywords={pageKeywords} selectPrimaryKeyword={selectPrimaryKeyword} primaryKeyword={primaryKeyword} auditMdlClose={auditMdlClose} />
                        {keywordErrMsg && <FormHelperText className="Mui-error">{keywordErrMsg}</FormHelperText>}
                     </div>
                     <div className="d-flex align-items-center justify-content-start m-b15">
                        <AntSwitch
                           onChange={showProjectKeywords}
                           inputProps={{ "aria-label": "ant design" }}
                           className="modal-toggle"
                        />
                        <Para className="audit_modal_show_all"><span className="m-l10">Show all keywords from this project</span></Para>
                     </div>

                     {/* <div className="m-b20 forms intent-input">
                        <FormControl sx={{ m: 1, minWidth: 120 }} className="add-page-form">
                           <Select
                              displayEmpty
                              inputProps={{ 'aria-label': 'Without label' }}
                              className='add-page-select'
                              onChange={selectPrimaryKeyword}
                              value={primaryKeyword}
                           >
                              <MenuItem value=''> Choose the primary keyword.</MenuItem>
                              {pageKeywords.length > 0 && pageKeywords.map((eachKeyword, index) => (
                                 <MenuItem key={index} value={eachKeyword.kw_id}>{eachKeyword.kw_name}</MenuItem>
                              ))}
                           </Select>
                           {keywordErrMsg && <FormHelperText className="Mui-error">{keywordErrMsg}</FormHelperText>}
                        </FormControl>
                     </div> */}
                     <div className="popup-button m-t10">
                        <Button onClick={auditMdlClose} className="modal-cancel-button" data-dismiss="modal">Cancel</Button>
                        <AppButton noIcon="d-none" value="Audit" color="primary" onclick={() => remapURL()} loading={btnloading} disabled={btnloading} />
                     </div>
                  </form>
               </header>
            </Box>
         </Fade>
      </Modal>
   )
}

export const SecondaryKeywordChipModal = (props) => {
   return (
      <Modal className="modal-wd-graph-modal" open={props.secondaryMdlVsble} onClose={props.handleSecondaryClose} closeAfterTransition
         aria-labelledby="modal-modal-title" aria-describedby="modal-modal-description"
      >
         <Fade in={props.secondaryMdlVsble} {...(props.secondaryMdlVsble ? { timeout: 750 } : { timeout: 1000 })}>
            <Box className="wd-modal-box add-popup" >
               <header className="wd-history-header modal-border">
                  <div className="d-flex align-items-center justify-content-between">
                     <div>
                        <Title className="wd-history-title">Focused Keywords</Title>
                        <Para className="wd-history-sub-title mb-0">List of keywords focused on this selected page.
                        </Para>
                     </div>
                     <div style={{ flex: "0 0 auto" }}>
                        <Button onClick={props.handleSecondaryClose} className="wd-CloseButton chip-popup-close">
                           <svg id="Component_69_46" data-name="Component 69 – 46" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
                              <path id="Path_410" data-name="Path 410" d="M13.4,12l6.3-6.3a.99.99,0,0,0-1.4-1.4L12,10.6,5.7,4.3A.99.99,0,0,0,4.3,5.7L10.6,12,4.3,18.3A.908.908,0,0,0,4,19a.945.945,0,0,0,1,1,.908.908,0,0,0,.7-.3L12,13.4l6.3,6.3a.967.967,0,0,0,1.4,0,.967.967,0,0,0,0-1.4Z"
                                 transform="translate(-4 -4)" fill="#0a0a0a" />
                           </svg>
                        </Button>
                     </div>
                  </div>
                  <div className="modal_addtag add-tag-margin">
                     <div className="tags-input keyword">
                        <div className="fM f-md mb-3 mt-4"></div>
                        <ul className="maxh110x overflow-y-auto">
                           {props.activeSecondaryKeywords.length > 0 && props.activeSecondaryKeywords.map((eachKeyword, index) => (
                              index === 0 ?
                                 <Tooltip key={eachKeyword.kw_name} title="Primary Keyword" TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}><li className="cursorP"><span className="p-r10">{eachKeyword.kw_name}</span></li></Tooltip>
                                 : <li className="cursorP" key={eachKeyword.kw_name}><span className="p-r10">{eachKeyword.kw_name}</span></li>
                           ))}
                        </ul>
                     </div>
                  </div>
               </header>
            </Box>
         </Fade>
      </Modal>
   )

}

export const RevokeGSCAccess = (props) => {
   const [btnloading, setBtnloading] = useState(false);
   // Revoke Access
   const revokeAccess = () => {
      const cookies = new Cookies();
      const userid = cookies.get('session_userid');
      const usertoken = cookies.get('session_token');
      if (userid) {
         setBtnloading(true)
         const data = {
            'userid': userid,
         };
         axios.post(global.apiurl + '/pageaudit/revokeaccess', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            const msg = res.message;
            if (res.status !== "true") {
               toast.error(msg)
               setBtnloading(false)
               props.modalClose()
            } else {
               toast.success(msg)
               setBtnloading(false)
               props.revokeSuccess()
            }
         }).catch(err => {
            setBtnloading(false)
            props.modalClose()
         });
      }
   }

   return (
      <div className="px-4 keyword-delete">
         <div className="pb-2 f20x"> By revoking access, we will discontinue tracking the index status of your pages. </div>
         <div className="pb-2 f15x lh22x text-justify"> Are you sure you want to revoke this access ? </div>
         <div className="pb-4 d-flex flex-wrap justify-content-end">
            <Box
               className="addButton pt-3 m-r15"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto", color: 'var(--ink-3)' }}
            >
               <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn h38x" noIcon="d-none"></AppButton>
            </Box>
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto" }}
            >
               <AppButton noIcon="d-none" value="Confirm" color="primary" onclick={revokeAccess} loading={btnloading} disabled={btnloading} class="Btn h38x" />
            </Box>
         </div>
      </div>
   )
}

export const AuditHomePage = (props) => {
   const [btnloading, setBtnloading] = useState(false);

   useEffect(() => {
      if (props.open) {
         setBtnloading(false)
      }
   }, [props.open]);

   const confirmHome = () => {
      setBtnloading(true)
      props.confirmHome()
   };

   return (
      <div className="px-4 keyword-delete">
         <div className="pb-4 f20x"> You haven't specified any specific URL/Slug in the input field. </div>
         <div className="pb-2 f15x lh22x text-justify"> Would you like to run the audit for the home page?</div>
         <div className="pb-4 d-flex flex-wrap justify-content-end">
            <Box
               className="addButton pt-3 m-r15"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto", color: 'var(--ink-3)' }}
            >
               <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn h38x" noIcon="d-none"></AppButton>
            </Box>
            <Box
               className="addButton pt-3"
               sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto" }}
            >
               <AppButton noIcon="d-none" value="Confirm" color="primary" onclick={confirmHome} loading={btnloading} disabled={btnloading} class="Btn h38x" />
            </Box>
         </div>
      </div>
   )
}

// PAGE AUDIT ENDS //

// GENERATE CLUSTER POP UP //
function ClusterRange(props) {
   return (
      <>
         <ModalBox className='dark pt-1' open={props.clusterOpen} title={'Range Cluster'} onClose={props.handleClusterClose} noIcon="d-none">
            <form onSubmit={props.handleContinue} autoComplete="on">
               <div className="p-3">
                  <Text class="f14x">
                     Input the maximum number of keywords allowed in the cluster (minimum value: 10)
                  </Text>
                  <div className="py-3">
                     {/* <InputLabel className="f14x text-white p-b5">Select range</InputLabel> */}
                     <TextField
                        className={props.classname}
                        error={props.error}
                        value={props.tlCl}
                        // value = {props.ttlCl.current.value}
                        // ref={props.ttlCl}
                        // onChange={e=>props.setTlCl(e.target.value)}
                        onChange={props.changeRef}
                        id="outlined-basic"
                        type="number"
                        variant="outlined"
                        autoComplete='off'
                        fullWidth
                        InputProps={{
                           inputProps: {
                              max: props.inputMax
                           }
                        }}
                     />
                     {props.error ?
                        <div className="redClr f12x m-t5">Minimum Cluster value is set to 10</div>
                        :
                        null
                     }
                  </div>
                  <div className="d-flex justify-content-between align-items-center">
                     {!props.error ?
                        <div className="f13x">At least {props.tlKwrds} clusters will be generated depending on the number of keywords.</div>
                        :
                        <div></div>
                     }
                     <AppButton type="submit" value="Continue" class="w-25"
                     // onclick={props.handleContinue}
                     />
                  </div>
               </div>
            </form>
         </ModalBox>
      </>
   )
}
export default React.memo(ClusterRange);
// GENERATE CLUSTER POP UP //

export const CGARemapModal = ({ ...props }) => {

   const [btnloading, setBtnloading] = useState(false);
   const [competitorURLErr, setCompetitorURLErr] = useState('');
   const [remapURL, setRemapURL] = useState('');

   useEffect(() => {
   }, [props.competitorURLs, props.searching]);


   const handleRemap = () => {
      if (remapURL) {
         props.handleRemap(remapURL)
      }
   }

   return (
      <Modal className="" open={props.openRemapModal} onClose={props.handleClose} closeAfterTransition
         aria-labelledby="modal-modal-title" aria-describedby="modal-modal-description">
         <Fade in={props.openRemapModal} {...(props.openRemapModal ? { timeout: 750 } : { timeout: 1000 })}>
            <Box className="wd-modal-box add-popup add-modal-width" >
               <header className="add-modal-width-pad">
                  <div className="popup-button-div">
                     <Button onClick={props.handleClose} className="wd-CloseButton popup-close">
                        <svg id="Component_69_46" data-name="Component 69 – 46" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
                           <path id="Path_410" data-name="Path 410" d="M13.4,12l6.3-6.3a.99.99,0,0,0-1.4-1.4L12,10.6,5.7,4.3A.99.99,0,0,0,4.3,5.7L10.6,12,4.3,18.3A.908.908,0,0,0,4,19a.945.945,0,0,0,1,1,.908.908,0,0,0,.7-.3L12,13.4l6.3,6.3a.967.967,0,0,0,1.4,0,.967.967,0,0,0,0-1.4Z"
                              transform="translate(-4 -4)" fill="#0a0a0a" />
                        </svg>
                     </Button>
                  </div>
                  <div className="d-flex align-items-center justify-content-between popup-head">
                     <div>
                        <Title className="wd-history-title">Remap URL</Title>
                        <Para className="wd-history-sub-title mb-0">Match your URL with Competitor URL
                        </Para>
                     </div>
                  </div>
                  <form fullWidth className='m-t15' autoComplete="off" >
                     <div className="m-b20 forms intent-input page_audit_div">
                        <CGARemapModalSearch className="page_audit_search" selectedRows={props.selectedRows} competitorURLs={props.competitorURLs} handleNewSearch={props.handleNewSearch} searching={props.searching} setRemapURL={setRemapURL} />
                        {competitorURLErr && <FormHelperText className="Mui-error">{competitorURLErr}</FormHelperText>}
                     </div>
                     <div className="popup-button m-t10">
                        <Button onClick={props.handleClose} className="modal-cancel-button" data-dismiss="modal">Cancel</Button>
                        <AppButton noIcon="d-none" value="Remap" color="primary" onclick={handleRemap} loading={btnloading} disabled={btnloading} />
                     </div>
                  </form>
               </header>
            </Box>
         </Fade>
      </Modal>
   )
}
