import React, { useState, useEffect } from 'react';
import "../style.scss";

import ReactApexChart from "react-apexcharts";
import moment from 'moment';
import {Para} from "../../commonComponents/parts";
import NotesDrawer from "../../commonComponents/notes_drawer";
import {Button, MenuItem} from "@mui/material";

import ClickAway from "../../commonComponents/click_away";

import Cookies from 'universal-cookie';
import axios from 'axios';
import CHART from "../../commonComponents/chart_palette";
import { rankCeiling } from "../../../utils/rank_state";

function KeywordHistoryChart({ children, ...props }) {
   var series = [];
   var options = {};
   // var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
   
   // PROPS DATA LOADED HERE
   var linechartkwdata = {"k_r": [], "t_c": 135, "lrd": moment().format("MM-DD-YYYY")};
   var revfulldate = [];
   // resscoregraphdetails = props.scoreChartData.dt;
   if(props.kwdata && linechartkwdata.k_r.length === 0){
      // console.log("props.kwdata ", props.kwdata)
      // var a = props.kwdata.RK.slice(0).reverse();
      var a = props.kwdata.RK ? props.kwdata.RK : [];
      var key = props.kwdata.key ? props.kwdata.key.toString().split("~")[0] : 0;

      /* A day with no position becomes a GAP, not a point.
         It used to be plotted at the out-of-range sentinel, which drew a
         line to a place the keyword was never measured at -- and that value
         was not even the ceiling: at the default depth of three pages only
         the first 30 results are searched.
         null leaves the series broken for that day, which is what "we have
         no position for this day" actually looks like. */
      const convertranks = a.map(el => (
         el === 0 ? null : el
      ));
      linechartkwdata = {...linechartkwdata, ...props.kwdata, 'k_r':convertranks, 'key':key}

      var endDate  = moment(linechartkwdata.lrd).format("MM-DD-YYYY");
      var i = 0;
      while(i < linechartkwdata.k_r.length){
         revfulldate.push(moment(endDate).subtract(i, 'days').format("MM-DD-YYYY"));
         i = i+1
      }
      // revfulldate = fulldate;
   }

   // HANDLING MOMENT AND DATE FILTERS 
   var lupdate_date = linechartkwdata.lrd;
   const this_weekday = moment(lupdate_date).day()+1;
   const last_weekday = moment(lupdate_date).day()+8;
   const this_monthday = moment(lupdate_date).date();
   const last_monthday = moment(lupdate_date).subtract(1,'months').daysInMonth()+moment(lupdate_date).date()
   var x = moment(moment(lupdate_date).startOf('quarter').format("MM-DD-YYYY"));
   var y = moment(lupdate_date).format("MM-DD-YYYY");
   const this_quarterday = Math.abs(x.diff(y, 'days'))+1;
   var c = moment(moment(lupdate_date).subtract(1, 'quarter').startOf('quarter').format("MM-DD-YYYY"));
   var d = moment(moment(lupdate_date).subtract(1, 'quarter').endOf('quarter').format("MM-DD-YYYY"));
   const last_quarterday = Math.abs(c.diff(d, 'days'))+Math.abs(x.diff(y, 'days'))+2
   var e = moment(moment(lupdate_date).startOf('year').format("MM-DD-YYYY"));
   var f = moment(lupdate_date).format("MM-DD-YYYY");
   const this_yearday = Math.abs(e.diff(f, 'days'))+1;
   var g = moment(moment(lupdate_date).subtract(1, 'year').startOf('year').format("MM-DD-YYYY"));
   var h = moment(moment(lupdate_date).subtract(1, 'year').endOf('year').format("MM-DD-YYYY"));
   const last_yearday = Math.abs(g.diff(h, 'days'))+Math.abs(e.diff(f, 'days'))+2

   /*var keyword_name = linechartkwdata.KW
   var startdat = linechartkwdata.cd*/

   var enddat = linechartkwdata.lrd
   var totalcount = linechartkwdata.t_c 
   var this_week = this_weekday
   var last_week = last_weekday
   var this_month = this_monthday
   var last_month = last_monthday
   var this_quarter = this_quarterday
   var last_quarter = last_quarterday
   var this_year = this_yearday
   var last_year = last_yearday
   
   // STATE DECLARATIONS
   const notesFunc = React.useRef(null)
   const [stateData, setStateData] = useState({
      loading: true,
      filtervalue : "tweek",
      kwrankfull : linechartkwdata.k_r.slice(0,this_weekday),
      kwrank : linechartkwdata.k_r.slice(0,this_weekday),
      // kwrankfull: [],
      // kwrank: [],
      kwdates: revfulldate.slice(0,this_weekday),
      kwdatesfull: revfulldate,
      // kwdatesfull : [],
      // kwdates : [],
      daterange : [],
      date_pick: false, 
      csvdata: [],
      csvheader: [],

      // notestabVsble: false,
      // notedate: linechartkwdata.lrd,
      // notesloading: false,
      // daynotes: [],
      kwnotesCnt: [],
      kwnotesCntfull: [],
      kwNotesMnthCnt: [],
      notetype : "day",
   }); 


   useEffect(() => {
      // var endDate  = moment(lupdate_date).format("MM-DD-YYYY");
      // var fulldate = [];
      // var i = 0;
      // while(i < linechartkwdata.k_r.length){
      //    fulldate.push(moment(endDate).subtract(i, 'days').format("MM-DD-YYYY"));
      //    i = i+1
      // }
      // var revfulldate = fulldate;
      // setStateData({...stateData, kwdates:revfulldate.slice(0,this_week), kwdatesfull:revfulldate });
   
      const cookies = new Cookies();
      var userid = props.u_id ? props.u_id : cookies.get('session_userid');
      var grpid = props.g_id ? props.g_id : cookies.get('activegrp'); 
      var usertoken = cookies.get('session_token');

      // if(props.ntscnt){
      //    setStateData({
      //       ...stateData, 
      //       loading : false, 
      //       kwnotesCnt : props.ntscnt.slice(0,revfulldate.length),
      //       kwnotesCntfull : props.ntscnt,
      //    })
      // }else 

      if(userid && grpid && linechartkwdata.key) {
         var data = {
            'userid': userid,
            'grpid': grpid,
            'idg': linechartkwdata.key,
            'type': "filter",
            's_p': 0,
            'e_p': this_week,
         };

         axios.post(global.apiurl + '/kw_gph', data, { 
            headers: {'Authorization': 'Token '+ usertoken }
         }).then(response => {
            return response.data; 
         }).then(res => {
            if(res.status === "true") {

               setStateData({
                  ...stateData, 
                  // kwdates: revfulldate.slice(0,this_weekday),
                  // kwdatesfull: revfulldate,
                  // kwrankfull : linechartkwdata.k_r.slice(0,this_weekday),
                  // kwrank : linechartkwdata.k_r.slice(0,this_weekday),

                  loading : false, 
                  kwnotesCnt : res.kw_gph_dtls.ntCnt.slice(0,revfulldate.length),
                  kwnotesCntfull : res.kw_gph_dtls.ntCnt,
               })
            } else {
               // history.push('/serprank')
            }
         }).catch((error) => {
            // history.push('/serprank')
         }); 
      }
   // eslint-disable-next-line react-hooks/exhaustive-deps
   }, [props.ntscnt])

   var { loading, filtervalue, kwdatesfull, kwrank, kwdates, kwrankfull, kwnotesCnt, kwNotesMnthCnt, kwnotesCntfull, notetype } = stateData;

   const handleFilter = (startpos, endpos, value) => {

      if ((filtervalue !== value || value === "custom_date_range")) { 

         if (value === "today") {
            // setOpen(!open);

            setStateData({...stateData, loading: true, kwrank : [], filtervalue : value});
         } else {
            setStateData({...stateData, loading: true, filtervalue : value});
         }

         if((kwdatesfull.length)+1 > endpos || (kwdatesfull.length)+1 > totalcount){
            chartdatachange(startpos, endpos, value);
         } else {
            const cookies = new Cookies();
            var userid = props.u_id ? props.u_id : cookies.get('session_userid');
            var grpid = props.g_id ? props.g_id : cookies.get('activegrp'); 
            var usertoken = cookies.get('session_token');
            // var keywid = linechartkwdata

            if(userid && grpid && linechartkwdata.key) {
               var data = {
                  'userid': userid,
                  'grpid': grpid,
                  'idg': linechartkwdata.key,
                  'type': "filter",
                  's_p': 0,
                  'e_p': endpos,
               };

               axios.post(global.apiurl + '/kw_gph', data, { 
                  headers: {'Authorization': 'Token '+ usertoken }
               }).then(response => {
                  return response.data; 
               }).then(res => {
                  if(res.status === "true") {
                     var linechartkwdata = {...linechartkwdata, ...res.kw_gph_dtls};
                     var endDate  = moment(enddat).format("MM-DD-YYYY");
            
                     var fulldate = [];
                     var i = 0;
                     while(i < linechartkwdata.k_r.length){
                        fulldate.push(moment(endDate).subtract(i, 'days').format("MM-DD-YYYY"));
                        i = i+1
                     }
                     var sltdates = fulldate.slice(startpos,endpos); 
                     var custom_datepick = false
                     var custom_date = []
                     
                     if (value === "custom_date_range") {
                        custom_datepick  = true
                        const start = sltdates[0];
                        const end = sltdates.slice(-1)[0];
                        custom_date = [moment(end), moment(start)]
                     }

                     // Same rule as above: no position that day is a gap.
                     const convertranks = linechartkwdata.k_r.map(el => (
                        el === 0 ? null : el
                     ));

                     setStateData({
                        ...stateData, 
                        kwrankfull : convertranks,
                        kwrank : convertranks.slice(startpos,endpos),
                        loading : false, 
                        kwdatesfull : fulldate, 
                        kwdates: sltdates,
                        filtervalue : value,
                        date_pick : custom_datepick,
                        daterange : custom_date,

                        kwnotesCnt : (endpos-startpos) > 92 ? linechartkwdata.ntMCnt.slice(startpos,endpos) : linechartkwdata.ntCnt.slice(startpos,endpos),
                        kwnotesCntfull : linechartkwdata.ntCnt,
                        kwNotesMnthCnt : linechartkwdata.ntMCnt,
                        notetype : (endpos-startpos) > 92 ? "month" : "day",
                     })
                  } else {
                     // history.push('/serprank')
                  }
               }).catch((error) => {
                  // history.push('/serprank')
               }); 
            }
         }
      } 
   };

   const chartdatachange = (startpos, endpos, value) => { 
      var fulldate = kwdatesfull;
      var custom_datepick = false;

      if (value === "custom_date_range") {
         custom_datepick  = true;
      }

      var update = kwrankfull.slice(startpos, endpos);
      if (update.every( (val, i, arr) => val === arr[0] )) {
         setTimeout(() => {
            setStateData({
               ...stateData, 
               kwrank : update,
               kwdates : fulldate.slice(startpos, endpos),
               filtervalue : value,
               date_pick : custom_datepick,
               loading: false,

               kwnotesCnt : (endpos-startpos) > 92 ? kwNotesMnthCnt.slice(startpos, endpos) : kwnotesCntfull.slice(startpos, endpos),
               notetype : (endpos-startpos) > 92 ? "month" : "day",
            });
         }, 500);
      } else {
         setStateData({
            ...stateData, 
            kwrank : update,
            kwdates : fulldate.slice(startpos, endpos),
            filtervalue : value,
            date_pick : custom_datepick,
            loading : false,
            
            kwnotesCnt : (endpos-startpos) > 92 ? kwNotesMnthCnt.slice(startpos, endpos) : kwnotesCntfull.slice(startpos, endpos),
            notetype : (endpos-startpos) > 92 ? "month" : "day",
         });
      }
   }

   // const [open, setOpen] = React.useState(false);
   // const toggleDrawer = (event) => {
   //    // if (event.type === "keydown" && (event.key === "Tab" || event.key === "Shift")) {
   //    //    return;
   //    // }

   //    setOpen(!open);
   // };

   // const notesopenfun = (event, chartContext, dataPointIndex) => {
   //    console.log("test open notes ", event, chartContext, dataPointIndex)
   //    if(notedate !== kwdates.slice(0).reverse()[dataPointIndex]){
   //       setOpen(!open);

   //        // this.setState({
   //        //     notestabVsble: "2",
   //        //     notesloading: true,
   //        //     notedate: this.state.kwdates.slice(0).reverse()[dataPointIndex],
   //        //     daynotes: [],
   //        // }, this.selectdatenotesget(this.state.kwdates.slice(0).reverse()[dataPointIndex]))
   //    }else{
   //       setOpen(!open);
   //        // this.setState({ notestabVsble: "2", });
   //    }
   // }

   // const notestabfun = (key) => {
   //     this.setState({ notestabVsble: key });
   // }

   /* Bounds from the days that HAVE a position. Math.max/min coerce null to
      0, so leaving the gaps in pinned the axis minimum at 0 and squashed the
      real range into the top of the chart. */
   const plottedRanks = (kwrank || []).filter((el) => typeof el === "number" && el > 0);
   var orgMaxValue = plottedRanks.length ? Math.max(...plottedRanks) : 10;
   var orgMinValue = plottedRanks.length ? Math.min(...plottedRanks) : 1;
   // var orgDiffValue = orgMaxValue - orgMinValue;

   var maxValue = orgMaxValue;
   var minValue = orgMinValue;
   
   // if ((maxValue-minValue) < 5) {
   //    maxValue = maxValue + 1
   //    minValue = minValue - 1
   // } else {
   //    maxValue = Math.max(...kwrank) + 1;
   //    minValue = Math.min(...kwrank) - 1;
   // }

   if(maxValue===minValue || (maxValue-minValue) < 6){
      minValue -= 2
      maxValue += 3
   }else{
      var avg_val = (maxValue-minValue)/4
      minValue = minValue - avg_val
   }

   // var notes = [0,0]
   var notes = kwnotesCnt.slice(0).reverse()
   // var note_icon = global.iconurl+"/static/uploads/notes_gray.png"
   var kwdatesrev = kwdates.slice(0).reverse()
   /* A range whose every reading is a gap has no line to draw. Handing
      ApexCharts a series of nulls draws axes and nothing else, because it
      counts the points and decides it has data -- so noData never fires and
      the chart reads as broken. An empty series lets noData say what was
      actually measured. */
   const ceiling = rankCeiling(props.kwdata);
   const outOfRange = ceiling ? "> " + ceiling : "Not ranked";
   const hasPlotted = plottedRanks.length > 0;
   const gapDays = (kwrank || []).filter((el) => el === null || el === undefined).length;

   series = hasPlotted ? [{
      name: 'Google Rank', 
      type: 'line',
      data: kwrank.slice(0).reverse()
   },{
      name: "Notes",
      type:"scatter",
      data: notes.map((n) => n > 0 ? minValue : null ),
      // data: [null, null],
   }] : [{
      name: 'Google Rank',
      type: 'line',
      data: []
   },{
      name: "Notes",
      type: "scatter",
      data: []
   }];

   options = {
      chart: {
         type: 'line',
         height: 315,
         width: "100%", 
         stacked: false,
         notesCnt : kwnotesCnt.slice(0).reverse(),
         notesdate : notetype,
         // notesCnt : [0,0],
         // notesdate : "month",
         events: {
             click: (event, chartContext, config) => { (config.seriesIndex === 1 && kwnotesCnt.slice(0).reverse()[config.dataPointIndex]) ? notesFunc.current(event, chartContext, config.dataPointIndex) : console.log("") }
             // click: (event, chartContext, config) => { config.seriesIndex === 1 ? this.notesopenfun(event, chartContext, config.dataPointIndex) : (event.target.instance && event.target.instance._stroke === "transparent")? console.log("click", event, chartContext, config.dataPointIndex, config.seriesIndex, event.target.instance._stroke) : console.log("fails",event.target) }
             // markerClick: () => { this.notestabfun() }
             // markerClick: function(event, chartContext, { seriesIndex, dataPointIndex, config}) {
             //     seriesIndex === 1 ?
             //         // this.notesopenfun(event, chartContext, dataPointIndex)
             //         console.log(event, chartContext, seriesIndex, dataPointIndex, config)
             //     :
             //         console.log(event, chartContext, seriesIndex, dataPointIndex, config)
             // },
         },
         zoom: {
            enabled: false,
         }, 
         selection: {
            enabled: false
         }, 
         // animations: {
         //    enabled: true,
         //    // easing: 'easeinout',
         //    easing: 'linear',
         //    speed: 800,
         //    animateGradually: {
         //        enabled: true,
         //        delay: 150
         //    },
         //    dynamicAnimation: {
         //        enabled: false,
         //        speed: 1000
         //    }
         // },
         animations: {
            initialAnimation: { 
               enabled: false
            }
         },
         toolbar: {
            show: false,
            offsetX: 0,
            offsetY: 0, 
            tools: {
               download: false,
               selection: false,
               zoom: false,
               zoomin: false,
               zoomout: false,
               pan: false,
               reset: false, 
            },
         },           
      },
      colors: [CHART.series[0], CHART.note],
      dataLabels: {
         // enabled: ['today', 'tweek', 'lweek', 'tmonth', 'lmonth', ''].includes(filtervalue) ? true : false,
         enabled: false,
      },
      fill: {
         type: ['solid'],
         colors: [CHART.series[0], CHART.note],
         // colors: CHART.series[0],
         // type: 'gradient',
         // gradient: {
         //    shadeIntensity: 1,
         //    inverseColors: false,
         //    opacityFrom: 0.1,
         //    opacityTo: 0,
         //    stops: [0, 95, 100]
         // },
      }, 
      grid: {
         show: true,
         borderColor: "rgba(0,0,0,0.03)",
         position: 'back',
         strokeDashArray: 0,
         padding: {
            top: 0,
            right: 10,
            bottom: 0,
            left: 30
         },
      },
      stroke: {
         curve: 'smooth',
         width: 2,
      },
      markers: {
         // size: 3,
         strokeWidth: 0,
         size: notetype === "month" ? [0.01, 6] : kwrank.length === 1 ? [4, 9] : kwrank.length > 45 ? [2,6] : [3, 6],
         colors: [CHART.series[0], CHART.note],
         // strokeColors: ['#1a3cff', 'transparent'],
         hover: {
            size: 6,
            // sizeOffset: 3
         }
      },  
      xaxis: {
         type: 'categories',
         // tickPlacement: 'between',
         tickPlacement: 'on',
         tickAmount: 15,
         categories: kwdatesrev, 
         labels: {
            formatter: function(value) {
               return moment(value).format("MMM D");    
            },
            style: {
               colors: CHART.label, 
               fontSize: '10px', 
               fontFamily: 'SemiBold',
            },
            offsetY: 5,
         },
         axisBorder: {
            show: false,
         },
         axisTicks: {
            show: true,
            borderType: 'solid',
            color: 'rgba(0,0,0,0.09)',
            height: 5,
         },            
         offsetX: 0,  
         tooltip: {
            enabled: false 
         },
         crosshairs: {
            show: false,
         },
      },
      yaxis: {
         show: linechartkwdata.k_r.length > 0 ? true : false, 
         // tickAmount: orgDiffValue >= 4 ? 5 : parseInt(orgDiffValue + 2), 
         tickAmount: 5, 
         min: parseInt(minValue),
         max: parseInt(maxValue) ,
         reversed: true,
         labels: {
            formatter: function (y) {
               return (y <= minValue || y < 0) ? "Notes" : y ? y.toFixed(0) + "" : 0 ;
            },
            style: {
               colors: CHART.label,
               fontSize: '10px', 
               fontFamily: 'SemiBold',
            },
            offsetX: 0,
         },
         tooltip: {
            enabled: false 
         } 
      },
      legend: {
         show: true, 
         position: "bottom", 
         showForSingleSeries: true, 
         // showForNullSeries: false,
         showForNullSeries: true,
         showForZeroSeries: true, 
         horizontalAlign: 'center', 
         fontFamily: 'SemiBold',
         fontSize: '14px', 
         labels: {
            colors: CHART.label,
            useSeriesColors: false
         },
         offsetY: 35,
         itemMargin: {
             horizontal: 10,
             vertical: 30
         },
         markers: {
            width: 12,
            height: 12,
            radius: 3,
            offsetX: -10,
         },
      },
      tooltip: {
         // shared: false,
         // intersect: true,
         enabled: true,
         // followCursor: true,
         x: {
            formatter: function (val, opts) { return (opts.w.config.chart.notesdate === "month" && opts.seriesIndex === 1) ? moment(kwdatesrev[opts.dataPointIndex]).format("MMMM, YYYY") : val ? moment(kwdatesrev[opts.dataPointIndex]).format("MMM D, YYYY") : moment(kwdates[0]).format("MMM D, YYYY") },
            // formatter: function (val, opts) {  return console.log(val, opts) },
         },
         y: {
            // formatter: function (val, opts) { return opts.seriesIndex === 1 ? notes[parseInt(opts.dataPointIndex)] : val },
            // formatter: function (val, opts) {  return console.log(val, opts, opts.w.config.chart.notesCnt[opts.dataPointIndex]) },
            /* No value for the day means the keyword was measured and not
               found, so the tooltip states the depth rather than the old
               hardcoded ">30", which was only right at the default 3 pages. */
            formatter: function (val, opts) { return (opts.seriesIndex === 1) ? notes[opts.dataPointIndex] : val ? val : outOfRange },
         },
      }, 
      /* Was "No enough data" in --accent, centred over the chart's watermark:
         a grammatical error, drawn in the link colour, on top of the logo, so
         it read as a broken element rather than a state. It is a state, and
         the state is that this range has fewer than two readings -- which is
         normal for a keyword added a day ago. */
      noData: {
         text: loading ? "" : (kwrank || []).length === 0 ? "No readings in this range yet"
            : ceiling ? "Not in the first " + ceiling + " on any day in this range"
            : "Did not rank on any day in this range",
         align: 'center',
         verticalAlign: 'middle',
         offsetX: 0,
         offsetY: -40,
         style: {
            color: "var(--ink-3)",
            fontSize: '14px',
            fontFamily: 'SemiBold',
         }
      }
   } 

	return (
      <div className={props.className}> 
         <div id="chart" className={loading? "" : "charthistory kwchart"} > 
            <div className="wd-history-duration-filter">
               <div className="d-flex align-items-center flex-wrap bg-transparent">

                  <label className={filtervalue === "today" ? "wd-filterLabel active" : "wd-filterLabel"}>
                     <input type="radio" name="radioname" value="one_value" />
                     <div className="wd-filterOption" onClick={()=>handleFilter(0, 1, "today")}> 
                        <span>Today</span>
                     </div>
                  </label>

                  <label className={filtervalue === "tweek" ? "wd-filterLabel active" : "wd-filterLabel"}> 
                     <input type="radio" name="radioname" value="one_value" />
                     <div className="wd-filterOption" onClick={()=>handleFilter(0,this_week,"tweek")}>
                        <span>Week</span>
                     </div>
                  </label>

                  <label className={filtervalue === "tmonth" ? "wd-filterLabel active" : "wd-filterLabel"}>
                     <input type="radio" name="radioname" value="one_value" />
                     <div className="wd-filterOption" onClick={()=>handleFilter(0,this_month,"tmonth")}>
                        <span>Month</span>
                     </div>
                  </label>

                  <label className={filtervalue === "tquarter" ? "wd-filterLabel active" : "wd-filterLabel"}>
                     <input type="radio" name="radioname" value="one_value" />
                     <div className="wd-filterOption" onClick={()=>handleFilter(0,this_quarter,"tquarter")}>
                        <span>Quarter</span> 
                     </div>
                  </label>

                  <label className={filtervalue === "tyear" ? "wd-filterLabel active" : "wd-filterLabel"}>
                     <input type="radio" name="radioname" value="one_value" />
                     <div className="wd-filterOption" onClick={()=>handleFilter(0,this_year,"tyear")}>
                        <span>Year</span>
                     </div>
                  </label>

                  <ClickAway 
                     childclassName="ExportList" 
                     parent={ 
                        <Button
                           color="white"
                           className={['lweek', 'lmonth', 'lquarter', 'lyear'].includes(filtervalue) ? "graghFilter active" : "graghFilter"}
                           variant="contained"
                        >
                           More
                        </Button>
                     }
                  >
                     <MenuItem className={filtervalue === "lweek" ? "primaryActive" : "primaryHover"} onClick={()=>handleFilter(this_week,last_week,"lweek")}>
                        <div className="d-flex"> Last week </div>
                     </MenuItem>

                     <MenuItem className={filtervalue === "lmonth" ? "primaryActive" : "primaryHover"} onClick={()=>handleFilter(this_month,last_month,"lmonth")}>
                        <div className="d-flex"> Last month </div>
                     </MenuItem>

                     <MenuItem className={filtervalue === "lquarter" ? "primaryActive" : "primaryHover"} onClick={()=>handleFilter(this_quarter,last_quarter,"lquarter")}>
                        <div className="d-flex"> Last quarter </div>
                     </MenuItem>

                     <MenuItem className={filtervalue === "lyear" ? "primaryActive" : "primaryHover"} onClick={()=>handleFilter(this_year,last_year,"lyear")}>
                        <div className="d-flex"> Last year </div>
                     </MenuItem>
                  </ClickAway> 

               </div>

               {/*<AppButton
                  value="Download"
                  class="wd-DwnButton"
                  Icon={
                     <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="16"
                        height="15.2"
                        viewBox="0 0 16 15.2"
                     >
                       <path
                           id="Path_411"
                           data-name="Path 411"
                           d="M11.032,11.532l-.232.24V9.7a.8.8,0,1,0-1.6,0v2.072l-.232-.24a.8.8,0,0,0-1.136,1.136l1.6,1.6a.8.8,0,0,0,.264.168.752.752,0,0,0,.608,0,.8.8,0,0,0,.264-.168l1.6-1.6a.8.8,0,0,0-1.136-1.136ZM15.6,4.9H10.576l-.256-.8A2.4,2.4,0,0,0,8.048,2.5H4.4A2.4,2.4,0,0,0,2,4.9V15.3a2.4,2.4,0,0,0,2.4,2.4H15.6A2.4,2.4,0,0,0,18,15.3v-8A2.4,2.4,0,0,0,15.6,4.9Zm.8,10.4a.8.8,0,0,1-.8.8H4.4a.8.8,0,0,1-.8-.8V4.9a.8.8,0,0,1,.8-.8H8.048a.8.8,0,0,1,.76.544L9.24,5.956A.8.8,0,0,0,10,6.5h5.6a.8.8,0,0,1,.8.8Z"
                           transform="translate(-2 -2.5)"
                           fill="#fff"
                       />
                     </svg>
                  }
               />*/} 
            </div>

            <div className="m-t30">
               <div className="gLoaderLabel"> 
                  { loading && 
                    <div className=" d-flex flex-column align-items-center justify-content-center w-100 grphloader">
                        <div className="loading m-b100" />
                    </div>
                  }
                  <ReactApexChart options={options} series={series} type={kwrank.length > 1 ? "line" : "scatter"} height={400} /> 


               </div>
               {/*This graphs shows the number of improved and declined keywords of the day. The graph chages everytime when you refresh your keywords. It accuratly depicts the fluctuations in your organic progress.*/}
               <Para class="wd-GraphDesc w-75 text-center">
               Every recorded position for this keyword over the selected range. A rise on the chart is a move towards position 1.
               {hasPlotted && gapDays > 0 ? " A break in the line is a day the domain was not in the first " + (ceiling || 30) + "." : ""}
               </Para> 
            </div>
         </div>
         <NotesDrawer notesFunc={notesFunc} kwdates={kwdatesrev} notetype={notetype} keyid={linechartkwdata.key} />
         

      </div>
	)
}

export default KeywordHistoryChart;