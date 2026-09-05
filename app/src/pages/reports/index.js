import React, { useEffect, useState, useCallback, useRef } from 'react';
import './style.scss';
import ProjectFavIcon from "../commonComponents/project_fav_icon";
import PageSkeleton from "../commonComponents/page_skeleton";
import { GetDomain } from '../widget/components/common';
import { Box, Grid, Modal, Fade, Backdrop, Button } from '@mui/material';
import { Link } from 'react-router-dom';
import { Para, Title, AppButton, SelectMenu } from "../commonComponents/parts";
import { Button as UiButton } from "@/components/ui/button";
import Cookies from 'universal-cookie';
import ReportWidgetManagement from './report_widget';

import RankForm from './sheets/rank_form';
import BaseForm from './sheets/base_form';

import { CloseIconlg } from "../commonComponents/icons";
import axios from 'axios';
import { toast } from 'react-toastify';
import OverviewForm from './sheets/overview_form';
import ExportReport from './components/export_report';
import { ModalBox } from '../commonComponents/Modals';
import EcomModal from './components/eComModal';
import { allowsTeamAction } from '../../utils/team_permissions';

const demoDataRows = [
    { DEMO: Array.from({ length: 5 }, () => ({ DEMO: 'DEMO' })) }
]

// EXPORT REPORT MANAGEMENT 

