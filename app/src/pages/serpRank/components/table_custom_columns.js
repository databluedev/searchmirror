import React, { useState, useEffect } from "react";
import { TableColumnIcon, DragDropIcon } from "../../commonComponents/icons";
import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import axios from 'axios';
import { MenuList, ClickAwayListener, Checkbox, FormControlLabel } from "@mui/material";
import { AppButton } from "../../commonComponents/parts";
import { Button } from "@/components/ui/button";
// import PopupState, { bindTrigger, bindMenu } from 'material-ui-popup-state';

import { DragDropContext, Droppable, Draggable } from "@hello-pangea/dnd";

const header_obj = { "brk": 'Best', "1d": '1d', "7d": '7d', "15d": '15d', "fts": 'SERP', "aio": 'AI Overview', "tg": 'Tags', "dt": 'Date',"clks": 'Clicks',"imps": 'Impressions' };
const elements = ["brk","1d", "7d", "15d","fts","aio","tg","dt"]

/* Columns this menu must not offer, because the table has no column to show
   for them:
     sv    "Volume" -- search volume has no provider on this product, so
           data_table.js has no sv column at all. The checkbox was in the menu,
           took a click, saved a preference and changed nothing on screen.
     clks  Search Console clicks and impressions, when the instance has no
     imps  Google OAuth client configured. There is no way for those numbers to
           exist, so offering the columns promises data that cannot arrive.
   `items` is the drag-reorderable list the menu shows, so the hidden keys are
   kept out of it -- @hello-pangea/dnd indexes against the array it rendered,
   and filtering at render time while splicing the unfiltered array would drag
   the wrong column. They are merged back on save (see columnsOrder), because
   `items` is also what Apply writes to the stored preference: dropping a key
   there would delete it, and an instance that later configures a GSC client
   would have no way to switch those columns back on. */
const hiddenColumns = () => (
   global.gscClientId ? ["sv"] : ["sv", "clks", "imps"]
);

// `order` is the visible list; anything the menu hides keeps its stored value
// and is appended, so a round-trip through Apply never drops a column.
const columnsOrder = (data, order) => {
   var result = {}
   order.forEach((key) => {
      result[key] = data[key]
   })
   Object.keys(data).forEach((key) => {
      if (!(key in result)) {
         result[key] = data[key]
      }
   })
   return result
}


