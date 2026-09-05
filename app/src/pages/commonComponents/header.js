import { Para, Title, AppButton, AppIconButton } from "./parts";
import { Link } from "react-router-dom";
import { Box } from "@mui/material";
import { BacklinkIcon, AddProjectIcon } from "../commonComponents/icons";

function Header(props) {
  // const mediumView = useMediaQuery("(max-width:767px)");
  return (
    <header>
      <div className="d-flex justify-content-between flex-wrap">
        <div className="d-flex align-items-center gap-3">
          <div className={`${props.back}`}>
            <Link to={props.backlink || "/projects"}>
            <AppIconButton
              class="sp-backbtn"
              Icon={<BacklinkIcon />}
            />
            </Link>
          </div>
          <div>
            <Title class="wd-title">{props.title}</Title>
            <Para class="wd-subTitle">{props.subTitle}</Para>
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

          { props.addprojectBtn ? 
          <Box
            className="addButton"
            sx={{ minWidth: "145px", maxWidth: "150px", flex: "0 0 auto" }}
          >
            <AppButton
              value="Add project"
              class="wd-btn-add p-l0 p-r0" 
              onclick={props.addproject}
              Icon={<AddProjectIcon />}
            ></AppButton>
          </Box>
          : null }
        </div>
      </div>
    </header>
  );
}

export default Header;
