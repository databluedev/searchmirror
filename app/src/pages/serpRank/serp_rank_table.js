import React, { useState, useEffect, useCallback } from "react";
import { useHistory } from "react-router-dom";
import { Tooltip, IconButton } from "@mui/material";
import "swiper/css";
import { ParaLg, Tsk } from "../commonComponents/parts";
import Cookies from 'universal-cookie';
import axios from 'axios';

import LstDataTable from "./data_table";
import GrdDataTable from "./grid_data_table";
import KWDelete from "./components/keyword_delete";
import GridTblFilter from "./gridTableComponents/grid_table_filter";
import ProjectFileExport from "./components/project_export";
import TableCustomColumns from "./components/table_custom_columns";
import SRTableSearch from "./components/serp_rank_table_search";
import TableViewToggle from "./components/table_view_toggle";
import { toast } from 'react-toastify';

import { RefreshIcon, TagIcon } from "../commonComponents/icons";
import RefreshBar from "../commonComponents/refresh_bar";
import { SerpLegend } from "./serp_features";
import { allowsTeamAction } from '../../utils/team_permissions';


const loadingRowTemplate = { "RK": [], "RW": null, "RS": "never_checked", "SV": "init", "io": "", "PM": "", "kwas": "" }
const createLoadingRows = () => Array.from(
   { length: 5 },
   (_, index) => ({ ...loadingRowTemplate, key: `loading-${index}` })
)
const grid_sort_obj = { "T": 'tag', "R": 'region', "D": 'device' };
// const listtbleheader = ["brk", "1d", "7d", "15d", "fts", "sv", "tg", "dt"]
// "sv" (search volume) is gone: there is no sv column in data_table.js to turn
// on, so it only ever put a dead checkbox in the Column menu. clks and imps
// stay in the default so an instance that configures a GSC client gets them,
// and are hidden by the table and the menu until it does.
const listtbleheader = { "brk": 1, "1d": 1, "7d": 1, "15d": 1, "clks": 1, "imps": 1, "fts": 1, "aio": 1, "tg": 1, "dt": 1 }

