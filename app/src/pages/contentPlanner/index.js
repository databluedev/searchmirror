import React, { useEffect, useState } from "react";
import { useHistory, useParams, useLocation } from "react-router-dom";
import "./style.scss";
import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import axios from 'axios';
import CEditSearchList from "./components/cedit_search_list";
import CEditOnBoard from "./cedit_onboard";
import CEditHeader from "./components/cedit_header";
import CapabilityNotice from "../commonComponents/capability_notice";
import { NoProjectYet } from "../commonComponents/not_ready";
import PageSkeleton from "../commonComponents/page_skeleton";
import { allowsTeamAction } from '../../utils/team_permissions';

function ContentPlanner(props) {
    const history = useHistory()
    const canManageContent = allowsTeamAction(props.fullbasedata, "ContentPlanner", "Manage Content");
    /* With no project there is no activegrp cookie -- private_route.js leaves it
       unset on purpose -- so every project-scoped call here would go out without
       a grpid. The page used to make them anyway and render the API's own
       "Invalid Params" in a red toast. */
    const hasProject = Boolean(props.projectList && props.projectList.length);
    const [showOnboard, setShowOnBoard] = useState(true);
    const [allContentPlans, setAllContentPlans] = useState([]);
    const [apiLoading, setApiLoading] = useState(true);
    const [initialdata, setInitialdata] = React.useState({
        regionData: [],
    });

    const [keyData, setKeyData] = useState({
        pageLoad: true,
        mainpage: 0,
        rankedKeywords: [],
        projectDomain: "",
        kwdSearchDetails: { "skey": 0, "tx": "", 'Rcd': "us", 'RN': "google.com", 'Rcnt': "United States" },
    });

    const contentPlannerForm = localStorage.getItem('contentPlannerForm');



    var { regionData } = initialdata
    var { pageLoad, kwdSearchDetails } = keyData;

    useEffect(() => {
        const cookies = new Cookies();
        const usertoken = cookies.get('session_token')
        const userid = cookies.get('session_userid')
        const grpid = cookies.get('activegrp');
        if (!usertoken || !userid) {
            history.push("/login");
        }
        if (!grpid) {
            return;   // no project: nothing to ask about
        }

        setKeyData({ ...keyData, pageLoad: true })
        var data = {
            'userid': userid,
            'grpid': grpid,
        };
        axios.post(global.apiurl + '/getsetting', data, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data;
        }).then(res => {
            if (res.status !== "true") {
                history.push("/")
                // The API's own wording is a diagnostic, not a sentence for a
                // reader. Say what happened to THEM and what to do next.
                toast.error("Content Planner settings could not be loaded. Try again in a moment.")
            } else {
                setInitialdata({
                    ...initialdata,
                    regionData: res.rg,
                })
            }
        }).catch(() => {
            // `error` here is an Axios object; rendering it printed
            // "AxiosError: Request failed with status code 500" at the user.
            toast.error("Content Planner settings could not be loaded. Try again in a moment.")
        });
        getAllContentPlans()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])


    const getAllContentPlans = () => {
        const cookies = new Cookies();
        const usertoken = cookies.get('session_token')
        const userid = cookies.get('session_userid')
        const grpid = cookies.get('activegrp');

        if (!usertoken || !userid) {
            history.push("/login");
        }
        if (!grpid) {
            setApiLoading(false);
            return;   // no project: nothing to ask about
        }

        axios.post(global.apiurl + '/contentmanager/list', { 'userid': userid, 'grpid': grpid }, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data;
        }).then(res => {
            setApiLoading(false)
            if (res.status !== "true") {
                history.push("/contentplanner")
                toast.error("Your content plans could not be loaded. Try again in a moment.")
            } else {

                if (res.data.length > 0) {
                    setShowOnBoard(false)
                }

                if (contentPlannerForm) {
                    setShowOnBoard(true)
                }

                setAllContentPlans(res.data)


            }
        }).catch(() => {
            setApiLoading(false)
            toast.error("Your content plans could not be loaded. Try again in a moment.")
        });
    }

    return (
        <>
            {!hasProject ?
                <section className="layout kr_layout">
                    <NoProjectYet feature="Content Planner" canAddProject={canManageContent} />
                </section>
            : apiLoading ?
                // Header then the plan table at its 10-row page size -- the
                // shape this page always arrives in. There is no stat strip
                // above it, so the skeleton has none either.
                <PageSkeleton label="Loading Content Planner" search rows={10} className="kr_layout" />
                : showOnboard && canManageContent ?
                    <CEditOnBoard
                        notice={<div className="capNoticeStandalone"><CapabilityNotice name="content_planner" /></div>}
                        projectList={props.projectList} fullbasedata={props.fullbasedata} regionData={regionData} kwdSearchDetails={kwdSearchDetails} refetchContentPlans={() => getAllContentPlans()} />
                    :
                    <section className="layout kr_layout">
                        <CEditHeader projectList={props.projectList} fullbasedata={props.fullbasedata} regionData={regionData} kwdSearchDetails={kwdSearchDetails} refetchContentPlans={() => getAllContentPlans()} canManage={canManageContent} />
                        <CapabilityNotice name="content_planner" />
                        <CEditSearchList projectList={props.projectList} allContentPlans={allContentPlans} refetchContentPlans={() => getAllContentPlans()} canManage={canManageContent} />
                    </section>

            }
        </>

    );
}

export default ContentPlanner;
