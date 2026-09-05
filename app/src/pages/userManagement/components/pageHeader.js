import { Para, Title } from "../../commonComponents/parts";
import ProjectFavIcon from "../../commonComponents/project_fav_icon";

function PageHeader(props) {
    return (
        <header>
            <div className="d-flex flex-wrap gap-3 align-items-center">
                <ProjectFavIcon projectList={props.projectList} />
                <div>
                    <Title class="wd-title">{props.title}</Title>
                    <Para class="wd-subTitle">Team logins and the roles that govern them.</Para>
                </div>
            </div>
        </header>
    )
}
export default PageHeader;