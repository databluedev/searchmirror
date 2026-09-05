import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";


function KeywordSearch(props) {

	const searchInptRef = React.useRef(null);
   const [searchVal, setSearchVal] = useState("");
   const [tablefullresult, setTblfulrslt] = useState({});


	useEffect(() => {
		setTblfulrslt(props.tablefullresult)
		setSearchVal("")
		searchInptRef.current.value = '';
	},[props.tablefullresult]);

	function listkwsearchFuc (e) {	   
	   if ((e.key === "Enter" || e.charCode === 13) && searchVal !== e.target.value){
	   	setSearchVal(e.target.value)
	      props.keydataUpdate(tablefullresult.filter(
	        item =>
	          JSON.stringify(item.KW)
	            .toLowerCase()
	            .indexOf(e.target.value.toLowerCase()) !== -1
	      )); 
	   }else if(e.target.value === "" && searchVal !== e.target.value){
	   	setSearchVal("")
	      props.keydataUpdate(props.tablefullresult);
	   }

	}

	return (
		<div className="search">
		   <Input
		      type="search"
		      id="outlined-basic"
		      ref={searchInptRef}
		      placeholder="Search"
		      onChange={listkwsearchFuc}
		      onKeyPress={listkwsearchFuc}
		      autoComplete="off"
		   />

		</div>
	);
}
export default KeywordSearch;