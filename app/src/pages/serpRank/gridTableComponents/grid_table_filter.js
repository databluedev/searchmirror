import React, { useState, useEffect,  } from "react";
// import LoadingBar from "react-top-loading-bar";
// import Cookies from 'universal-cookie';
// import { toast } from 'react-toastify';
// import axios from 'axios';

import ClickAway from "../../commonComponents/click_away";
import { MenuItem } from "@mui/material";
import { AppIconButton } from "../../commonComponents/parts";
import { FilterIcon, TagIcon } from "../../commonComponents/icons";


function GridTblFilter(props) {

	const [gridtype, setGridtype] = useState('tag');

	// const [open, setOpen] = useState(false);
	
	useEffect(() => {
      // var grid_sort_key = Object.keys(grid_sort_obj).find(key => grid_sort_obj[key] === grdtbltype);
		setGridtype(props.grdtbltype);

	},[props.grdtbltype]);

	const gridtype_chng = (grdtype,grdTag) => {
	    if (gridtype !== grdtype){
	    		setGridtype(grdtype);
	         props.gridUpdate('L',grdtype,grdTag);
	         // var data = props.projectList.map((item, i) => item.GY === parseInt(grpid) ? {...item, 'd_v': view+'~T'} : item)
	    }
	}

	return (
		<>
         <ClickAway 
            childclassName="ExportList" 
			parent={ <AppIconButton	class={"messageIcon"} Icon={<FilterIcon color="var(--ink-3)"/>} /> }
         >
            <MenuItem className={gridtype === "tag" ? "primaryActive" : "primaryHover"} onClick={() => gridtype_chng('tag','T')} >
              	<div className="d-flex justify-content-between align-items-center">
              		<TagIcon />
              	   <div className="m-r20 m-l10"> Tags </div>
              	</div>
            </MenuItem>
            <MenuItem className={gridtype === "region" ? "primaryActive" : "primaryHover"} onClick={() => gridtype_chng('region','R')} >
              	<div className="d-flex justify-content-between align-items-center">
              		<TagIcon />
              	   <div className="m-r20 m-l10"> Region </div>
              	</div>
            </MenuItem>
            <MenuItem className={gridtype === "device" ? "primaryActive" : "primaryHover"} onClick={() => gridtype_chng('device','D')} >
              	<div className="d-flex justify-content-between align-items-center">
              		<TagIcon />
              	   <div className="m-r5 m-l10"> Device </div>
              	</div>
            </MenuItem>

         </ClickAway> 
      </>
	);
}
export default GridTblFilter;