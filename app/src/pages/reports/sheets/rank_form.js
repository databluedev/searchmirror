import React, { useEffect, useState } from 'react';
import { Link, useHistory } from "react-router-dom";
import { Input, SelectMenu, AppButton } from "../../commonComponents/parts";
import { Button } from "@/components/ui/button";
import { Grid, InputLabel } from '@mui/material';
import Cookies from 'universal-cookie';

import '../style.scss';
import axios from 'axios';
import { toast } from 'react-toastify';

const RankForm = (props) => {

    /* The range starts at 2, not 1, because 1 is not a range this backend can
       build. keyword_ranking_report (serp/widget.py) computes two week columns
       unconditionally and only adds a third from duration_limit 3 up, so
       "Past 1 week" and "Past 2 weeks" produced byte-identical reports. On the
       monthly side KeywordRankingMonthlySerializer slices the periods to
       duration_limit and then reads monthly_ranking[1] for MOM Change
       (report_serializers.py:299), which raises on a one-element slice and
       silently drops the change column from every row.

       overview_form.js already dropped both and left the originals commented
       above its lists; this form and its e-commerce clone still offered them. */
    const weekDays = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    const monthDays = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    const weekIntervals = ["Past 2 weeks", "Past 3 weeks", "Past 4 weeks", "Past 5 weeks", "Past 6 weeks", "Past 7 weeks", "Past 8 weeks", "Past 9 weeks", "Past 10 weeks", "Past 11 weeks", "Past 12 weeks"];
    const monthINterval = ["Past 2 months", "Past 3 months", "Past 4 months", "Past 5 months", "Past 6 months", "Past 7 months", "Past 8 months", "Past 9 months", "Past 10 months", "Past 11 months", "Past 12 months"];
    const orderByVals = ['Ascending', 'Descending']
    /* "Weekly Schedule" / "Monthly Schedule" promised a delivery cadence.
       Nothing in this instance delivers a report on a timer: ReportManager
       rows are created with download_link "NA" and no scheduler ever reads
       track_status back. The choice is real, but what it sets is the period
       one column covers -- a week or a month -- which the report is rebuilt
       against live on every load. Same two words overview_form.js uses. */
    const patchSchedule = ["Weekly", "Monthly"];

    const initialState = {
        sheetName: "",
        selectedMetrics: ["landing_pages", "base_ranking"],
        trackDay: 2,
        trackInterval: ['Past 2 weeks'],
        trackOnMonth: ['Past 3 months'],
        orderBy: ['Ascending'],
        btnLoading: false,
        scheduleInterval: ['Weekly']
    }

    const [data, setData] = useState(initialState);

    const [errMsg, setErrMsg] = useState({
        trackDayBug: "",
        sheetNameBug: "",
        trackScheduleBug: "",
        trackMonthBug: ''
    });

    var { trackDayBug, sheetNameBug, trackScheduleBug, trackMonthBug } = errMsg;
    var { sheetName, selectedMetrics, trackDay, trackInterval, orderBy, btnLoading, scheduleInterval, trackOnMonth } = data;

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

    const handleOrderBy = (e) => {
        var { target: { value }, } = e;
        value = (typeof value === "string") ? value.split(",") : value[0];
        setData(data => ({ ...data, orderBy: value }))
    }

    const handleTrackDay = (e) => {
        var { target: { value }, } = e;
        value = (typeof value === "string") ? value.split(",") : value[0];

        setData({
            ...data,
            trackInterval: value,
        })

        setErrMsg({
            ...errMsg,
            trackDayBug: "",
        })
    };

    const handleMonthTrackDay = (e) => {
        var { target: { value }, } = e;
        value = (typeof value === "string") ? value.split(",") : value[0];

        setData({
            ...data,
            trackOnMonth: value,
        })

        setErrMsg({
            ...errMsg,
            trackMonthBug: "",
        })
    };

    const addSheet = async (e) => {
        var flag = 1
        var schedule_level = "weekly";
        var reportDuration = trackDay;
        setData(data => ({ ...data, btnLoading: true }))

        // var intervalIndex = weekIntervals.indexOf(trackInterval.toString().trim());  
        // if (intervalIndex !== -1) {
        //     trackDay = weekDays[intervalIndex];  
        // }

        if (scheduleInterval[0] === "Monthly") {
            schedule_level = "monthly";
            reportDuration = 3;

            var intervalIndex = monthINterval.indexOf(trackOnMonth.toString().trim());
            if (intervalIndex !== -1) {
                reportDuration = monthDays[intervalIndex];
            }
        } else {
            var intervalIndex = weekIntervals.indexOf(trackInterval.toString().trim());
            if (intervalIndex !== -1) {
                reportDuration = weekDays[intervalIndex];
            }
        }
        if (sheetName.length <= 0) {
            flag = 0;
            toast.error("Please enter the sheet name.");
        } else if (selectedMetrics.length < 1) {
            flag = 0;
            toast.error("Choose at least one ranking metric.");
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
                    'metrics': selectedMetrics,
                    'type': "keyword_ranking",
                    'schedule': schedule_level,
                    'duration': reportDuration,
                    'change': ["number"],
                    'orderby': orderBy[0]
                };

                // axios.post(global.apiurl + '/dF9rZYWRkXb21ldH3JlcG9y3JkXXl3JY3Mp', data, {

                await axios.post(global.apiurl + '/dF9rZYWRkXb21ldH3JlcG9y3JkXXl3JY3Mp', data, {
                    headers: { 'Authorization': 'Token ' + usertoken }
                }).then(response => {
                    return response.data;
                }).then(r => {
                    if (r.st === 1) {
                        toast.success(r.message)
                        setData(data => ({ ...data, btnLoading: false }))
                        props.setData(data => ({ ...data, rlFlg: true }))
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

    const handleMetrics = (value, checked) => {
        setData(current => ({
            ...current,
            selectedMetrics: checked
                ? [...new Set([...current.selectedMetrics, value])]
                : current.selectedMetrics.filter(metric => metric !== value),
        }))
    }

    const handleChecked = (name) => {
        return selectedMetrics.includes(name) ? true : false;
    }

    const handleScheduleInterval = (e) => {
        var { target: { value }, } = e;
        value = (typeof value === "string") ? value.split(",") : value[0];

        setData({
            ...data,
            scheduleInterval: value,
        })

        setErrMsg({
            ...errMsg,
            trackScheduleBug: "",
        })
    };

    return (
        <>
            <div id="drp-rank-content" className="m-b20">
                <div className="m-b20 maxW300x">
                    <h2 className="fB f15x m-b5">
                        Report Name <span className="redClr">*</span>
                    </h2>
                    <Input placeholder="Ex: Keyword Ranking" value={sheetName} onchange={handleSheetName} errmsg={sheetNameBug} error={sheetNameBug.length > 0} />
                </div>
            </div>

            <Grid container spacing={3}>
                <Grid item xs={12} md={12} lg={12}>
                    <div className="m-b20 drp-inner-block">
                        <div>
                            <div className="m-b10">
                                <h2 className="fB f15x m-b5">
                                    Metrics
                                </h2>
                            </div>
                            <div className="drp-border m-t10  m-b10" />
                            <div className="grid grid-cols-3 justify-items-start h-[80px] items-center">
                                {/* Locked on, not unavailable: every ranking
                                    report emits the keyword column
                                    (report_serializers.py:149), so it is the one
                                    metric that cannot be turned off. */}
                                <div className="customRadio" title="Every ranking report has a keyword column">
                                    <label className="labl">
                                        <input type="checkbox" checked={true} disabled={true} name="radioname" value={"keywords"} />
                                        <div>
                                            <span className="border" />
                                            <span className="f14x">Keywords</span>
                                        </div>
                                    </label>
                                </div>

                                {/* <div className="customRadio">
                                  <label className="labl">
                                  <input type="checkbox" name="radioname" value={"target_url"} 
                                    checked={handleChecked("target_url")} 
                                    onChange={(e) => handleMetrics(e.target.value, e.target.checked)} 
                                  />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Target Url</span>
                                  </div>
                                  </label> 
                               </div> */}

                                {/* Not an OAuth question: search volume comes from
                                    the Google Ads Keyword Planner, and
                                    serp/searchvolume.py returns without calling
                                    it whenever files/google-ads.yaml is absent,
                                    which is the normal state here. Every keyword
                                    keeps the "init" default, so the column is
                                    dashes on every row. */}
                                <div className="customRadio" title="Needs Google Ads API credentials, which this instance does not have">
                                    <label className="labl opacity-60">
                                        <input type="checkbox" checked={false} disabled />
                                        <div>
                                            <span className="border" />
                                            <span className="f14x">Search Volume <small>(Google Ads later)</small></span>
                                        </div>
                                    </label>
                                </div>

                                <div className="customRadio">
                                    <label className="labl">
                                        <input type="checkbox" name="radioname" value={"landing_pages"}
                                            checked={handleChecked("landing_pages")}
                                            onChange={(e) => handleMetrics(e.target.value, e.target.checked)}
                                        />
                                        <div>
                                            <span className="border" />
                                            <span className="f14x">Ranking Url</span>
                                        </div>
                                    </label>
                                </div>

                                <div className="customRadio">
                                    <label className="labl">
                                        <input type="checkbox" name="radioname" value={"base_ranking"}
                                            checked={handleChecked("base_ranking")}
                                            onChange={(e) => handleMetrics(e.target.value, e.target.checked)}
                                        />
                                        <div>
                                            <span className="border" />
                                            <span className="f14x">Base Rank</span>
                                        </div>
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div className='d-flex flex-wrap gap-3'>
                            <div>
                                <div className="m-t30 m-b20">
                                    <h2 className="fB f15x m-b5">
                                        Duration
                                    </h2>
                                    <div className="drp-border m-t10  m-b10" />
                                </div>

                                <div className="m-b20">
                                    <InputLabel shrink className="">
                                        Period & Range
                                        <span className="redClr">
                                            {" *"}
                                        </span>
                                    </InputLabel>
                                    <div className='d-flex'>
                                        <div className="w200x m-r10">
                                            <SelectMenu value={scheduleInterval} menulist={patchSchedule} placeholder="Select" onchange={handleScheduleInterval} errmsg={trackScheduleBug} error={trackScheduleBug.length > 0} />
                                        </div>
                                        {scheduleInterval[0] === "Weekly" ?
                                            <div className="w200x">
                                                <SelectMenu value={trackInterval} menulist={weekIntervals} placeholder="Select" onchange={handleTrackDay} errmsg={trackDayBug} error={trackDayBug.length > 0} />
                                            </div>
                                            :
                                            <div className="w200x">
                                                <SelectMenu value={trackOnMonth} menulist={monthINterval} placeholder="Select" onchange={handleMonthTrackDay} errmsg={trackMonthBug} error={trackMonthBug.length > 0} />
                                            </div>
                                        }
                                    </div>
                                </div>
                            </div>
                            <div>
                                <div className="m-t30 m-b20">
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

                                    <div className="w200x">
                                        <SelectMenu value={orderBy} menulist={orderByVals} placeholder="Select" onchange={handleOrderBy} errmsg={trackDayBug} error={trackDayBug.length > 0} />
                                    </div>
                                </div>
                            </div>
                        </div>

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
                    <AppButton loading={btnLoading} noIcon="d-none" class="wd-btn-add" value="Add Report" color="primary" type="submit" onclick={addSheet} />
                </div>
            </div>
        </>
    )
}

export default RankForm;



