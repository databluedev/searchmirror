import React, { useEffect } from "react";
import { ListViewIcon, GridViewIcon } from "../../commonComponents/icons";
import Cookies from 'universal-cookie';
// import { toast } from 'react-toastify';
import axios from 'axios';
import { ToggleButton, ToggleButtonGroup } from "@mui/material";
// import { AppButton } from "../../commonComponents/parts";

function TableViewToggle(props) {

	const [tableview, setTableview] = React.useState('L');

	useEffect(() => {
		setTableview(props.tableview);

	},[props.tableview]);

	const handleChange = (event, view) => {
		if(view !== null){
		    setTableview(view);
			props.tableviewUpdate(view);
		    // this.setState({ lsttblhdlst: tableheaderlst, tblHdFltrMenuVsbl: false })
		    const cookies = new Cookies(); 
		    const userid = cookies.get('session_userid');
		    const usertoken = cookies.get('session_token')
		    const grpid = cookies.get('activegrp'); 
		    if(userid && grpid ){

		        var data = {
		           'userid': userid,
		           'grpid': grpid,
		           'view': view,
		        };

		        axios.post(global.apiurl + '/dashboard_view_change', data, {
		            headers: {'Authorization': 'Token '+ usertoken }
		        }).then(response => {
		            return response.data;
		        }).then(res => {
		            if(res.status !== "true") {
		                // const msg = res.message;
		                // toast.error(msg)  
		            } else {
		            	// var data = props.projectList.map((item, i) => item.GY === parseInt(grpid) ? {...item, 'd_v': view+'~T'} : item)
		            	// props.baseauthdataUpdate(data);
		                // this.setState({tblhdlst: [...tableheaderlst,"alpjt"] });
		                // toast.success('Table columns update successfully.'); 
		                // cookies.set('__sp_lst_tbl_cmn__', tableheaderlst, { path: '/', maxAge: global.cookiesexpire });
		            }
		        });
		    }
		}
	}

	return (
	    <ToggleButtonGroup
	      color="primary"
	      className="listaGrid h43x"
	      value={tableview}
	      exclusive
	      onChange={handleChange}
	    >
	      <ToggleButton size="small" value="L">
	      	<ListViewIcon className="m-l8" />
	      	<span className="p-l10 p-r5 f14x"> List </span>
	      </ToggleButton>
	      <ToggleButton size="small" value="G">
	      	<GridViewIcon className="m-l5" />
	      	<span className="p-r10 p-l10 f14x"> Grid </span>
	      </ToggleButton>
	    </ToggleButtonGroup>
	);
}
export default TableViewToggle;