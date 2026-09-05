import React, { useState } from "react";

import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import axios from 'axios';
import { AppButton } from "../../commonComponents/parts";
import {ModalBox, KeywordDelete } from "../../commonComponents/Modals";


function KWTypoerror(props) {

	const [open, setOpen] = useState(false);
	// const handleOpen = () => setOpen(true);
	const handleClose = () => setOpen(false);

	const [fixbtnloading, setFixBtnloading] = useState(false);
	const [ignrbtnloading, setIngrBtnloading] = useState(false);
	const [typokwid, setTypokwid] = useState(0);

	const typoerrorfixbtn = (kwid, action) =>{
	    const cookies = new Cookies();
	    const userid = cookies.get('session_userid');
	    const usertoken = cookies.get('session_token')
	    const grpid = cookies.get('activegrp');


		if (action==="fix") { 
			setFixBtnloading(true) 
		}else{
			setIngrBtnloading(true)
		}
	    var split_key = kwid.toString().split('~');
	    var typoid = split_key[0];
	    setTypokwid(typoid)

	    // if(type === "fix"){
	    //     this.setState({exportpdfurl:"", exportcsv:[], exporttxt:[], });
	    // }


	    // var typoid = e.target.getAttribute("data-typoerrorfixbtn");
	    // if(this.state.showgrid) {
	    //     var split_key = typoid.split('~');
	    //     typoid = split_key[0];
	    // }
	    // var type = e.target.getAttribute("data-type");

	    if(userid && typoid) { 
	        const data = {
	            'userid': userid,
	            'grpid': grpid,
	            'keyid': typoid,
	            'action': action,
	        };
	        axios.post(global.apiurl + '/typoerrorfix', data, {
	        // headers: {'Authorization': global.token}
	        headers: {'Authorization': 'Token '+ usertoken}
	        }).then(response => {
	            return response.data;
	        }).then(res => {
	            const msg = res.message;
	            if(res.status !== "true"){
	                if(msg === "Keyword already exists"){
	                    //         title: 'This keyword already exists on this ('+this.state.groupname+') project. shall I delete this keyword?',
	                	setOpen(true)
	                }else{
	                    toast.error("something went wrong")
	                    // this.setState({errfixloading : false});   
	                }
	                
	            } else {
	            //     this.UNSAFE_componentWillMount(); 
	            //     this.componentDidMount(); 
	                if(msg === "Error Ignored"){
	                    toast.success("Keyword Error Ignored")
	                }else{
	                    toast.success("Keyword Error Fixed")
	                }
         			props.tableUpdate()

	                // setTimeout(() => {
	                // }, 1500);
	            }
				setFixBtnloading(false)
				setIngrBtnloading(false)
	        }).catch(err => {
	    		setFixBtnloading(false)
	    		setIngrBtnloading(false)
	            setOpen(false)
	        });
	    
	    }
	    
	}

	return (
		<div>
		  	<p className="m-b5">
			    <span className="lh20x f13x">{"Typo error! '"}</span>
			    <span className="lh20x"><b>{props.row.kwas}</b></span>
			    <span className="lh20x f13x">{"' only available for SERP rank"}</span>
			  	<span className="smallButton contents">
			    <AppButton noIcon="m-0"	value="Fix"	class="py-0 px-2 m-l5 h24x f13x" onclick={()=> typoerrorfixbtn(props.row.key, "fix")} loading={fixbtnloading} disabled={ignrbtnloading} ></AppButton>
			    <AppButton class="secondaryBtn py-0 px-2 m-l5 h24x f13x" noIcon="m-0" value="Ignore" onclick={()=> typoerrorfixbtn(props.row.key, "ignore")} loading={ignrbtnloading} disabled={fixbtnloading}></AppButton>
			  </span>
		  	</p>

          	<ModalBox title="" onClose={handleClose} open={open} >
    			<KeywordDelete selectedRowIds={[typokwid]} modalClose={handleClose} updatefullpage={props.updatefullpage} content={"typoerror"} />
          	</ModalBox>
		</div>
	);
}
export default KWTypoerror;