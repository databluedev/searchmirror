import React, { useState } from "react";
import { DeleteIcon } from "../../commonComponents/icons";
import { toast } from 'react-toastify';
import { Tooltip, Zoom, IconButton } from "@mui/material";
import {ModalBox, ProjectDelete, KeywordDelete } from "../../commonComponents/Modals";

function KWDelete(props) {

	const [open, setOpen] = useState(false);
	const handleOpen = () => setOpen(true);
	const handleClose = () => setOpen(false);
	
	const emptyDelete = () => { 
	  toast.warning("To delete, select at least one keyword")
	}

	return (
		<>
			{/* Icon-only, so it carries its own accessible name (DESIGN.md
			    "Button"). AppIconButton drops unknown props and cannot take
			    one, hence IconButton directly -- same element, same classes.
			    `dangerIcon` is the destructive treatment in _data.scss. */}
			{ (props.selectedRowIds && props.selectedRowIds.length > 0) ?
				<Tooltip classes={{ tooltip: "Tltpsmall text-center" }} title={props.kwtype !== "kwoverview" ? "Delete the selected keywords" : "Delete this keyword"} placement="top" TransitionComponent={Zoom} >
				    <div>
				    <IconButton
				    	onClick={handleOpen}
				    	aria-label={props.kwtype !== "kwoverview" ? "Delete the selected keywords" : "Delete this keyword"}
				      	className={"messageIcon dangerIcon "+ (props.kwtype !== "kwoverview" ? "kwselect" : "")}
				    >
				      	<DeleteIcon />
				    </IconButton>
				    </div>
	            </Tooltip>
            :
            	<IconButton
            		onClick={emptyDelete}
            		aria-label="Delete keywords"
            	  	className={"messageIcon"}
            	>
            	  	<DeleteIcon />
            	</IconButton>
			}

            <ModalBox title="" onClose={handleClose} open={open} >
            	{ props.basedata.kw_c === props.selectedRowIds.length ? 
              		<ProjectDelete pid={props.basedata.GY} modalClose={handleClose} updatefullpage={props.updatefullpage} />
            	:
	    			<KeywordDelete selectedRowIds={props.selectedRowIds} modalClose={handleClose} updatefullpage={props.updatefullpage} />
	    		}
            </ModalBox>            
        </>
	);
}
export default KWDelete;