function SerpRankTable(props) {

   const history = useHistory();
   const [tableview, setTableview] = useState('L');
   const [grdtbltype, setGrdtbltype] = useState('tag');
   const [selectedRowIds, setSelectedRowIds] = useState([]);
   const canManageTags = allowsTeamAction(props.fullbasedata, "Keyword", "Manage Tag");
   const canRefreshKeywords = allowsTeamAction(props.fullbasedata, "Keyword", "Manual Refresh");
   const canDeleteKeywords = allowsTeamAction(props.fullbasedata, "Keyword", "Delete Keywords");
   const canSelectKeywords = canManageTags || canRefreshKeywords || canDeleteKeywords;

   const onRefreshTriggerFunc = React.useRef(null)
   const onRefreshCheckFunc = React.useRef(null)

   const [gridTableData, setGridTableData] = useState({ 'otg': [], 'grdfullresult': {}, 'grdtblfltrresult': {} });
   const [listTableData, setListTableData] = useState(() => {
      const loadingRows = createLoadingRows();
      return { 'age': 20, 'lth': listtbleheader, 'lstresult': loadingRows, 'lstfltrresult': loadingRows };
   });

   const cookies = new Cookies();
   const usertoken = cookies.get('session_token');
   const userid = cookies.get('session_userid');
   const grpid = cookies.get('activegrp');

   // Create a ref to the LstDataTable component
   const managetagopenFunc = React.useRef(null)

   // tableUpdate and gridUpdate call each other and are also invoked from user
   // handlers, so the requests are not owned by any one effect. One controller
   // for the whole component: unmounting aborts whatever is still in flight
   // instead of letting it resolve into setListTableData/setGridTableData.
   const abortRef = React.useRef(null)
   if (abortRef.current === null) {
      abortRef.current = new AbortController()
   }
   useEffect(() => () => abortRef.current.abort(), []);

   useEffect(() => {

      const loadingRows = createLoadingRows();
      setListTableData({ 'age': 20, 'lth': listtbleheader, 'lstresult': loadingRows, 'lstfltrresult': loadingRows })
      setGridTableData({ 'otg': [], 'grdfullresult': {}, 'grdtblfltrresult': {} })

      var tableview_split = props.basedata.d_v ? props.basedata.d_v.toString().split('~') : ['L', 'T'];
      setTableview(tableview_split[0]);
      setGrdtbltype(grid_sort_obj[tableview_split[1]])

      // const limit = (cookies.get('__sp_pg_lmt__') === "50" || cookies.get('__sp_pg_lmt__') === "100") ? cookies.get('__sp_pg_lmt__') : 50
      // const listtblhdlst = typeof(cookies.get('__sp_lst_tbl_cmn__')) !== "undefined" ? cookies.get('__sp_lst_tbl_cmn__') : [] 
      // setLsttblhdlst(listtblhdlst)

      if (tableview_split[0] === 'G') {
         gridUpdate(tableview_split[0], grid_sort_obj[tableview_split[1]])
      } else {
         tableUpdate(tableview_split[0]);
      }

      setSelectedRowIds([])

      const loaderTimeout = setTimeout(() => {
         global.PageTopLoader.current.complete();
      }, 1000);

      return () => clearTimeout(loaderTimeout);
      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [props.basedata]);


   const tabledataUpdate = (data) => {
      setListTableData(olddata => ({ ...olddata, 'lstresult': data, 'lstfltrresult': data }))
   }

   const tablefilterdataUpdate = (data) => {
      setListTableData(olddata => ({ ...olddata, 'lstfltrresult': data }))
   }

   const GrdtabledataUpdate = (data) => {
      setGridTableData(olddata => ({ ...olddata, 'grdfullresult': data, 'grdtblfltrresult': data }))
   }

   const GrdtablefilterdataUpdate = (data) => {
      setGridTableData(olddata => ({ ...olddata, 'grdtblfltrresult': data }))
   }

   const refreshPending = (rfs) => {
      if (rfs && rfs === "onk") {
         props.refresh_onUpdate(true);
      }
      if (rfs && (rfs === "onk" || rfs === "onv")) {
         if (typeof onRefreshCheckFunc.current === "function") {
            onRefreshCheckFunc.current(userid, grpid, rfs)
         }
      }
   }

   const refreshUpdate = (refreshSwt, status = "init") => {
      props.refresh_onUpdate(refreshSwt);
      if (status === "success") {
         props.updatefullpage()
         // if (tableview === 'G'){
         //    gridUpdate()
         // }else{
         //    tableUpdate();  
         // }
      }
   }

   /* List Table Result Updation */
   const tableUpdate = (tablevw = tableview) => {

      if (userid && grpid) {

         var data = {
            'userid': userid,
            'grpid': grpid,
            'field': "ranknow",
            'sort': "asc",
            'graph': "False",
            'limit': 50
         };
         axios.post(global.apiurl + '/dashservice', data, {
            headers: { 'Authorization': 'Token ' + usertoken },
            signal: abortRef.current.signal
         }).then(response => {
            return response.data;
         }).then(res => {
            if (res.st !== 1) {
               const msg = res.message;
               toast.error(msg)
            } else {

               if (res.results) {
                  // A saved order predates any column added since; spread it
                  // first so the user's order survives the new key.
                  var missing_defaults = Object.fromEntries(
                     Object.entries(listtbleheader).filter(([key]) => !(key in res.tnc))
                  )
                  var lstblth = Object.keys(res.tnc).length > 0 ? { ...res.tnc, ...missing_defaults } : listtbleheader
                  // setListTableData(olddata => ({...olddata, 'age': res.gA, 'lth': lstblth, 'lstresult': res.results.slice(0,10), 'lstfltrresult': res.results.slice(0,10)}))
                  setListTableData(olddata => ({ ...olddata, 'age': res.gA, 'lth': lstblth, 'lstresult': res.results, 'lstfltrresult': res.results }))
               }

               if (tablevw === 'L') {
                  // gridUpdate('G',grdtbltype)
                  gridUpdate('')
               } else {
                  refreshPending(res.mr);
                  if (selectedRowIds.length > 0) {
                     setSelectedRowIds([])
                  }
               }

            }

         }).catch((error) => {
            // history.push("/")
         });
      }
   }

   /* Grid Table Result Updation */
   const gridUpdate = (tablevw = tableview, gridtype = '', grdTag = '') => {

      if (userid && grpid) {
         var data = {
            'userid': userid,
            'grpid': grpid,
            'gridtype': gridtype
         };
         axios.post(global.apiurl + '/gridauth', data, {
            headers: { 'Authorization': 'Token ' + usertoken },
            signal: abortRef.current.signal
         }).then(response => {
            return response.data;
         }).then(res => {

            if (res.status !== "true") {
               toast.error(res.message)
            } else {
               // gridResults
               if (res.results) {
                  setGridTableData(olddata => ({ ...olddata, 'otg': res.unq, 'grdfullresult': res.results[0], 'grdtblfltrresult': res.results[0] }))
               }
               if (tablevw === 'L') {
                  setGrdtbltype(grid_sort_obj[grdTag])
               }
               if (tablevw === 'G') {
                  tableUpdate(tablevw);
               } else {
                  refreshPending(res.count);
                  if (selectedRowIds.length > 0) {
                     setSelectedRowIds([])
                  }
               }

            }
         }).catch(() => {
            // Aborted on unmount, or the request failed -- either way there is
            // nothing to render. Without a handler the abort would surface as
            // an unhandled promise rejection.
         });
      }
   }

   const handleRowSelected = useCallback(state => {
      var checkedListAll = state.selectedRows.map((row) => row.key);
      setSelectedRowIds(checkedListAll);
   }, []);

   const GridCheckedListUpdate = (list) => {
      setSelectedRowIds(list);
   }

   const tableviewUpdate = (view) => {
      setTableview(view);
      setSelectedRowIds([]);
   }

   const resetSelectedRowIds = () => {
      setSelectedRowIds([]);
      tableUpdate('L');
   }

   //
   const keywordpageroute = (kwdata) => {
      var ids = kwdata.key.toString().split("~")
      var path = `/keywords/${global.keywordsecret + parseInt(ids[0])}/${kwdata.KW.split(' ').join('_').toLowerCase()}`

      history.push({ pathname: path, state: { 'kwdata': kwdata, 'basedata': { ...props.basedata, 'kw_c': listTableData.lstresult.length } } })
   }

   const onRefreshClick = () => {
      if (props.refresh_on === false) {
         onRefreshTriggerFunc.current()
         return false;
      }
   }

   const onAddTags = () => {
      if (selectedRowIds.length) {
         managetagopenFunc.current(selectedRowIds, "", gridTableData.otg)
      }
      else {
         toast.error("Select keywords to add tags")
      }
   }

   return (
      <>
         <section className={"SR-table"}>
            <ParaLg class="fB mb-0 lineHAuto">
               {" "}
               Total keywords <span>({props.basedata.kw_c})</span>
            </ParaLg>

            <div className="header m-t20 m-b20">
               <div className="left">
                  <SRTableSearch tablefullresult={tableview === "G" ? gridTableData.grdfullresult : listTableData.lstresult} tableview={tableview} tabledataUpdate={tableview === "G" ? GrdtablefilterdataUpdate : tablefilterdataUpdate} />
                  <ProjectFileExport fullbasedata={props.fullbasedata} basedata={props.basedata} pageupdate={false} refresh_on={props.refresh_on} lstfltrresult={listTableData.lstfltrresult} />
               </div>

               <div className="right">
                  {/* AppIconButton drops unknown props, so it cannot carry an
                      aria-label. These are icon-only controls and DESIGN.md
                      requires an accessible name, so they use IconButton
                      directly -- same element, same class names. */}
                  {canManageTags ? <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"Select keywords to add tags"} >
                     <div className="d-flex">
                        <IconButton
                           className={"boxIcon" + (selectedRowIds.length > 0 ? " kwselect" : "")}
                           aria-label={selectedRowIds.length > 0 ? "Add tags to the selected keywords" : "Add tags to keywords"}
                           onClick={onAddTags}
                        >
                           <TagIcon height="18" width="18" />
                        </IconButton>
                     </div>
                  </Tooltip> : null}
                  {canRefreshKeywords ? <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={selectedRowIds.length === 0 ? "Refresh all the keywords" : "Refresh the selected keywords"} >
                     <div className="d-flex">
                        {/* RefreshBar below carries "Refreshing... N%" for the
                            whole run, so the button does not spin as well. */}
                        <IconButton
                           className={"boxIcon" + (selectedRowIds.length > 0 ? " kwselect" : "")}
                           aria-label={selectedRowIds.length === 0 ? "Refresh all keywords" : "Refresh the selected keywords"}
                           disabled={props.refresh_on !== false}
                           onClick={onRefreshClick}
                        >
                           {typeof props.refresh_on === "boolean" ? <RefreshIcon height="18" width="18" /> : <Tsk width={30} />}
                        </IconButton>
                     </div>
                  </Tooltip> : null}
                  {canDeleteKeywords ? <div>
                     <KWDelete selectedRowIds={selectedRowIds} updatefullpage={props.updatefullpage} basedata={props.basedata} />
                  </div> : null}

                  {tableview === "G" ?
                     <GridTblFilter gridUpdate={gridUpdate} grdtbltype={grdtbltype} />
                     :
                     <TableCustomColumns lsttblhdlst={listTableData.lth} projectage={listTableData.age} tablehdUpdate={(tableheaderlst) => setListTableData(olddata => ({ ...olddata, 'lth': tableheaderlst }))} />
                  }

                  <TableViewToggle tableview={tableview} tableviewUpdate={tableviewUpdate} projectList={props.projectList} baseauthdataUpdate={props.baseauthdataUpdate} />
               </div>
            </div>

            {tableview === "G" ?
               <GrdDataTable grdfullresult={gridTableData.grdfullresult} grdtblfltrresult={gridTableData.grdtblfltrresult} grdtbltype={grdtbltype} tableUpdate={gridUpdate} tabledataUpdate={GrdtabledataUpdate} GridCheckedListUpdate={GridCheckedListUpdate} selectedRowIds={selectedRowIds} updatefullpage={props.updatefullpage} keywordpageroute={keywordpageroute} canSelectKeywords={canSelectKeywords} />
               :
               <LstDataTable managetagopenFunc={managetagopenFunc} resetSelectedRowIds={resetSelectedRowIds} kwCount={props.basedata.kw_c} lstresult={listTableData.lstresult} lstfltrresult={listTableData.lstfltrresult} tableUpdate={tableUpdate} tabledataUpdate={tabledataUpdate} gridtableUpdate={gridUpdate} handleRowSelected={handleRowSelected} selectedRowIds={selectedRowIds} updatefullpage={props.updatefullpage} projectbase={{ 'age': listTableData.age, 'lth': listTableData.lth, 'otg': gridTableData.otg }} keywordpageroute={keywordpageroute} canSelectKeywords={canSelectKeywords} />
            }

         </section>
         {canRefreshKeywords ? <RefreshBar onRefreshTriggerFunc={onRefreshTriggerFunc} onRefreshCheckFunc={onRefreshCheckFunc} kwids={selectedRowIds} refresh_on={props.refresh_on} refreshUpdate={refreshUpdate} pageurl={"keywords"} pjtid={grpid} /> : null}
         <SerpLegend rows={listTableData.lstresult} />
      </>
   );
}

export default SerpRankTable;
