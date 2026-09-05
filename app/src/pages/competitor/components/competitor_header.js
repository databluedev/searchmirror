import React, { useEffect, useState } from "react";

import Cookies from 'universal-cookie';
import { Title,Para,AppTooltip } from "../../commonComponents/parts";
import {fstLtrCapitalfun} from "../../common_fun";   
import ProjectFavIcon from "../../commonComponents/project_fav_icon";
import ReanalysisComponent from './reanalysis';
import TopAllCompettors from './top_all_competiitors';
import ProjectSearch from "../../dashboard/components/projects_search";

function CompetitorHeader(props) {
   const [baseData, setBaseData] = useState({});
   const Comparison = (
      <div>
         <Para class="m-b0">
            Here is the list of competitors you defined.
         </Para>
      </div>
   );
   useEffect(() => {
      const cookies = new Cookies();
      const grpid = cookies.get('activegrp');

      var apidata = {}
      if(props.projectList.length > 0) {
         apidata = props.projectList.filter(item => item.GY === parseInt(grpid))[0];
         if (typeof(apidata) !== "object" || apidata.length === 0) {
            apidata = props.projectList[0];
         }
         setBaseData(apidata);
      } 
   }, [props.projectList, props.aiRunStatus.Astatus]); 

   return (
      <header> 
         <div className="d-flex justify-content-between flex-wrap gap-3">
            <div className="d-flex flex-wrap gap-3 align-items-center">
               <ProjectFavIcon projectList={props.projectList} fullbasedata={props.fullbasedata} />
               <div>

               { props.aiRunStatus.Astatus === "OVER" ?
                  <>
                     <Title class="wd-title">Direct Competitors
                     <span className="m-l5">
                        <AppTooltip place="bottom-start" class="m-b0" title={Comparison} />
                     </span>
                     </Title>
                  </>
                  :
                  <Title class="wd-title">Competitors Analysis</Title>
               }
                  <Para class="wd-subTitle m-b0 d-flex align-items-center lh14x">{fstLtrCapitalfun(baseData.NM)}</Para>
               </div>
            </div>
            
            <div
               className="d-flex align-items-center twoButton addkeyhdr dashboard flex-none gap-[0.6rem]"
            >

               { props.aiRunStatus.Astatus === "OVER" ?
                  <>

                  { props.aiRunStatus.fullCp.length > props.compProjectPageLimit ?
                     <ProjectSearch fulldata={props.aiRunStatus.fullCp} dataUpdate={props.filterdataUpdate} />
                  : null }

                  {props.canReanalyse ? <div>
                     {/* <Tooltip title="Reanalysis" placement="top" TransitionComponent={Zoom} classes={{ tooltip: "Tltpsmall" }}>
                        <div>
                        <AppIconButton class="compLottieIcon" Icon={ <Lottie animationData={CompLottie} />}  />    
                        </div>
                     </Tooltip> */}
                     <ReanalysisComponent pageUpdate={props.pageUpdate} addlm={props.aiRunStatus.lm - props.aiRunStatus.uCc} />
                  </div> : null}
                  {props.canAdd ? <div className="min-w-[174px] max-w-[174px] flex-none" >
                     <TopAllCompettors tcc={props.aiRunStatus.tcc} pageUpdate={props.pageUpdate} dataUpdate={props.dataUpdate} addlm={props.aiRunStatus.lm - props.aiRunStatus.uCc} canAdd={props.canAdd} />
                  </div> : null}
                  </>
               : null }
            </div>
         </div>
      </header>
   );
}

export default CompetitorHeader;
