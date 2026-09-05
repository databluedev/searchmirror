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
import PageSkeleton from "../commonComponents/page_skeleton";
import { allowsTeamAction } from '../../utils/team_permissions';

function ContentPlanner(props) {
    const history = useHistory()
    const canManageContent = allowsTeamAction(props.fullbasedata, "ContentPlanner", "Manage Content");
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
                toast.error(res.message)
            } else {
                setInitialdata({
                    ...initialdata,
                    regionData: res.rg,
                })
            }
        }).catch((error) => {
            toast.error(error)
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

        axios.post(global.apiurl + '/contentmanager/list', { 'userid': userid, 'grpid': grpid }, {
            headers: { 'Authorization': 'Token ' + usertoken }
        }).then(response => {
            return response.data;
        }).then(res => {
            setApiLoading(false)
            if (res.status !== "true") {
                history.push("/contentplanner")
                toast.error(res.message)
            } else {

                if (res.data.length > 0) {
                    setShowOnBoard(false)
                }

                if (contentPlannerForm) {
                    setShowOnBoard(true)
                }

                setAllContentPlans(res.data)


            }
        }).catch((error) => {
            setApiLoading(false)
            toast.error(error)
        });
    }

    return (
        <>
            {apiLoading ?
                // Header then the plan table at its 10-row page size -- the
                // shape this page always arrives in. There is no stat strip
                // above it, so the skeleton has none either.
                <PageSkeleton label="Loading Content Planner" search rows={10} className="kr_layout" />
                : showOnboard && canManageContent ?
                    <>
                        <div className="capNoticeStandalone"><CapabilityNotice name="content_planner" /></div>
                        <CEditOnBoard projectList={props.projectList} fullbasedata={props.fullbasedata} regionData={regionData} kwdSearchDetails={kwdSearchDetails} refetchContentPlans={() => getAllContentPlans()} />
                    </>
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
