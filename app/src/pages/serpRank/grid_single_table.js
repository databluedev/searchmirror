import React, { useState, useEffect } from "react";
import { SmallText, Tsk} from "../commonComponents/parts";
import {fstLtrCapitalfun} from "../common_fun";   

import TrendingTable from "./gridTableComponents/trending_table";
import ManageTagFullPage from "../commonComponents/manage_tag_full_page";


const loadingRowTemplate = { "RK": [], "RW": null, "RS": "never_checked", "SV": "init", "io": "", "PM": "", "kwas": "" }
const createLoadingRows = () => Array.from(
   { length: 5 },
   (_, index) => ({ ...loadingRowTemplate, key: `loading-${index}` })
)


function TrendingWidget({ children, ...props }) {

   const [dataRows, setDataRows] = useState(createLoadingRows);
   const [serpscore, setSerpscore] = useState(-1); 
   const [toggleCleared, setToggleCleared] = useState(false);

   useEffect(() => {   

      if(props.filteredresult && props.tag){
         setDataRows(props.filteredresult['tags'][props.tag.name] ? props.filteredresult['tags'][props.tag.name] : [])
         setSerpscore(props.filteredresult['tscr'][props.tag.name] ? props.filteredresult['tscr'][props.tag.name] : 0)
      }
   
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [props.filteredresult]);

   useEffect(() => {
      if(props.gridCheckedTag !== props.tag.name){
         setToggleCleared(!toggleCleared)
      }

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [props.gridCheckedTag]);

   return (
      dataRows.length > 0 ?
      <>
         <section className="gd-table">
            <div className="gd-table-header">

               <div className="header d-flex justify-content-between align-items-start gap-3">
                 <div className="gdHead__id">
                   <div className="gdHead__label">
                     { fstLtrCapitalfun(props.grdtbltype) }
                   </div>
                   <div className="gdHead__name">
                     { (!props.tag.name && props.tag.name !== 0) ?
                        <Tsk width={90} />
                     :
                        <span>
                          {fstLtrCapitalfun(props.tag.name)}
                          {(props.grdtbltype === "region" && dataRows.length > 0) ? <span className="gdHead__qualifier"> ({dataRows[0]['CY']})</span> : null}
                        </span>
                     }
                   </div>
                   <SmallText class="gdHead__count mb-0">
                     {(!props.tag.name && props.tag.name !== 0) ? <Tsk width={60} /> : dataRows.length + (dataRows.length === 1 ? " keyword" : " keywords")}
                   </SmallText>
                 </div>
                 <div className="gdHead__score" title="Search Visibility Score">
                   <div className="gdHead__label">Visibility</div>
                   <div className="gdHead__scoreValue">
                     {serpscore > -1 ? Math.round(serpscore) : <Tsk width={40} />}
                   </div>
                   <div className="gdHead__scoreDenom">out of 100</div>
                 </div>
               </div>

            </div>
            
            <TrendingTable toggleCleared={toggleCleared} grdresult={dataRows} grdfullresult={props.grdfullresult} tag={props.tag} tableUpdate={props.tableUpdate} tabledataUpdate={props.tabledataUpdate} handleRowSelected={props.handleRowSelected} selectedRowIds={props.selectedRowIds} updatefullpage={props.updatefullpage} keywordpageroute={props.keywordpageroute} canSelectKeywords={props.canSelectKeywords} />

            { (props.selectedRowIds && (props.selectedRowIds).length > 0 && props.gridCheckedTag === props.tag.name) ? 
               <ManageTagFullPage type="gridtable" managetagopenFunc={null} selectedRowIds={props.selectedRowIds} tableUpdate={props.tableUpdate}/>
            : null }
            
         </section>
      </>
      
      :  null 
   )
}

export default TrendingWidget;
