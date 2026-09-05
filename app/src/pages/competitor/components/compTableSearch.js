import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";
import Cookies from 'universal-cookie';
import axios from 'axios';


function COMPTableSearch(props) {

	const searchInptRef = React.useRef(null);
   const [searchVal, setSearchVal] = useState("");
   // const [tablefullresult, setTblfulrslt] = useState({});


	useEffect(() => {
		// setTblfulrslt(props.fullComp)
		setSearchVal("")
		searchInptRef.current.value = '';
	},[props.fullComp]);

	function listkwsearchFuc (e) {
	   
	   if ((e.key === "Enter" || e.charCode === 13) && searchVal !== e.target.value){
	   	setSearchVal(e.target.value)
		   // console.log('////////////////////////',e.target.value)
         // const filterDatas = Object.keys(tablefullresult)
         //    .filter((key) => key.includes(e.target.value))
         //    .reduce((obj, key) => {
         //       return Object.assign(obj, {
         //          [key]: tablefullresult[key]
         //       });
         // }, {});
         // props.compdataUpdate(filterDatas)


         props.compdataUpdate({},true)
         const cookies = new Cookies();
         const usertoken = cookies.get('session_token')
         const userid = cookies.get('session_userid')
         const grpid = cookies.get('activegrp');

         var data = {
            'userid': userid,
            'grpid': grpid,
            'search': e.target.value,
         };
         axios.post(global.apiurl + '/compai/competitorslist', data, {
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data;
         }).then(res => {
            if(res.st !== 1){
            	// failed
            }else {
         		props.compdataUpdate(res.Cl)
            }
         }).catch((error) => {
            // history.push("/")
         });

	      
	   }else if(e.target.value === "" && searchVal !== e.target.value){
	   	setSearchVal("")
	      props.compdataUpdate(props.fullComp);
	   }

	}

	return (
		<div className={`search topCompSearch ${props.pageType && props.pageType === "modal"? "" : "m-b20"}`}>
		   <Input
		      type="search"
		      id="outlined-basic"
		      ref={searchInptRef}
		      placeholder={props.tcc ? "Search among "+(props.tcc)+" competitors" : "Search"}
		      onChange={listkwsearchFuc}
		      onKeyPress={listkwsearchFuc}
		      autoComplete="off"
		   />

		</div>
	);
}
export default COMPTableSearch;