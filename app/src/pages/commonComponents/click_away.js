import * as React from 'react';
// import Menu from '@mui/material/Menu';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import Box from '@mui/material/Box';
// import { SxProps } from '@mui/system';
import { Grow } from '@mui/material';
import MenuList from '@mui/material/MenuList';
// import Paper from '@mui/material/Paper';
import { MenuIcon } from "./icons";

function ClickAway({ children, ...props }) {
   const [open, setOpen] = React.useState(false);

   const handleClick = () => {
      setOpen((prev) => !prev);
   };

   const handleClickAway = () => {
      setOpen(false);
   };

   return (
      <>
         <ClickAwayListener
            mouseEvent="onMouseDown"
            touchEvent="onTouchStart"
            onClickAway={handleClickAway} 
         >
            <Box
               component={props.parent ? "span" : "button"}
               type={props.parent ? undefined : "button"}
               className="actionToggleIcon"
               aria-label={props.parent ? undefined : (props.label || "Widget actions")}
               aria-expanded={props.parent ? undefined : open}
               onClick={props.parent ? undefined : handleClick}
            >
               {props.parent ?
                  React.cloneElement(props.parent, {
                     onClick: handleClick,
                     "aria-label": props.label || "Open menu",
                     "aria-expanded": open,
                  })
                  : <MenuIcon width={14} height={props.height} />
               }
               
               {open ? (
            <Grow in={open} {...(open ? { timeout: 750 } : { timeout: 1000 })}> 
                  <Box className={"actionToggleList "+ (props.childclassName ? props.childclassName : " MenuIconlist")}>
                     <MenuList>
                         {children}
                     </MenuList>
                  </Box>
            </Grow>
               ) : null} 
            </Box>
         </ClickAwayListener>
      </>
   ); 
}
export default ClickAway;

export function ClickAwayI({ children, ...props }) {
   const [open, setOpen] = React.useState(false);

   const handleClick = () => {
      setOpen((prev) => !prev);
   };

   const handleClickAway = () => {
      setOpen(false);
   };
   return (
      <ClickAwayListener
         mouseEvent="onMouseDown"
         touchEvent="onTouchStart"
         onClickAway={handleClickAway}
      >
         {/* <Box className="actionToggleIcon" onClick={handleClick}> */}
         <Box onClick={handleClick} style={{ width: '33px', height: '32px', paddingLeft: '8px', paddingBottom: '1px', color:'white' }} className="d-flex align-items-center">{`+${(props.row.prjcts.length) - 6}`}
            {open ? (
               <Grow style={{maxHeight:'250px', overflow:'scroll'}} in={open} {...(open ? { timeout: 750 } : { timeout: 1000 })}>
                  <Box className={"actionToggleList " + (props.childclassName ? props.childclassName : " MenuIconlist")}>
                     <MenuList>
                        {
                           children
                        }
                     </MenuList>
                  </Box>
               </Grow>
            )
               : null}
         </Box>
      </ClickAwayListener>
   )
}
