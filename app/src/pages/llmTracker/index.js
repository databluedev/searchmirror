import React, { useEffect, useRef, useState } from "react";
import { useHistory, useParams, useLocation } from "react-router-dom";
import "./style.scss";
import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import axios from 'axios';
import LLMSearchList from "./components/llm_search_list";
import LLMOnboardInfo from "../commonComponents/llm/llm_onboard_info";
import LLMHeader from "./components/llm_header";
import LLMInsights from "./components/llm_insights";
import CapabilityNotice from "../commonComponents/capability_notice";
import PageSkeleton from "../commonComponents/page_skeleton";
import { allowsTeamAction } from '../../utils/team_permissions';

function LLMTracker(props) {
    const history = useHistory()
    const canManageGeo = allowsTeamAction(props.fullbasedata, "LLMTracker", "Manage Geo Citations");
    // A project with no prompts has nothing to put in the table, so the page
    // shows the first-run screen instead of an empty grid and three buttons
    // whose purpose is not obvious. Set from the list response below -- a
    // search that matches nothing is an empty result, not a new project, and a
    // member without manage rights cannot create prompts, so neither of them
    // gets the onboarding.
    const [showOnboard, setShowOnBoard] = useState(false);
    const [allLLMPrompts, setAllLLMPrompts] = useState([]);
    const [apiLoading, setApiLoading] = useState(true);
    const [searchValue, setSearchValue] = useState('');
    // Bumped on every table refetch so the insight cards (Mention Summary,
    // trend) re-read their aggregates after Run analysis / Add, instead of
    // showing figures from page load.
    const [refreshTick, setRefreshTick] = useState(0);
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



    const savedPrompts = JSON.parse(localStorage.getItem('llmSavedPrompts') || '[]');
    const llmTrackerForm = localStorage.getItem('llmTrackerForm');

    var { regionData } = initialdata
    var { pageLoad, kwdSearchDetails } = keyData;

    // getAllLLMPrompts runs from this effect and from the search/refetch
    // callbacks handed to the children, so the requests belong to the component
    // rather than to one effect. Unmounting aborts whatever is in flight
    // instead of letting it resolve into setAllLLMPrompts/setApiLoading.
    const abortRef = useRef(null)
    if (abortRef.current === null) {
        abortRef.current = new AbortController()
    }
    useEffect(() => () => abortRef.current.abort(), []);

    useEffect(() => {
        const fetchInitialData = async () => {
            const cookies = new Cookies();
            const usertoken = cookies.get('session_token')
            const userid = cookies.get('session_userid')
            const grpid = cookies.get('activegrp');
            if (!usertoken || !userid) {
                history.push("/login");
                return;
            }

            // Initialize with empty array
            setAllLLMPrompts([]);
            setShowOnBoard(false);

            setKeyData({ ...keyData, pageLoad: true })
            var data = {
                'userid': userid,
                'grpid': grpid,
            };
            
            try {
                const response = await axios.post(global.apiurl + '/getsetting', data, {
                    headers: { 'Authorization': 'Token ' + usertoken },
                    signal: abortRef.current.signal
                });
                
                if (response.data.status !== "true") {
                    history.push("/")
                    toast.error(response.data.message)
                } else {
                    setInitialdata({
                        ...initialdata,
                        regionData: response.data.rg,
                    })
                }
            } catch (error) {
                // The unmount cleanup aborted this; there is no failure to report.
                if (axios.isCancel(error)) {
                    return;
                }
                toast.error(error)
            }
            
            // Call API to get initial prompts data
            await getAllLLMPrompts('');
        };

        fetchInitialData();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []) // Empty dependency array to run only once

    const getAllLLMPrompts = async (search = '', silent = false) => {
        // Update search value state
        setSearchValue(search);

        // Only the first load (and search) blanks the page to a spinner. A
        // refetch after Add / Run / Delete is silent -- it refreshes the table
        // in place without unmounting the section (which would tear down an open
        // modal and flash the whole page).
        if (!silent) setApiLoading(true);
        let aborted = false;
        try {
            const cookies = new Cookies();
            const usertoken = cookies.get('session_token')
            const userid = cookies.get('session_userid')
            const grpid = cookies.get('activegrp');

            if (!usertoken || !userid) {
                history.push("/login");
                return;
            }

            // Build request data
            const requestData = {
                userid: userid,
                groupid: grpid
            };
            
            // Add search parameter if provided
            if (search && search.trim()) {
                requestData.search = search.trim();
            }

            const response = await axios.post(global.apiurl + '/llmtracker/list', requestData, {
                headers: { 'Authorization': 'Token ' + usertoken },
                signal: abortRef.current.signal
            });

            if (response.data && response.data.status === "true") {
                const data = response.data.data || [];
                setAllLLMPrompts(data);
                setShowOnBoard(data.length === 0 && !(search && search.trim()));
            } else {
                // Fallback to empty array if API fails
                setAllLLMPrompts([]);
            }
        } catch (error) {
            // The unmount cleanup aborted this: nothing to report, nothing to
            // render into. `finally` still runs, hence the flag.
            if (axios.isCancel(error)) {
                aborted = true;
                return;
            }
            console.error('Error fetching prompts:', error);
            
            // Fallback to empty array if API fails
            setAllLLMPrompts([]);
        } finally {
            // Match the guard above: a silent refetch never toggled the spinner.
            if (!aborted && !silent) {
                setApiLoading(false);
            }
        }
    }

    return (
        <>
            {apiLoading ?
                // The shape is known before the payload is: header, the two
                // insight cards, then the prompt table at its 10-row page size.
                // A centred bar on a blank h100vh said only "wait" and then
                // dropped a full page in at once.
                <PageSkeleton label="Loading Geo Citations" cards={2} cardHeight={276} search rows={10} className="kr_layout" />
                : (showOnboard && canManageGeo) ?
                    <section className="layout kr_layout">
                        <div className="capNoticeStandalone"><CapabilityNotice name="geo_citations" /></div>
                        <LLMOnboardInfo regionData={regionData} kwdSearchDetails={kwdSearchDetails} refetchLLMPrompts={() => getAllLLMPrompts()} />
                    </section>
                    :
                    <section className="layout kr_layout">
                        <LLMHeader projectList={props.projectList} fullbasedata={props.fullbasedata} regionData={regionData} kwdSearchDetails={kwdSearchDetails} refetchLLMPrompts={() => { getAllLLMPrompts('', true); setRefreshTick((t) => t + 1); }} canManage={canManageGeo} />
                       <CapabilityNotice name="geo_citations" />
                        <LLMInsights refreshKey={refreshTick} />
                        <LLMSearchList
                            projectList={props.projectList}
                            allLLMPrompts={allLLMPrompts}
                            refetchLLMPrompts={() => { getAllLLMPrompts('', true); setRefreshTick((t) => t + 1); }}
                            onSearch={(search) => getAllLLMPrompts(search)}
                            searchValue={searchValue}
                            canManage={canManageGeo}
                        />

                    </section>

            }
        </>

    );
}

export default LLMTracker;