function TableCustomColumns(props) {

	const [open, setOpen] = React.useState(false);
	const [tableheaderlst, setTableheaderlst] = useState({});
  	const [projectage, setProjectage] = useState(0);

	const [applyallproject, setApplyallproject] = useState(false);
	const [btnloading, setBtnloading] = useState(false);

	const [items, setItems] = useState(elements);

	const onDragEnd = (result) => {
	   const newItems = Array.from(items);
	   const [removed] = newItems.splice(result.source.index, 1);
	   newItems.splice(result.destination.index, 0, removed);
	   setItems(newItems);
	};

	useEffect(() => {
		setTableheaderlst(props.lsttblhdlst);
		setItems(Object.keys(props.lsttblhdlst).filter((key) => !hiddenColumns().includes(key)));
		setProjectage(props.projectage)
		setApplyallproject(false);
	
	// eslint-disable-next-line react-hooks/exhaustive-deps
	},[props.lsttblhdlst]);

	const tblhdUpdate = () =>{
		setBtnloading(true)
		setOpen(false);

		// props.tablehdUpdate(tableheaderlst);
		const col_order = columnsOrder(tableheaderlst, items)
		props.tablehdUpdate(col_order);
	    // this.setState({ lsttblhdlst: tableheaderlst, tblHdFltrMenuVsbl: false })
	    const cookies = new Cookies(); 
	    const userid = cookies.get('session_userid');
	    const usertoken = cookies.get('session_token')
	    const grpid = cookies.get('activegrp'); 
	    if(userid && grpid ){

	        var data = {
	           'userid': userid,
	           'grpid': grpid,
	           'tblvw': col_order,
	           'alpjt': applyallproject,
	        };

	        axios.post(global.apiurl + '/tablecolumsupdate', data, {
	            headers: {'Authorization': 'Token '+ usertoken }
	        }).then(response => {
	            return response.data;
	        }).then(res => {
	            if(res.status !== "true") {
	                const msg = res.message;
	                toast.error(msg)  
	            } else {
	                // this.setState({tblhdlst: [...tableheaderlst,"alpjt"] });
	                toast.success('Table columns update successfully.'); 
	                // cookies.set('__sp_lst_tbl_cmn__', tableheaderlst, { path: '/', maxAge: global.cookiesexpire });
	            }
	            setBtnloading(false)
	        });
	    }
	}

	const tableHdFilterFun = (e) => {
		// if(!tableheaderlst.includes(e.target.value)){
		// 	setTableheaderlst([...tableheaderlst, e.target.value])
		//     // this.setState({ tableheaderlst: [...tableheaderlst, e.target.value] })
		// }else{
		//    const hdlist = tableheaderlst.filter(hd => hd !== e.target.value);
		//    setTableheaderlst(hdlist)
		//    // this.setState({ tblhdlst: hdlist })
		// }

		// if(tableheaderlst[e.target.value]){
		if(tableheaderlst.hasOwnProperty(e.target.value)){
			setTableheaderlst({...tableheaderlst, [e.target.value]: Number(!tableheaderlst[e.target.value]) })
		}
	}


	const handleClick = () => {
	   setOpen((prev) => !prev);
	};

	const handleClickAway = () => {
	   setOpen(false);
	};

	return (
		<ClickAwayListener mouseEvent="onMouseDown" touchEvent="onTouchStart" onClickAway={handleClickAway} >
            <div className="actionToggleIcon">
				<Button variant="secondary" onClick={handleClick} className="w-full borderBtn darkgray"><span className="d-flex m-r10"><TableColumnIcon className="" /></span><span>Column</span></Button>

				{open ? (
				   <div className={"normalToggleList table-header-list ExportList"}>
				      	<MenuList className="minW180x">
	      		    		<div>
	      		    			<div className="scroll maxh320x p-b5 brdBottom">
	      							<FormControlLabel className="d-flex m-0 p-l15" control={<Checkbox name="lstHdrfilter" value="kw" checked />} label="Keyword" disabled />
	      							<FormControlLabel className="d-flex m-0 p-l15" control={<Checkbox name="lstHdrfilter" value="rnk" checked />} label="Rank" disabled />

						      		<DragDropContext onDragEnd={onDragEnd}>
					      		      <Droppable droppableId="droppable">
					      		        {(provided) => (
					      		          <div {...provided.droppableProps} ref={provided.innerRef}>
					      		            {items.map((item, index) => (
		  												((parseInt(projectage) > 1 || item !== '1d') && (parseInt(projectage) > 7 || item !== '7d') && (parseInt(projectage) > 15 || item !== '15d') ) ?
						      		              	<Draggable key={item} draggableId={item} index={index}>
						      		                	{(provided, snapshot) => (
							      		               	<div
						      		               	      ref={provided.innerRef}
						      		               	      snapshot={snapshot}
						      		               	      {...provided.draggableProps}
						      		               	      {...provided.dragHandleProps}
						      		               	    >
							  								<div className="d-flex align-items-center p-l10">
							  								<DragDropIcon />
							  								<FormControlLabel className="d-flex m-0 w-100" control={<Checkbox name="lstHdrfilter" value={item} checked={Boolean(tableheaderlst[item])} onChange={tableHdFilterFun} />} label={header_obj[item]} />
						      		               	   		</div>
						      		               	   </div>
						      		                	)}
						      		              	</Draggable>
		  												: null
					      		            ))}
					      		          </div>
					      		        )}
					      		      </Droppable>
					      		   </DragDropContext>

				      			{/*<div className="scroll maxh320x p-b5 brdBottom">
				  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="kw" checked />} label="Keyword" disabled />
				  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="rnk" checked />} label="Rank" disabled />
				  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="brk" checked={tableheaderlst.includes('brk')} onChange={tableHdFilterFun} />} label="Best" />
				  						{parseInt(projectage) > 1 ?
				  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="1d" checked={tableheaderlst.includes('1d')} onChange={tableHdFilterFun} />} label="1d" />
				  						: null}
				  						{parseInt(projectage) > 7 ?
				  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="7d" checked={tableheaderlst.includes('7d')} onChange={tableHdFilterFun} />} label="7d" />
				  						: null}
				  						{parseInt(projectage) > 15 ?
				  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="15d" checked={tableheaderlst.includes('15d')} onChange={tableHdFilterFun} />} label="15d" />
				  						: null}
				  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="fts" checked={tableheaderlst.includes('fts')} onChange={tableHdFilterFun} />} label="SERP" />
				  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="sv" checked={tableheaderlst.includes('sv')} onChange={tableHdFilterFun} />} label="Volume" />
				  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="tg" checked={tableheaderlst.includes('tg')} onChange={tableHdFilterFun} />} label="Tags" />
				  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="dt" checked={tableheaderlst.includes('dt')} onChange={tableHdFilterFun} />} label="Date" />
				      			</div>*/}

				      			</div>
				      		  	
			  						{/*<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" value="alpjt" checked={tableheaderlst.includes('alpjt')} onChange={tableHdFilterFun} />} label="Apply all projects" />*/}
			  						<FormControlLabel className="d-flex m-0" control={<Checkbox name="lstHdrfilter" className="chk_apply_span" value="alpjt" checked={applyallproject} onChange={(e)=> {setApplyallproject(!applyallproject)} }  />} label="Apply to all projects" />
                				<div className="d-flex justify-content-center align-items-center mt-2">
				      		  		{/*<AppButton value="Apply" noIcon="d-none" class="md maxW150x" loading={btnloading} onclick={tblhdUpdate} disabled={JSON.stringify(props.lsttblhdlst) === JSON.stringify(tableheaderlst) ? true : false } />*/}
				      		  		<AppButton value="Apply" noIcon="d-none" class="md maxW150x" loading={btnloading} onclick={tblhdUpdate} />
				      			</div>
				      		</div>
		      	      	</MenuList>
		      	   </div>
		      	) : null}
            </div>
        </ClickAwayListener>
	);
}
export default TableCustomColumns;
