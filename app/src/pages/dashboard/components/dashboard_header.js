import { AddProjectIcon } from "../../commonComponents/icons";
import { Para, Title, AppButton } from "../../commonComponents/parts";
import ProjectSearch from "./projects_search";

function DashHeader(props) {
  // const mediumView = useMediaQuery("(max-width:767px)");
  return (
    <header>
      <div className="d-flex justify-content-between flex-wrap px-1">
         <div className="d-flex align-items-center gap-3">
            <div>
               <Title class="wd-title">All Projects</Title>
               <Para class="wd-subTitle">{"Total Projects ("+(props.fullbasedata ? props.fullbasedata.uPL : "0")+")"}</Para>
            </div>
         </div>

         <div
             className={`d-flex align-items-center gap-3 ${props.rightside}`}
             style={{ flex: "0 0 auto" }}
         >
            {/*<AppIconButton
               Icon={<NewVersionIcon />}
            />

            {mediumView ? (
               <AppIconButton
                 Icon={<ScheduleMeetingIcon />}
               />
            ) : (
               <Box
                 className=""
                 sx={{ minWidth: "190px", maxWidth: "200px", flex: "0 0 auto" }}
               >
                 <AppButton
                   value="Schedule Meeting"
                   color="white"
                   class="borderBtn"
                   Icon={<ScheduleMeetingIcon />}
                 ></AppButton>
               </Box>
            )}*/}

            { props.fulldata.length > props.projectPageLimit ?
               <ProjectSearch fulldata={props.fulldata} dataUpdate={props.dataUpdate} tcc={props.fullbasedata ? props.fullbasedata.uPL : "0"}/>
            : null }

            {props.canManageProjects ? <div className="addButton min-w-[145px] max-w-[150px] shrink-0">
               {/* .shinySweep runs a highlight across the fill once per hover
                   and once per keyboard focus -- a press affordance on the one
                   primary action of the screen, not a button that glints at
                   you while you read the list. */}
               <AppButton
                 value="Add Project"
                 class="wd-btn-add p-l0 p-r0 shinySweep"
                 onclick={props.addproject}
                 Icon={<AddProjectIcon />}
               ></AppButton>
            </div> : null}
         </div>
      </div>
    </header>
  );
}

export default DashHeader;
