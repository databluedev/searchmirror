import React, { useEffect, useState, useCallback } from "react";
import TrendingWidget from "./grid_single_table"; 
import EmptyTable from "./gridTableComponents/empty_table";
import { Grid } from "@mui/material";
import "./style.scss";

export default function GrdDataTable({...props }) {
   const [gridCheckedTag, setGridCheckedTag] = useState(""); 


	useEffect(() => {
      setGridCheckedTag("");

      // eslint-disable-next-line react-hooks/exhaustive-deps
	}, [props.grdfullresult]);

  const handleRowSelected = useCallback(state => {

      var checkedListAll = state.selectedRows.map((row) => row.key.toString().split("~")[0]);
      var tagid = state.selectedRows.length > 0 ? state.selectedRows[0].key.toString().split("~") : ['0',""]
      if(tagid.length > 1 && gridCheckedTag !== tagid[1]){
        setGridCheckedTag(tagid[1]);
      }else{
        setGridCheckedTag("");
      }
      
      props.GridCheckedListUpdate(checkedListAll) ;
      // eslint-disable-next-line react-hooks/exhaustive-deps 
   }, []);


	return (
    	<>
    		<div className="px-0">
    		   {/* One card per row. Two half-width cards put a 29-keyword table in a
    		       486px column and left the one-keyword card beside it as dead space. */}
    		   <Grid container spacing={3} className="projectSection">
               { (Object.keys(props.grdtblfltrresult).length > 0 && props.grdtblfltrresult['tagkeys']) ?
                  <>
                  { props.grdtblfltrresult['tgin'] === 1 ?
                     <Grid item xs={12}>
                        <EmptyTable grdtbltype={props.grdtbltype} />
                     </Grid>
                  :
                     props.grdtblfltrresult['tagkeys'].map((tagname,i) => ( 
                        <Grid item xs={12} key={i}>
                           <TrendingWidget tag={{'name': tagname, 'key': i}} filteredresult={props.grdtblfltrresult} grdfullresult={props.grdfullresult} tableUpdate={props.tableUpdate} tabledataUpdate={props.tabledataUpdate} handleRowSelected={handleRowSelected} selectedRowIds={props.selectedRowIds} updatefullpage={props.updatefullpage} gridCheckedTag={gridCheckedTag} grdtbltype={props.grdtbltype} keywordpageroute={props.keywordpageroute} canSelectKeywords={props.canSelectKeywords} />
                        </Grid>
                     )) 
                  }
                  </>
             	:
                  <>
                     <Grid item xs={12}>
                       <TrendingWidget tag={{'key': 101}}  />
                     </Grid>

                     <Grid item xs={12}>
                        <TrendingWidget tag={{'key': 102}} />
                     </Grid>
                  </>
               }
    		   </Grid>
    		</div>
      </>
   );
}
