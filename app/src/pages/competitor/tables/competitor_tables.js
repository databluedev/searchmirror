import React, {useState, useEffect, useMemo} from "react";
import { isRanked, rankLabel, rankSortKey } from "../../../utils/rank_state";
import { useHistory } from "react-router-dom";
import { ParaLg, Tsk } from "../../commonComponents/parts";
import KeywordSearch from "../components/keywordSearch";
import CompetitorLstTable from "./competitor_list_table";

var lstresltdata = { "key": 11342, "RK": [], "RW": null, "RS": "never_checked", "SV": "init", "io": "", "PM": "", "kwas": "" }

function CompetitorTables(props) {

   const history = useHistory();

   const [listTableData, setListTableData] = useState({'age': props.age, 'totalkw': 0, 'lstresult': Array(5).fill(lstresltdata), 'lstfltrresult': Array(5).fill(lstresltdata)});

   useEffect(() => {

      if (props.tableData.lstresult.length > 0){
         setListTableData(olddata => ({...olddata, 'age':props.age, 'totalkw': props.tableData.lstresult.length, 'lstresult':props.tableData.lstresult, 'lstfltrresult':props.tableData.lstresult }))
      }

      // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [props.tableData]);



   const tableUpdate = (data) => {
      // api call for table api data display
   }

   const tablefilterdataUpdate = (data) => {
      setListTableData(olddata => ({...olddata, 'lstfltrresult': data}))
   }

   const competitorOutranks = useMemo(() => {
      /* "The competitor outranks you" needs the competitor to actually rank.
         Your own side may legitimately not -- that is the widest gap there
         is -- so it uses the sort key, which orders unranked past every real
         position without claiming to be one. */
      return listTableData.lstresult
         .filter(row => row.KW && isRanked(row) && Number(row.RW) < rankSortKey({ RW: row.MRW, RS: row.MRS, RSK: row.MRSK }))
         .map(row => ({ ...row, gap: rankSortKey({ RW: row.MRW, RS: row.MRS, RSK: row.MRSK }) - Number(row.RW) }))
         .sort((left, right) => right.gap - left.gap);
   }, [listTableData.lstresult]);

   const createContentBrief = (row) => {
      localStorage.setItem('contentPlannerForm', 'true');
      localStorage.setItem('contentPlannerSeed', JSON.stringify({
         primaryKeyword: row.KW,
         secondaryKeywords: competitorOutranks
            .filter(item => item.KW !== row.KW)
            .slice(0, 5)
            .map(item => item.KW),
      }));
      history.push('/contentplanner');
   };


   return (
      <>
         {competitorOutranks.length > 0 ?
            <section className="whiteCard m-b20 p20x" aria-labelledby="ranking-opportunities-title">
               <div className="d-flex align-items-start justify-content-between gap-3 flex-wrap">
                  <div>
                     <h2 id="ranking-opportunities-title" className="fB f18x m-b5">Ranking opportunities</h2>
                     <p className="mb-0 newlightTxtClr">
                        {props.cprojectName} outranks {props.projectName} for {competitorOutranks.length} shared keyword{competitorOutranks.length === 1 ? '' : 's'}.
                     </p>
                  </div>
               </div>
               <div className="d-flex flex-column gap-2 m-t15">
                  {competitorOutranks.slice(0, 3).map(row =>
                     <div key={row.key} className="d-flex align-items-center justify-content-between gap-3 border rounded p-3 flex-wrap">
                        <div>
                           <div className="fM f15x">{row.KW}</div>
                           <div className="f12x newlightTxtClr m-t5">
                              Your rank {rankLabel({ RW: row.MRW, RS: row.MRS, RC: row.MRC }, true)} · competitor rank {row.RW}
                           </div>
                        </div>
                        <button type="button" className="btn btn-dark" onClick={() => createContentBrief(row)}>
                           Create content brief
                        </button>
                     </div>
                  )}
               </div>
            </section>
         : null}
         <section className="totalkeyword">
            <div className="d-flex align-items-center justify-content-between m-b20">
               <ParaLg class="fB mb-0 lh24x d-flex align-items-center">
                  Total keywords <span className="d-flex align-items-center m-l5">({ listTableData.totalkw ? listTableData.totalkw : <Tsk width={20} height={20} />})</span>
               </ParaLg>

               <div>
                  <KeywordSearch tablefullresult={listTableData.lstresult} tableview={"L"}  keydataUpdate={tablefilterdataUpdate}/>
                  {/*<ProjectFileExport fullbasedata={props.fullbasedata} basedata={props.basedata} pageupdate={false} refresh_on={props.refresh_on} lstfltrresult={lstfltrresult} />*/}
               </div>
            </div>

            <CompetitorLstTable lstresult={listTableData.lstresult} lstfltrresult={listTableData.lstfltrresult} tableUpdate={tableUpdate} projectbase={{'age':listTableData.age, 'pn':props.projectName, 'cpn':props.cprojectName }} />

         </section>
      </>
   );
}

export default CompetitorTables;
