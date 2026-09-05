import React, { useState, useEffect } from "react";
import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import axios from 'axios';
import { Input } from "@/components/ui/input";


function SRTableSearch(props) {

	const searchInptRef = React.useRef(null);
   const [searchVal, setSearchVal] = useState("");
   const [tablefullresult, setTblfulrslt] = useState({});
//    const [filteredresult, setfilteredresult] = useState({});


	useEffect(() => {
		setTblfulrslt(props.tablefullresult)
		setSearchVal("")
		searchInptRef.current.value = '';
	},[props.tablefullresult, props.tableview]);

	function listkwsearchFuc (e) {
	   
	   if ((e.key === "Enter" || e.charCode === 13) && searchVal !== e.target.value){
	   	setSearchVal(e.target.value)
	      props.tabledataUpdate(tablefullresult.filter(
				item =>
					JSON.stringify(item.KW)
						.toLowerCase()
						.indexOf(e.target.value.toLowerCase()) !== -1
	      )); 
	   }else if(e.target.value === "" && searchVal !== e.target.value){
	   	setSearchVal("")
	      props.tabledataUpdate(tablefullresult);
	   }

	}

	function gridkwsearchFun (e) {
	   
	   if ((e.key === "Enter" || e.charCode === 13) && searchVal !== e.target.value){

	      const value = typeof(e) === "string" ? e : e.target.value
	   	setSearchVal(value);
         props.tabledataUpdate([]);
         const cookies = new Cookies(); 
         const userid = cookies.get('session_userid');
         const usertoken = cookies.get('session_token');
         const grpid = cookies.get('activegrp'); 
         if(userid && grpid ){
            var data = {
               'userid': userid,
               'grpid': grpid,
               'grdSValue': value,
               'gridtype': "tag",
            };
            axios.post(global.apiurl + '/gridauth', data, {
                 headers: {'Authorization': 'Token '+ usertoken }
            }).then(response => {
                 return response.data;
            }).then(res => {

               if(res.status !== "true") {
                  toast.error(res.message)  
               } else if(res.results) {
                  // gridResults
                  props.tabledataUpdate(res.results[0]);
               }
            });
	      }
	   }else if(e.target.value === "" && searchVal !== e.target.value){
	      props.tabledataUpdate([]);
	   	setSearchVal("");
	      setTimeout(() => {          
	         props.tabledataUpdate(tablefullresult);
	      }, 500);
	   }
	}

	return (
		<div>
		   <Input
		      type="search"
		      className="search"
		      id="outlined-basic"
		      ref={searchInptRef}
		      placeholder="Search"
		      // value={searchVal}
		      // onChange={listsearchfilter}
		      onChange={props.tableview === 'G' ? gridkwsearchFun : listkwsearchFuc}
		      // onChange={(e)=> setSearchVal(e.target.value)}
		      // onSearch={(e) => kwsearchFunc.current(e)}
		      // onPressEnter={(e) => kwsearchFunc.current(e)}
		      // onChange={(e) => e.target.value === "" ? kwsearchFunc.current(e) : null}
		      // onKeyPress={(e) => kwsearchFunc.current(e)}
		      onKeyPress={props.tableview === 'G' ? gridkwsearchFun : listkwsearchFuc}
		      // onKeyPress={listsearchfilter}
		      // onSearch={searchfilter}
		      autoComplete="off"
		      aria-label="Search keywords"
		   />

		</div>
	);
}
export default SRTableSearch;