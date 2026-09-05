import React, { useEffect, useState } from 'react';
import { Link } from "react-router-dom";
import { Input, SelectMenu, AppButton } from "../../commonComponents/parts";
import { Button } from "@/components/ui/button";
import { Grid, InputLabel } from '@mui/material';
import Cookies from 'universal-cookie'; 

import '../style.scss';
import axios from 'axios';
import { toast } from 'react-toastify';

const EBaseForm = (props) => {

    const monthDays = [1,2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    const monthIntervals = ["Past 1 month", "Past 2 months", "Past 3 months", "Past 4 months", "Past 5 months", "Past 6 months", "Past 7 months", "Past 8 months", "Past 9 months", "Past 10 months", "Past 11 months", "Past 12 months"];
    const orderByVals = ['Ascending', 'Descending']

    const initialState = {
        sheetName: "", 
        trackDay: 3, 
        trackInterval: ['Past 3 months'],
        compareMetrics: [],
        orderBy: ['Ascending'],
        btnLoading:false
    }

    const [data, setData] = useState(initialState);

    const [errMsg, setErrMsg] = useState({
        trackDayBug: "",
        sheetNameBug: "", 
    });

    var { trackDayBug, sheetNameBug } = errMsg; 
    var { sheetName, trackDay, trackInterval, compareMetrics, orderBy, btnLoading } = data;  

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

    const handleOrderBy=(e)=>{
        var { target: { value },} = e;
        value = (typeof value === "string") ? value.split(",") : value[0];
        setData(data=>({...data, orderBy:value}))
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

    const handleMetrics = (value, checked) => {
      var rprtValues = compareMetrics;
      if(checked) { 
         if(rprtValues.indexOf(value) === -1) {
            rprtValues.push(value)
            setData({
               ...data,
               compareMetrics: rprtValues, 
            }) 
         }
      } else {
         var removeIndex = rprtValues.indexOf(value); 
         if(removeIndex !== -1) {
            rprtValues.splice(removeIndex, 1)
            setData({
               ...data,
               compareMetrics: rprtValues, 
            })
         }
      } 
    }

    const handleChecked = (name) => {
      return compareMetrics.includes(name) ? true : false; 
    }

    const addSheet = async(e) => {
        var flag = 1
        var trackDay = 3;
        var schedule_level = "monthly";
        setData(data=>({...data, btnLoading:true}))

        var intervalIndex = monthIntervals.indexOf(trackInterval.toString().trim());  
        if (intervalIndex !== -1) {
            trackDay = monthDays[intervalIndex];  
        }

        if (sheetName.length <=0 ) {
            flag = 0;
            toast.error("Please enter the sheet name.");
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
                    'sheet' : sheetName,
                    'type': "domain_metrics",  
                    'schedule': schedule_level,   // monthly
                    'duration': trackDay, 
                    'change': compareMetrics,    // number or percentage 
                    'orderby': orderBy[0]
                }; 

                // axios.post(global.apiurl + '/dF9kb21YG9yhaW5cWV0cmljfbWRkX3Jlcw', data, {

                await axios.post(global.apiurl + '/e-domain_sheet', data, {
                    headers: { 'Authorization': 'Token ' + usertoken }
                }).then(response => {
                    return response.data;
                }).then(r => { 
                    if (r.st === 1) { 
                        toast.success(r.message)
                        setData(data=>({...data, btnLoading:false}))
                        props.setData(data=>({...data, rlFlg:true}))
                        
                        // TIME DELAY AFTER THE TOAST MESSAGE 
                        // setTimeout(() => {
                        //     window.location.reload(); 
                        // }, 1500);
                        setData(initialState)
                        props.handleClose()

                    } else {
                        toast.error(r.message)
                        setData(data=>({...data, btnLoading:false}))
                    }
                }).catch((error) => {
                    toast.error(error.message)  
                    setData(data=>({...data, btnLoading:false}))
                });
            }   
        }
        setData(data=>({...data, btnLoading:false}))
    }   

    return (
        <>
            <div id="drp-rank-content" className="m-b20">
                <div className="m-b20 maxW300x">
                    <h2 className="fB f15x m-b5">
                       Report Name <span className="redClr">*</span>
                    </h2>
                    <Input placeholder="Ex: Domain Metrics" value={sheetName} onchange={handleSheetName} errmsg={sheetNameBug} error={sheetNameBug.length > 0} /> 
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
                            <div className="grid grid-cols-4 justify-items-start h-[40px] items-center">
                               <div className="customRadio py-1">
                                  <label className="labl">
                                  <input type="checkbox" checked={true} disabled={true} name="radioname" value={"keywords"} />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Domain Authority (MOZ)</span>
                                  </div>
                                  </label>
                               </div>

                               <div className="customRadio py-1">
                                  <label className="labl">
                                  <input type="checkbox" checked={true} disabled={true} name="radioname" value={"keywords"} />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Domain Rating (AHREF)</span>
                                  </div>
                                  </label>
                               </div>
                               <div className="customRadio py-1">
                                  <label className="labl">
                                  <input type="checkbox" checked={true} disabled={true} name="radioname" value={"keywords"} />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Number of Backlinks (AHREF)</span>
                                  </div>
                                  </label>
                               </div>

                               <div className="customRadio py-1">
                                  <label className="labl">
                                  <input type="checkbox" checked={true} disabled={true} name="radioname" value={"keywords"} />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Referring Domains (AHREF)</span>
                                  </div>
                                  </label>
                               </div>

                               <div className="customRadio py-1">
                                  <label className="labl">
                                  <input type="checkbox" checked={true} disabled={true} name="radioname" value={"keywords"} />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Mobile Speed</span>
                                  </div>
                                  </label>
                               </div>

                               <div className="customRadio py-1">
                                  <label className="labl">
                                  <input type="checkbox" checked={true} disabled={true} name="radioname" value={"keywords"} />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Desktop Speed</span>
                                  </div>
                                  </label>
                               </div>

                               <div className="customRadio py-1">
                                  <label className="labl">
                                  <input type="checkbox" checked={true} disabled={true} name="radioname" value={"keywords"} />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Core web vital(Mobile)</span>
                                  </div>
                                  </label>
                               </div>

                               <div className="customRadio py-1">
                                  <label className="labl">
                                  <input type="checkbox" checked={true} disabled={true} name="radioname" value={"keywords"} />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Mobile Friendliness</span>
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
                                    Monthly Interval
                                    <span className="redClr">
                                        {" *"}
                                    </span>
                                </InputLabel>

                                <div className="maxW300x">
                                    <SelectMenu value={trackInterval} menulist={monthIntervals} placeholder="Select" onchange={handleTrackDay} errmsg={trackDayBug} error={trackDayBug.length > 0} />
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

                                <div className="maxW300x">
                                    <SelectMenu value={orderBy} menulist={orderByVals} placeholder="Select" onchange={handleOrderBy} errmsg={trackDayBug} error={trackDayBug.length > 0} />
                                </div>
                           </div>
                        </div>
                        </div>

                        <div>
                            <div className="m-t30">
                                <h2 className="fB f15x m-b5"> 
                                   Comparison
                                </h2>
                                <div className="drp-border m-t10 m-b10" /> 
                            </div>

                            <div className="grid grid-cols-3 justify-items-start h-[40px] items-center">
                                <div className="customRadio">
                                  <label className="labl">
                                  <input type="checkbox" name="units_name" value={"number"}
                                    checked={handleChecked("number")} 
                                    onChange={(e) => handleMetrics(e.target.value, e.target.checked)} />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">{"Change in Number"}</span> 
                                  </div>
                                  </label>
                                </div>

                                <div className="customRadio">
                                  <label className="labl">
                                  <input type="checkbox" name="units_name" value={"percentage"}
                                    checked={handleChecked("percentage")}
                                    onChange={(e) => handleMetrics(e.target.value, e.target.checked)} />
                                  <div>
                                     <span className="border" />
                                     <span className="f14x">Change in Percentage</span>
                                  </div>
                                  </label>
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

export default EBaseForm;




