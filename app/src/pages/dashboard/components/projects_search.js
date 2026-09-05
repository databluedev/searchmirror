import React, { useState, useEffect } from "react";
import { Input } from "@/components/ui/input";

function ProjectSearch(props) {

	const searchInptRef = React.useRef(null);
   const [searchVal, setSearchVal] = useState("");
   const [tablefullresult, setTblfulrslt] = useState([]);

	useEffect(() => {
		setTblfulrslt(props.fulldata)
		setSearchVal("")
		searchInptRef.current.value = '';
	},[props.fulldata]);

	function listkwsearchFuc (e) {
	   if ((e.key === "Enter" || e.charCode === 13) && searchVal !== e.target.value){
	   	setSearchVal(e.target.value)

         props.dataUpdate(tablefullresult.filter(
            item =>
             	JSON.stringify(item)
               .toLowerCase()
               .indexOf(e.target.value.toLowerCase()) !== -1
         )); 
      }else if(e.target.value === "" && searchVal !== e.target.value){
        	setSearchVal("")
         props.dataUpdate(props.fulldata);
      }
	}

	return (
		<div className="search">
		   <Input
		      type="search"
		      id="outlined-basic"
		      ref={searchInptRef}
		      placeholder={"Search"}
		      // placeholder={props.tcc ? "Search among "+(props.tcc)+" competitors" : "Search"}
		      onChange={listkwsearchFuc}
		      onKeyPress={listkwsearchFuc}
		      autoComplete="off"
		   />

		</div>
	);
}
export default ProjectSearch;