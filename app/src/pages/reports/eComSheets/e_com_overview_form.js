import React, { useEffect, useState } from 'react';
import { Link, useHistory } from "react-router-dom";
import { Input, SelectMenu, AppButton } from "../../commonComponents/parts";
import { Button } from "@/components/ui/button";
import { Grid, InputLabel, capitalize } from '@mui/material';
import Cookies from 'universal-cookie';

import '../style.scss';
import axios from 'axios';
import { toast } from 'react-toastify';

const EOverviewForm = (props) => {
    /*
        const monthDays = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
        const weekDays = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
        const monthIntervals = ["Past 1 month", "Past 2 months", "Past 3 months", "Past 4 months", "Past 5 months", "Past 6 months", "Past 7 months", "Past 8 months", "Past 9 months", "Past 10 months", "Past 11 months", "Past 12 months"];
        const weekIntervals = ["Past 1 week", "Past 2 weeks", "Past 3 weeks", "Past 4 weeks", "Past 5 weeks", "Past 6 weeks", "Past 7 weeks", "Past 8 weeks", "Past 9 weeks", "Past 10 weeks", "Past 11 weeks", "Past 12 weeks"];
    */

    /* These index the interval lists below, which start at "Past 2 ..." -- the
       one-period option was dropped because the backend cannot build it (see
       e_com_rank_form.js). Left at [1..12] here while the labels started at 2,
       this array was off by one on every choice: "Past 2 weeks" posted
       duration 1 and "Past 12 weeks" posted 11. The non-ecommerce form
       (sheets/overview_form.js) was corrected and this clone was not. */
    const monthDays = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    const weekDays = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    
    const patchSchedule = ["Weekly", "Monthly"];
    const monthIntervals = ["Past 2 months", "Past 3 months", "Past 4 months", "Past 5 months", "Past 6 months", "Past 7 months", "Past 8 months", "Past 9 months", "Past 10 months", "Past 11 months", "Past 12 months"];
    const weekIntervals = ["Past 2 weeks", "Past 3 weeks", "Past 4 weeks", "Past 5 weeks", "Past 6 weeks", "Past 7 weeks", "Past 8 weeks", "Past 9 weeks", "Past 10 weeks", "Past 11 weeks", "Past 12 weeks"];
    const orderByVals = ['Ascending', 'Descending']; 

    // The form used to open on "Google analytics" whatever the account had
    // connected, and Add Report answered every click with "Connect Google
    // Analytics to add GA Sheet". GA and Search Console are parked pending a
    // server-side OAuth flow, so isGa/isGsc are false and that was a dead end
    // by default. Only sources this account can actually report on are offered,
    // and the first of them is the one selected.
    const availableMetrics = [
        ...(props.isGa ? ['google analytics'] : []),
        ...(props.summaryList || []).filter(item => item !== 'google search console' || props.isGsc),
    ]
    const radioButtons = availableMetrics

    const initialState = {
        sheetName: "",
        selectedMetrics: availableMetrics[0] || '',
        scheduleInterval: ['Weekly'],
        trackDay: 2,
        trackOnDay: ['Past 2 weeks'],
        trackOnMonth: ['Past 3 months'],
        trackInterval: ['Past 2 weeks'],
        orderBy: ['Ascending'],
        btnLoading: false,  
    }

    const [data, setData] = useState(initialState);

    const [errMsg, setErrMsg] = useState({
        trackDayBug: "",
        sheetNameBug: "",
    });

    var { trackDayBug, sheetNameBug } = errMsg;
    var { sheetName, selectedMetrics, trackDay, trackInterval, orderBy, scheduleInterval, trackOnDay, trackOnMonth, btnLoading } = data;

    const handleSheetName = (e) => {
        setData({
            ...data,
            sheetName: e.target.value,
        })

        setErrMsg({
            ...errMsg,
            sheetNameBug: "",
        })
    };

    // const handleOrderBy=(e)=>{
    //     var { target: { value },} = e;
    //     console.log(value)
    //     value = (typeof value === "string") ? value.split(",") : value[0];
    //     console.log(value)
    //     setData(data=>({...data, orderBy:value}))
    // }

    // const handleTrackDay = (e) => { 
    //     var { target: { value }, } = e; 
    //     value = (typeof value === "string") ? value.split(",") : value[0];

    //     setData({
    //         ...data, 
    //         trackInterval: value, 
    //     })

    //     setErrMsg({
    //         ...errMsg,
    //         trackDayBug: "",  
    //     })
    // };

    const select_summary = {
        'google search console': 'gsc_overview',
        'keyword ranking': 'keyword_ranking_overview',
        'google analytics': 'ga_overview'
    }

    const addSheet = async (e) => {
        var flag = 1
        var schedule_level = "weekly";
        /* Was `var trackDay = trackDay;` -- a var declaration shadowing the
           destructured state of the same name, so this started as undefined and
           only ever held a number because the lookup below always matches a
           value that came out of the very list it searches. Named apart, like
           rank_form's reportDuration, so the two cannot be confused again. */
        var reportDuration = 2;
        setData(data => ({ ...data, btnLoading: true }))

        if (scheduleInterval[0] === "Monthly") {
            schedule_level = "monthly";
            reportDuration = 3;

            var intervalIndex = monthIntervals.indexOf(trackOnMonth.toString().trim());
            if (intervalIndex !== -1) {
                reportDuration = monthDays[intervalIndex];
            }
        } else {
            var intervalIndex = weekIntervals.indexOf(trackOnDay.toString().trim());
            if (intervalIndex !== -1) {
                reportDuration = weekDays[intervalIndex];
            }
        }

        if (sheetName.length <= 0) {
            flag = 0;
            toast.error("Please enter the sheet name.");
        }
        if (selectedMetrics === 'google analytics') {
            if (!props.isGa) {
                flag = 0
                toast.error('Connect Google Analytics to add GA Sheet')
            }
        }
        if (selectedMetrics === 'google search console') {
            if (!props.isGsc) {
                flag = 0
                toast.error('Connect Google Search Console to add GSC Sheet')
            }
        }

        if (flag) {
            // ADD SHEET AXIOS AND OTHER FUNCTIONALITY.
            const cookies = new Cookies();
            const usertoken = cookies.get('session_token');
            const userid = cookies.get('session_userid');
            const grpid = cookies.get('activegrp');

            if (userid && grpid) {

                var data = {
                    'userid': userid,
                    'grpid': grpid,
                    'sheet': sheetName,
                    'type': select_summary[selectedMetrics],
                    'schedule': (scheduleInterval[0]).toLowerCase(),
                    'duration': reportDuration,
                    'orderby': orderBy[0]
                };

                // axios.post(global.apiurl + '/dF9rZYWRkXb21ldH3JlcG9y3JkXXl3JY3Mp', data, {

                await axios.post(global.apiurl + '/e-overview_sheet', data, {
                    headers: { 'Authorization': 'Token ' + usertoken }
                }).then(response => {
                    return response.data;
                }).then(r => {
                    if (r.st === 1) {
                        toast.success(r.message)
                        setData(data => ({ ...data, btnLoading: false }))
                        props.setData(data => ({ ...data, rlFlg: true }))

                        // TIME DELAY AFTER THE TOAST MESSAGE 
                        // setTimeout(() => {
                        //     window.location.reload(); 
                        // }, 1500);
                        setData(initialState)
                        props.handleClose()

                    } else {
                        toast.error(r.message)
                        setData(data => ({ ...data, btnLoading: false }))
                    }
                }).catch((error) => {
                    toast.error(error.message)
                    setData(data => ({ ...data, btnLoading: false }))
                });
            }
        }
        setData(data => ({ ...data, btnLoading: false }))
    }

    const handleMetrics = (e) => {
        setData(data => ({ ...data, selectedMetrics: e.target.value }))
    }

    const handleScheduleInterval = (e) => {
        var { target: { value }, } = e;
        value = (typeof value === "string") ? value.split(",") : value[0];

        setData({
            ...data,
            scheduleInterval: value,
        })
    };
    const handleMonthTrackDay = (e) => {
        var { target: { value }, } = e;
        value = (typeof value === "string") ? value.split(",") : value[0];

        setData({
            ...data,
            trackOnMonth: value,
        })
    };
    const handleDayTrackDay = (e) => {
        var { target: { value }, } = e;
        value = (typeof value === "string") ? value.split(",") : value[0];

        setData({
            ...data,
            trackOnDay: value,
        })
    };

    const handleOrderBy = (e) => {
        var { target: { value }, } = e;
        value = (typeof value === "string") ? value.split(",") : value[0];
        setData(data => ({ ...data, orderBy: value }))
    }

    return (
        <>
            <div id="drp-rank-content" className="m-b20">
                <div className="m-b20 maxW300x">
                    <h2 className="fB f15x m-b5">
                        Report Name <span className="redClr">*</span>
                    </h2>
                    <Input placeholder="Ex: Weekly ranking summary" value={sheetName} onchange={handleSheetName} errmsg={sheetNameBug} error={sheetNameBug.length > 0} />
                </div>
            </div>

            <Grid container spacing={3}>
                <Grid item xs={12} md={12} lg={12}>
                    <div className="m-b20 drp-inner-block">
                        <div className='d-flex flex-wrap gap-3'>
                            <div>
                                <div className='m-b20'>
                                    <h2 className='fB f15x m-b5'>Duration</h2>
                                    <div className="drp-border m-t10  m-b10" />
                                </div>
                                <div className='fB f15x m-b5' />
                                <div className="m-b20">
                                    <InputLabel shrink className="">
                                        Period & Range
                                        <span className="redClr">
                                            {" *"}
                                        </span>
                                    </InputLabel>
                                    <div className='d-flex'>
                                        <div className='w200x m-r10'>
                                            {selectedMetrics === 'google search console' ?
                                                <SelectMenu value={scheduleInterval} menulist={patchSchedule} onchange={handleScheduleInterval} placeholder='select' />
                                                : selectedMetrics === 'google analytics' ?
                                                    <SelectMenu value={scheduleInterval} menulist={patchSchedule} onchange={handleScheduleInterval} placeholder='select' />
                                                    :
                                                    <SelectMenu value={scheduleInterval} menulist={['Weekly', 'Monthly']} onchange={handleScheduleInterval} placeholder='select' />
                                            }
                                        </div>
                                        {scheduleInterval[0] === "Monthly" ?
                                            <div className="w200x">
                                                <SelectMenu value={trackOnMonth} menulist={monthIntervals} placeholder="Select" onchange={handleMonthTrackDay} />
                                            </div>
                                            :
                                            <div className="w200x">
                                                <SelectMenu value={trackOnDay} menulist={weekIntervals} placeholder="Select" onchange={handleDayTrackDay} />
                                            </div>
                                        }
                                    </div>
                                </div>
                            </div>
                            {selectedMetrics !== 'keyword ranking' ?
                                <div>
                                    <div className=" m-b20">
                                        <h2 className="fB f15x m-b5">
                                            Order By
                                        </h2>
                                        <div className="drp-border m-t10  m-b10" />
                                    </div>

                                    <div className="m-b20">
                                        <InputLabel shrink className="">
                                            Date Sort
                                            <span className="redClr">
                                                {" *"}
                                            </span>
                                        </InputLabel>

                                        <div className="d-flex ">
                                            <div className="w200x m-r10">
                                                <SelectMenu value={orderBy} menulist={orderByVals} placeholder="Select" onchange={handleOrderBy} />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                :
                                null
                            }
                        </div>
                        <div>
                            <div className="m-b10">
                                <h2 className="fB f15x m-b5">
                                    Metrics
                                </h2>
                            </div>
                            <div className="drp-border m-t10  m-b10" />
                            {radioButtons.length === 0 ?
                            <p className="wd-subTitle m-b0">
                                A summary is built on top of another report. Add a Keyword Ranking
                                report first and it will be selectable here.
                            </p>
                            :
                            <div className="grid grid-cols-3 justify-items-start h-[40px] items-center">
                                {radioButtons.map((item, index) => (
                                    <div className='customRadio' key={item}>
                                        <label className='labl'>
                                            <input type="radio" name="radioname" value={item}
                                                checked={selectedMetrics === item}
                                                onChange={handleMetrics}
                                            />
                                            <div>
                                                <span className='border' />
                                                <span className='f14x'>{capitalize(item)}</span>
                                            </div>
                                        </label>
                                    </div>
                                ))}
                                {/* <div className="customRadio">
                                  <label className="labl">
                                  <input type="radio" name="radioname" value={"google_search_console"} 
                                    checked={selectedMetrics==="google_search_console"} 
                                    onChange={handleMetrics} 
                                  />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Google Search Console</span>
                                  </div>
                                  </label> 
                               </div>

                               <div className="customRadio">
                                  <label className="labl">
                                  <input type="radio" name="radioname" value={"google_analytics"} 
                                    checked={selectedMetrics==="google_analytics"}
                                    onChange={handleMetrics} 
                                    id='ga' 
                                  />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Google Analytics</span>
                                  </div>
                                  </label>
                               </div>

                               <div className="customRadio">
                                  <label className="labl">
                                  <input type="radio" name="radioname" value={"keyword_rankin"} 
                                    checked={selectedMetrics==="keyword_rankin"} 
                                    onChange={handleMetrics}
                                    id='rank'
                                  />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Keyword Ranking</span>
                                  </div>
                                  </label>
                               </div>

                               <div className="customRadio">
                                  <label className="labl">
                                  <input type="radio" name="radioname" value={"domain_metrics"}  
                                    checked={selectedMetrics==="domain_metrics"}  
                                    onChange={handleMetrics}
                                    id='dm'
                                  />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Domain Metrics</span>
                                  </div>
                                  </label>
                               </div> */}
                            </div>
                            }
                        </div>
                        {/* <div className='d-flex flex-wrap gap-3'>
                        <div>
                            <div className="m-t30 m-b20">
                                <h2 className="fB f15x m-b5"> 
                                   Duration
                                </h2>
                                <div className="drp-border m-t10  m-b10" />
                            </div>

                            <Box className="m-b20">
                                <InputLabel shrink className="">
                                    Weekly Ranking Interval
                                    <span className="redClr">
                                        {" *"}
                                    </span>
                                </InputLabel> 

                                <div className="maxW300x">  
                                    <SelectMenu value={trackInterval} menulist={weekIntervals} placeholder="Select" onchange={handleTrackDay} errmsg={trackDayBug} error={trackDayBug.length > 0} />
                                </div>
                           </Box>
                        </div> 
                        <div>
                            <div className="m-t30 m-b20">
                                <h2 className="fB f15x m-b5"> 
                                   Order By
                                </h2>
                                <div className="drp-border m-t10  m-b10" />
                            </div>

                            <Box className="m-b20">
                                <InputLabel shrink className="">
                                    Weekly Ranking Interval
                                    <span className="redClr">
                                        {" *"}
                                    </span>
                                </InputLabel> 

                                <div className="maxW300x">  
                                    <SelectMenu value={orderBy} menulist={orderByVals} placeholder="Select" onchange={handleOrderBy} errmsg={trackDayBug} error={trackDayBug.length > 0} />
                                </div>
                           </Box>
                        </div> 
                        </div> */}

                    </div>
                </Grid>
            </Grid>

            <div className="footer">
                <div>
                    <Link to={"/reports"}>
                        <Button variant="secondary" onClick={props.handleClose} className="w-full borderBtn">Cancel</Button>
                    </Link>
                </div>
                <div>
                    <AppButton loading={btnLoading} disabled={btnLoading || radioButtons.length === 0} noIcon="d-none" class="wd-btn-add" value="Add Report" color="primary" type="submit" onclick={addSheet} />
                </div>
            </div>
        </>
    )
}

export default EOverviewForm;