const ReportManagement = (props) => {

    const canAddReports = allowsTeamAction(props.fullbasedata, "Reports", "Add Report");
    const canDeleteReports = allowsTeamAction(props.fullbasedata, "Reports", "Delete Report");
    const canExportReports = allowsTeamAction(props.fullbasedata, "Reports", "Enable Export");
    const canRenameReports = allowsTeamAction(props.fullbasedata, "Reports", "Rename Report");

    // The backend serves report sheets two at a time (serp/widget.py,
    // generate_widget: offset = (page - 1) * 2). "There may be more" is
    // therefore "the last batch came back full" -- anything short is the end.
    const REPORTS_PER_PAGE = 2

    // The sheet covers the whole viewport; the 60px left inset was the old
    // collapsed rail width applied to a surface that has no rail on it, and it
    // left the header hanging off-centre against a footer pinned at --rail-w.
    const style = {
        position: "absolute",
        width: "100%",
        height: "100%",
        bgcolor: "var(--surface)",
        overflowY: "auto",
        outline: "none"
    };

    const [data, setData] = useState({
        baseData: {},                       // CHOOSEN PROJECT DATA
        projectList: props.projectList,     // COMPLETE PROJECT LIST
        onChange: false,                    // USE EFFECT ON CHANGE TRIGGER
        btnloading: false,
        viewLoad: 0,                        // 1 - CONFIG, 2 - WIDGET, 
        filterMenu: "rank",
        summaryList: [],
        rlFlg: false,
        isGa: false,
        isGsc: false,
        load_more: 0,
        page: 1,
        shtFlg: true,
        pltSts: false,
        platform: '',
        isLoading: true
    });

    const [dynamicReport, setDynamicReport] = useState(demoDataRows);
    const [widLod, setWidLod] = useState(false);
    const [pltfrm, setPltFrm] = useState(['E-commerce'])

    var { baseData, onChange, projectList, btnloading, viewLoad, shtFlg, filterMenu, summaryList, rlFlg, isGa, isGsc, pltSts, platform, isLoading, load_more } = data;

    // handleInitialise runs from the mount effect and chains into
    // checkGscGaEnabled; handleLoadMore runs from the table. None of them is
    // owned by a single effect, so the component owns one controller: leaving
    // the route aborts whatever is in flight instead of letting it resolve into
    // setData/setDynamicReport. The deferred render below is tracked the same
    // way -- a pending setTimeout is just as much a leak as a pending request.
    const abortRef = useRef(null)
    if (abortRef.current === null) {
        abortRef.current = new AbortController()
    }
    const timersRef = useRef([])
    const deferRender = (fn, ms) => {
        timersRef.current.push(setTimeout(fn, ms))
    }
    useEffect(() => () => {
        abortRef.current.abort();
        timersRef.current.forEach(clearTimeout);
        timersRef.current = [];
    }, []);

    const checkGscGaEnabled = async () => {
        setData(prev => ({ ...prev, btnloading: true }))
        let aborted = false

        const cookies = new Cookies();
        var usertoken = cookies.get('session_token')
        var grpid = cookies.get('activegrp')
        var userid = cookies.get('session_userid')
        var data = { 'userid': userid, 'grpid': grpid }

        await axios.post(global.apiurl + "/is_enable", data, {
            headers: { 'Authorization': 'Token ' + usertoken },
            signal: abortRef.current.signal
        }).then(r => {
            return r.data
        }).then(res => {
            if (res.st === 1) {
                setData(prev => ({ ...prev, isGa: res.dt['ga'], isGsc: res.dt['gsc'], pltSts: res.dt['pltfrm'], platform: res.dt['platform'] }))
            }
        }).catch(err => {
            // The unmount cleanup aborted this: nothing failed, and the
            // statement after the await must not run either.
            if (axios.isCancel(err)) {
                aborted = true
                return
            }
            console.error("Reports: capability check failed", err)
        })
        if (!aborted) {
            setData(prev => ({ ...prev, btnloading: false }))
        }
    }

    const handleLoadMore = async () => {
        if (shtFlg) {
            setData(data => ({ ...data, load_more: 1 }))

            const cookies = new Cookies();
            var grpid = cookies.get('activegrp')
            const usertoken = cookies.get('session_token')
            const userid = cookies.get('session_userid');
            const param_data = {
                'userid': userid,
                'grpid': grpid,
                'page': data.page,
            }

            await axios.post(global.apiurl + "/dynamic_widget", param_data, {
                headers: { 'Authorization': 'Token ' + usertoken },
                signal: abortRef.current.signal
            }).then(r => {
                return r.data
            }).then(response => {
                if (response.hasOwnProperty('sht_flg')) {
                    setData(prev => ({ ...prev, shtFlg: false }))
                }
                if (response.st === 1) {
                    var res = response.dt
                    let reportData = [...dynamicReport, ...res]

                    deferRender(() => {
                        setDynamicReport(reportData);
                        setData(data => ({ ...data, viewLoad: 2, summaryList: response.sm_list, page: response.page, load_more: res.length < REPORTS_PER_PAGE ? 0 : -1 }))
                    }, 1000)

                } else {
                    // sht_flg is how the API says "that was the last page". Any
                    // other refusal is a real failure and the reader has to be
                    // told -- the button used to vanish in silence either way.
                    if (!response.hasOwnProperty('sht_flg')) {
                        toast.error("More reports could not be loaded. Please try again.")
                    }
                    setData(data => ({ ...data, load_more: 0 }))
                }
            }).catch((error) => {
                // The unmount cleanup aborted this: nothing failed, and there
                // is nothing left to render the failure into.
                if (axios.isCancel(error)) {
                    return
                }
                toast.error("More reports could not be loaded. Please try again.")
                setData(data => ({ ...data, load_more: 0 }))
            })
        }
    }

    const handleInitialise = useCallback(async (projectList) => {
        const cookies = new Cookies();
        var grpid = cookies.get('activegrp')
        var apidata = {}
        let aborted = false

        if (projectList.length > 0) {
            apidata = projectList.filter(item => item.GY === parseInt(grpid))[0];

            if (typeof (apidata) !== "object" || apidata.length === 0) {
                apidata = projectList[0];
            }

            cookies.set('activegrp', apidata.GY, { path: '/', maxAge: global.cookiesexpire });
            cookies.set('w_order', baseData.w, { path: '/', maxAge: global.cookiesexpire })

            setData({
                ...data,
                baseData: apidata,
            })
        }
        setWidLod(false)

        const usertoken = cookies.get('session_token')
        const userid = cookies.get('session_userid');
        const param_data = {
            'userid': userid,
            'grpid': grpid,
            'page': data.page,
        }

        await axios.post(global.apiurl + "/dynamic_widget", param_data, {
            headers: { 'Authorization': 'Token ' + usertoken },
            signal: abortRef.current.signal
        }).then(r => {
            return r.data
        }).then(response => {
            if (response.st === 1) {
                var res = response.dt

                deferRender(() => {
                    setDynamicReport(res);
                }, 1000)

                if (res.length >= REPORTS_PER_PAGE) {
                    setData(data => ({ ...data, viewLoad: 2, page: response.page, summaryList: response.sm_list, load_more: -1 }))
                } else {
                    setData(data => ({ ...data, viewLoad: 2, page: response.page, summaryList: response.sm_list, load_more: 0 }))
                }

                setWidLod(true)

            } else {
                setData(data => ({ ...data, viewLoad: 1, load_more: 0 }))
                setWidLod(true)
            }
        }).catch((error) => {
            // The unmount cleanup aborted this: nothing failed, and the
            // follow-up request below must not be started either.
            if (axios.isCancel(error)) {
                aborted = true
                return
            }
            setData(data => ({ ...data, viewLoad: 1, load_more: 0 }))
            setWidLod(true)
        })
        if (!aborted) {
            checkGscGaEnabled()
        }
    }, [onChange, props.projectList])

    // USE EFFECT
    useEffect(() => {
        setData(data => ({ ...data, load_more: 0 }))
        handleInitialise(props.projectList)
    }, [onChange, props.projectList]);

    const [open, setOpen] = useState(false);
    const [eOpen, setEopen] = useState(false);
    const [platOpen, setPlatOpen] = useState(false)

    const handleOpen = () => {
        if (pltSts) {
            setPlatOpen(true)
        } else {
            if (platform === 'Non E-commerce') {
                setOpen(true)
            } else {
                setEopen(true)
            }
        }
    }

    const handleRprtOpen = async () => {
        setPlatOpen(false);

        const cookies = new Cookies()
        var data = { 'userid': cookies.get('session_userid'), 'grpid': cookies.get('activegrp'), 'pltform': pltfrm[0] }

        await axios.post(global.apiurl + '/change_platform', data, {
            headers: { 'Authorization': 'Token ' + cookies.get('session_token') }
        }).then(res => {
            return res.data
        }).then(response => {
            if (response.st === 1) {
                setData(prev => ({ ...prev, pltSts: false }))
                if (pltfrm[0] === 'Non E-commerce') {
                    setOpen(true);
                } else {
                    setEopen(true)
                }
            } else {
                toast.error(response.dt || "Could not change the report platform.")
            }
        }).catch(err => {
            toast.error("Could not change the report platform.")
        })
    }

    const handleClose = () => {
        setOpen(false)
        setEopen(false)
        setPlatOpen(false)
        if (rlFlg) {
            // A full window.location.reload() after adding a report threw away
            // the session's scroll position and flashed the whole shell. The
            // list is fetched by one request; re-run that, and put the sheet
            // back to its default type so reopening Add Report does not land on
            // whichever tab was left selected.
            setData(prev => ({
                ...prev,
                rlFlg: false,
                page: 1,
                load_more: 0,
                shtFlg: true,
                filterMenu: 'rank',
                summaryList: [],
            }))
            setDynamicReport(demoDataRows)
            setWidLod(false)
            handleInitialise(props.projectList)
        }
    }

    const handleFilter = (value) => {
        setData({
            ...data,
            filterMenu: value,
        })
    };

    const handlePlatClose = () => setPlatOpen(false)

    const handlePlatChange = (e) => {
        var { target: { value }, } = e;
        value = (typeof value === "string") ? value.split(",") : value[0];
        setPltFrm(value)
        setData(prev => ({ ...prev, platform: value[0] }))
    }

    return (
        <>
            {viewLoad ?
                <section className='layout' id='layout' onClick={props.handleClick} >
                    <header className=''>
                        <div className="d-flex justify-content-between flex-wrap gap-3">
                            <div className="d-flex flex-wrap gap-3 align-items-center">
                                <ProjectFavIcon projectList={props.projectList} />
                                <div>
                                    <Title class="wd-title">Reports</Title>
                                    <a className="wd-subTitle d-flex" rel="noreferrer" href={baseData.DN} target="_blank">
                                        {<GetDomain url={baseData.DN} />}
                                        <span className="m-l5">
                                            <svg
                                                className="primarySvg"
                                                id="Component_76_1"
                                                data-name="Component 76 – 1"
                                                xmlns="http://www.w3.org/2000/svg"
                                                width="10"
                                                height="10"
                                                viewBox="0 0 12 12"
                                            >
                                                <path
                                                    id="Path_417"
                                                    data-name="Path 417"
                                                    d="M14.333,8.333A.667.667,0,0,0,13.667,9v4a.667.667,0,0,1-.667.667H5A.667.667,0,0,1,4.333,13V5A.667.667,0,0,1,5,4.333H9A.667.667,0,1,0,9,3H5A2,2,0,0,0,3,5v8a2,2,0,0,0,2,2h8a2,2,0,0,0,2-2V9A.667.667,0,0,0,14.333,8.333Z"
                                                    transform="translate(-3 -3)"
                                                    fill="currentColor"
                                                />
                                                <path
                                                    id="Path_418"
                                                    data-name="Path 418"
                                                    d="M14.331,4.333h1.053L11.191,8.52a.669.669,0,1,0,.947.947L16.331,5.28V6.333a.667.667,0,1,0,1.333,0V3.667A.667.667,0,0,0,17,3H14.331a.667.667,0,1,0,0,1.333Z"
                                                    transform="translate(-5.665 -3)"
                                                    fill="currentColor"
                                                />
                                            </svg>
                                        </span>
                                    </a>
                                </div>
                            </div>

                            <div className="d-flex align-items-center undefined dashboard flex-[0_0_auto] gap-[0.6rem]">

                                {viewLoad > 1 ?
                                    <>
                                        {canExportReports ? <div className="min-w-[130px] max-w-[130px] flex-[0_0_auto]">
                                            <ExportReport />
                                        </div> : null}
                                        {canAddReports ? <div className="d-flex w150x">
                                            <AppButton
                                                noIcon="d-none"
                                                id="againbtnclick"
                                                value="Add Report"
                                                color="primary"
                                                type="submit"
                                                disabled={btnloading}
                                                class="m-r0"
                                                onclick={handleOpen}
                                            />
                                        </div> : null}
                                    </>
                                    :
                                    null
                                }

                            </div>
                        </div>
                    </header>

                    {viewLoad == 1 ?
                        <div className="emptyState">
                            <p className="emptyState__label">Reports</p>
                            {/* "takes about five minutes to build" described a
                                job that does not exist. Adding a report writes a
                                ReportSheets row and nothing else -- no crawl is
                                queued, no credit is spent -- and /dynamic_widget
                                builds the rows live out of the ranking history
                                already on record (serp/widget.py generate_widget),
                                on every load. So a new report is there on the
                                next fetch, which handleClose triggers straight
                                away. What it cannot do is invent history: on a
                                project that has not been ranked yet it arrives
                                empty and fills in as the crawls land. */}
                            <p className="emptyState__body">
                                No report has been configured for this project yet. A report is a
                                saved view of the ranking history this project has already
                                collected, so it appears as soon as you add it.
                            </p>
                            {canAddReports ? <div className="emptyState__action">
                                <AppButton
                                    noIcon="d-none"
                                    id="againbtnclick"
                                    value="Configure report"
                                    color="primary"
                                    type="submit"
                                    disabled={btnloading}
                                    onclick={handleOpen}
                                />
                            </div> : null}
                        </div>
                        :
                        <>
                            <ReportWidgetManagement basedata={baseData} viewLoad={viewLoad} dynamicReport={dynamicReport} widLod={widLod} fullbasedata={props.fullbasedata} projectList={props.projectList} handleInitialise={handleInitialise} canDelete={canDeleteReports} canRename={canRenameReports} />

                            {load_more === 0 ?
                                <div className="text-center p-t20 p-b30">
                                    <div style={{ height: "40px" }}>
                                    </div>
                                </div>
                                :
                                <>
                                    {(load_more === 1 && dynamicReport.length) ?
                                        <div className="text-center p-t20 p-b30">
                                            <div className="d-flex justify-content-center align-items-center" style={{ height: "40px" }}>
                                                <div className="loading"></div>
                                            </div>
                                        </div>
                                        :
                                        <div className="d-flex justify-content-center p-t20 p-b30">
                                            <button type="button" className="btn borderBtn reportLoadMore" onClick={() => handleLoadMore()}>
                                                Load more reports
                                            </button>
                                        </div>
                                    }
                                </>
                            }
                        </>
                    }

                    {/* NON E-COMMERCE REPORT CONFIGURE POPUP - STARTS */}
                    <Modal
                        className="full-page-modal"
                        open={open}
                        onClose={handleClose}
                        aria-labelledby="report-modal-title"
                        aria-describedby="report-modal-description"
                        closeAfterTransition
                        BackdropComponent={Backdrop}
                        BackdropProps={{
                            timeout: 1000,
                        }}
                    >
                        <Fade in={open} {...(open ? { timeout: 750 } : { timeout: 1000 })}>
                            <Box className="fp-modal-box drp-modal" sx={style}>
                                <header className="fp-modal-header">
                                    <div className="d-flex align-items-center justify-content-between px-2">
                                        <div>
                                            <Title id="report-modal-title" class="fp-modal-title">
                                                {"Configure Report"}
                                            </Title>
                                            <Para id="report-modal-description" class="fp-modal-sub-title mb-0">
                                                {"Customize and control reports to fit your unique requirements."}
                                            </Para>
                                        </div>

                                        <div style={{ flex: "0 0 auto" }}>
                                            <Button aria-label="Close report configuration" onClick={handleClose} className="wd-CloseButton">
                                                <CloseIconlg color="#0a0a0a" />
                                            </Button>
                                        </div>
                                    </div>
                                </header>

                                <section className="drp-form">
                                    <div className="px-2 m-b70">

                                        <Grid container spacing={3} className="drp-main-grid">
                                            <Grid className="drp-filter-grid" item xs={12} md={12} lg={12}>

                                                {/* .wd-filterLabel / .wd-filterOption are declared in
                                                    serpRank, competitor and pageaudit -- none of which this
                                                    page imports -- so this strip shipped with no styling at
                                                    all: five bare radios above five run-together labels. The
                                                    rules now live in this page's own stylesheet.

                                                    The two types this instance can build come first. Domain
                                                    Metrics reads DomainTracking.da_metrics / dr_metrics, and
                                                    nothing in backend/ or engine/ has written those since the
                                                    Moz and Ahrefs integrations were unrouted -- seo_metrics_sub
                                                    bails on the empty list, so the sheet is created, reports
                                                    success, and never appears in the list. It is marked
                                                    unavailable the same way Search Console, Analytics and
                                                    Search Volume already are; re-enable it by restoring the
                                                    onChange and dropping `disabled`. */}
                                                <div className="wd-history-duration-filter reportTypePicker">
                                                    <div className="d-flex align-items-center flex-wrap bg-transparent">

                                                        <label className={filterMenu === "rank" ? "wd-filterLabel active" : "wd-filterLabel"}>
                                                            <input type="radio" name="report-type" value="rank" checked={filterMenu === "rank"} onChange={() => handleFilter("rank")} />
                                                            <div className="wd-filterOption">
                                                                <span>Keyword Ranking</span>
                                                            </div>
                                                        </label>

                                                        <label className={filterMenu === "overview" ? 'wd-filterLabel active' : "wd-filterLabel"}>
                                                            <input type="radio" name="report-type" value="overview" checked={filterMenu === "overview"} onChange={() => handleFilter("overview")} />
                                                            <div className='wd-filterOption'>
                                                                <span className=''>Summary</span>
                                                            </div>
                                                        </label>

                                                        <label className="wd-filterLabel disabled" title="Needs a Moz or Ahrefs connection, which this instance does not have">
                                                            <input type="radio" name="report-type" value="base" disabled />
                                                            <div className="wd-filterOption">
                                                                <span>Domain Metrics <small>(Moz/Ahrefs later)</small></span>
                                                            </div>
                                                        </label>

                                                        <label className="wd-filterLabel disabled" title="Available after Google OAuth is added">
                                                            <input type="radio" name="report-type" value="gsc" disabled />
                                                            <div className="wd-filterOption">
                                                                <span>Google Search Console <small>(OAuth later)</small></span>
                                                            </div>
                                                        </label>

                                                        <label className="wd-filterLabel disabled" title="Available after Google OAuth is added">
                                                            <input type="radio" name="report-type" value="ga" disabled />
                                                            <div className="wd-filterOption">
                                                                <span>Google Analytics <small>(OAuth later)</small></span>
                                                            </div>
                                                        </label>

                                                    </div>
                                                </div>
                                            </Grid>

                                            <Grid className="drp-content-grid" item xs={12} md={12} lg={12}>
                                                <div className="drp-content-block">
                                                    {filterMenu === "rank" ?
                                                            <RankForm handleClose={handleClose} setData={setData} />

                                                        : filterMenu === "base" ?
                                                            <BaseForm handleClose={handleClose} setData={setData} />
                                                            :
                                                                    <OverviewForm summaryList={summaryList} handleClose={handleClose} setData={setData} isGa={isGa} isGsc={isGsc} />
                                                    }

                                                </div>
                                            </Grid>
                                        </Grid>
                                    </div>
                                </section>
                            </Box>
                        </Fade>
                    </Modal>
                    {/* NON E-COMMERCE REPORT CONFIGURE POPUP - ENDS */}

                    {/* E-COMMERCE REPORT CONFIGURE POPUP - STARTS */}
                    <EcomModal open={eOpen} handleClose={handleClose} style={style} filterMenu={filterMenu} handleFilter={handleFilter} setData={setData} isGa={isGa} isGsc={isGsc} summaryList={summaryList} />
                    {/* E-COMMERCE REPORT CONFIGURE POPUP - ENDS */}

                    {/* PLATFORM SELECTION PRIORITY IF NOT CONFIGURED - STARTS */}
                    <ModalBox title={"Select Platform"} open={platOpen} handleClose={handlePlatClose} onClose={handlePlatClose}>
                        <div className='rprtPlatformSelect px-3'>
                            <div className='p-b10 wd-subTitle'>
                                Reports are laid out differently for a store than for a content site.
                                Pick the one that matches this project -- it is asked once and applies
                                to every report on it.
                            </div>
                            <div className='p-b15'>
                                <SelectMenu value={pltfrm} menulist={['E-commerce', 'Non E-commerce']} placeholder='Select' onchange={handlePlatChange} />
                            </div>
                            <div className='d-flex justify-content-end p-b15'>
                                <UiButton variant="primary" className='w-25' onClick={handleRprtOpen}>Continue</UiButton>
                            </div>
                        </div>
                    </ModalBox>
                    {/* // PLATFORM SELECTION PRIORITY IF NOT CONFIGURED - ENDS */}

                </section >
                :
                // viewLoad 0 is "the report list has not answered yet". What
                // lands is the header and a report card -- a title row over a
                // table -- which is the shape drawn here. The card's own body
                // has skeletons of its own (components/ecom_widget.js), so the
                // two waits read as one continuous object.
                <PageSkeleton label="Loading reports" rows={8} />
            }
        </>
    )
}

export default ReportManagement;

