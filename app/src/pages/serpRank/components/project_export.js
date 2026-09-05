import React, { useState, useEffect, useRef } from "react";
import { rankLabel } from "../../../utils/rank_state";
import { FileExportIcon } from "../../commonComponents/icons";
import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import axios from 'axios';
import { MenuItem } from "@mui/material";
import ClickAway from "../../commonComponents/click_away";
import { CSVLink } from "react-csv";
import { Button } from "@/components/ui/button";
import { getfulldate } from "../../common_fun";

// const csvheadersa = [
//   	{ label: "S.No", key: "sno" },
//   	{ label: "Keyword", key: "keyword" },
//   	{ label: "Rank", key: "Rank" },
//   	{ label: "Best rank", key: "Best rank" },
//   	{ label: "1d", key: "Day" },
//   	{ label: "7d", key: "Week" },
//   	{ label: "Volume", key: "Volume" },
//   	// { label: "Comp", key: "Comp" },
//   	{ label: "URL", key: "URL" },
//   	{ label: "Region", key: "region" },
//   	{ label: "Created on", key: "Created on" }
// ];

const csvheadersat = [
	{ label: "S.No", key: "sno" },
	{ label: "Keyword", key: "KW" },
	{ label: "Rank", key: "RW" },
	{ label: "Best rank", key: "brnk" },
	{ label: "1d", key: "OD" },
	{ label: "7d", key: "SD" },
	{ label: "Volume", key: "SV" },
	// { label: "Comp", key: "Comp" },
	{ label: "URL", key: "SR" },
	{ label: "Region", key: "RG" },
	{ label: "Created on", key: "cd" }
];

function ProjectFileExport(props) {

	const [exporttxt, setExporttxt] = useState([]);
	const [exportcsv, setExportcsv] = useState([]);
	const [exportpdfurl, setExportpdfurl] = useState("");
	const [projectname, setProjectname] = useState("tracker_report");
	const [exportCSVloading, setExportCSVloading] = useState(true);
	const [exportPDFloading, setExportPDFloading] = useState(false);
	const [exportTXTloading, setExportTXTloading] = useState(false);
	const exportBusy = exportCSVloading || exportPDFloading || exportTXTloading;

	// One loading idiom: the top bar. The menu items stay disabled while busy.
	useEffect(() => {
		const loader = global.PageTopLoader && global.PageTopLoader.current;
		if (!loader) return;
		if (exportBusy) loader.continuousStart(); else loader.complete();
	}, [exportBusy]);
	const csvLink = useRef(null);

	useEffect(() => {
		setExporttxt([]);
		// setExportcsv([]);
		setExportpdfurl("");
		setExportcsv([]);

	}, [props.basedata, props.pageupdate, props.refresh_on, props.lstfltrresult]);

	useEffect(() => {

	}, [exportcsv]);

	const exportMenuClick = () => {
		if (props.basedata.hasOwnProperty('NM')) {
			setProjectname(props.basedata.NM.replace(/\s+/g, '-').toLowerCase());
		}

		if (props.lstfltrresult && props.lstfltrresult.length > 0 && props.lstfltrresult[0].KW) {
			// exportCSVdata()
			const srtdata = props.lstfltrresult.sort((a, b) => a.RW > b.RW ? 1 : -1);
			const data = srtdata.map((kw, i) => (
				{
					'sno': i + 1,
					'KW': kw.KW,
					// The export said '>30' while the chart plotted the same value as a
					// position. Both now come from one place, and an unmeasured
					// keyword exports as such rather than as a rank.
					'RW': rankLabel(kw, true),
					'brnk': kw.brnk === 0 ? '-' : kw.brnk,
					'OD': kw.OD === 0 ? '-' : Math.abs(kw.OD).toString() + ' (' + (kw.OD > 0 ? 'up)' : kw.OD < 0 ? 'down)' : null),
					'SD': kw.SD === 0 ? '-' : Math.abs(kw.SD).toString() + ' (' + (kw.SD > 0 ? 'up)' : kw.SD < 0 ? 'down)' : null),
					'SV': kw.SV === '-1' ? '-' : kw.SV,
					'RG': kw.RG ? kw.RG : '-',
					'SR': kw.SR,
					'cd': kw.cd ? getfulldate(kw.cd) : '-',
				}
			));

			setExportcsv(data);
			setExportCSVloading(false);
		}
	}

	/* CSV Export Data API */
	const exportCSVdata = () => {

		const cookies = new Cookies();
		const userid = cookies.get('session_userid');
		const grpid = cookies.get('activegrp');
		const usertoken = cookies.get('session_token')
		if (userid && grpid) {
			setExportCSVloading(true);
			var data = {
				'userid': userid,
				'grpid': grpid,
				'type': 'csv',
			};

			axios.post(global.apiurl + '/export', data, {
				headers: { 'Authorization': 'Token ' + usertoken }
			}).then(response => {
				return response.data;
			}).then(res => {
				if (res.status !== "true") {
				} else {
					setExportcsv(res.data);
					setExportCSVloading(false);
					// exportCSVdownload(res.data);
					// setTimeout(() => {
					// 	exportCSVdownload()
					// }, 1000);
				}
			}).catch((error) => {
				setExportCSVloading(false);
				// history.push("/")
			});
		}
	};

	const exportCSVdownload = () => {
		if (exportcsv.length > 0) {
			csvLink.current.link.click()
			setExportCSVloading(false);
		} else {
			exportCSVdata()
		}
	}

	/* PDF Export Data API */
	const exportpdf = () => {
		if (exportpdfurl !== "") {
			exportPDFdownload(exportpdfurl);
		} else {
			const cookies = new Cookies();
			const userid = cookies.get('session_userid');
			const usertoken = cookies.get('session_token')
			const grpid = cookies.get('activegrp');

			if (userid && grpid) {
				setExportPDFloading(true);
				var data = {
					'userid': userid,
					'grpid': grpid,
				};

				axios.post(global.apiurl + '/pdfexport', data, {
					responseType: 'blob',
					headers: { 'Authorization': 'Token ' + usertoken }
				}).then(response => {
					return response.data;
				}).then((blob) => {
					var url = window.URL.createObjectURL(blob);
					setExportpdfurl(url);
					setExportPDFloading(false);

					exportPDFdownload(url);
				}).catch((error) => {
					setExportPDFloading(false);
					// history.push("/")
				});
			}
		}
	}

	const exportPDFdownload = (url) => {
		var a = document.createElement('a');
		a.href = url;
		a.download = projectname + ".pdf";
		document.body.appendChild(a); // we need to append the element to the dom -> otherwise it will not work in firefox
		a.click();
		a.remove();  //afterwards we remove the element again 
	}

	//Export txt file
	const exporttxtfun = () => {
		if (exporttxt.length > 0) {
			exportTXTdownload(exporttxt);
		} else {
			const cookies = new Cookies();
			const userid = cookies.get('session_userid');
			const usertoken = cookies.get('session_token')
			const grpid = cookies.get('activegrp');

			if (userid && grpid) {
				setExportTXTloading(true)

				var data = {
					'userid': userid,
					'grpid': grpid,
					'type': 'txt',
				};

				axios.post(global.apiurl + '/export', data, {
					headers: { 'Authorization': 'Token ' + usertoken }
				}).then(response => {
					return response.data;
				}).then(res => {
					if (res.status !== "true") {
					} else {
						setExporttxt(res.txtdata);
						setExportTXTloading(false);
						exportTXTdownload(res.txtdata);
					}
				}).catch((error) => {
					setExportTXTloading(false);
					// history.push("/")
				});
			}

		}
	}

	const exportTXTdownload = (data) => {
		var rp_data = (data).join('\n')
		const a = document.createElement("a");
		a.href = URL.createObjectURL(new Blob([rp_data], { type: "text/plain" }));
		a.setAttribute("download", projectname + ".txt");
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
	}

	/* Export on refresh run time */
	const exportRefrsAlert = () => {
		toast.error("Please wait! Until the completion of your refresh.")
	}

	return (
		<div onClick={exportMenuClick}>
			<ClickAway
				childclassName="ExportList"
				parent={<Button variant="secondary" className="w-full borderBtn darkgray"><span className="d-flex m-r10"><FileExportIcon className="" /></span><span>Export</span></Button>}
			>
				<MenuItem className="primaryHover" onClick={exportCSVloading ? null : props.refresh_on ? exportRefrsAlert : exportCSVdownload} disabled={exportCSVloading} >
					<div className="d-flex justify-content-between">
						<div className="m-r20"> Export project in .CSV </div>
					</div>
				</MenuItem>
				<MenuItem className="primaryHover" onClick={exportPDFloading ? null : props.refresh_on ? exportRefrsAlert : exportpdf} disabled={exportPDFloading} >
					<div className="d-flex justify-content-between">
						<div className="m-r20"> Export project in .PDF </div>
					</div>
				</MenuItem>
				<div className="brdBottom m-t5 m-b5 m-l10 m-r10" />
				<MenuItem className="primaryHover" onClick={exportTXTloading ? null : props.refresh_on ? exportRefrsAlert : exporttxtfun} disabled={exportTXTloading} >
					<div className="d-flex justify-content-between">
						<div className="m-r5"> Export keywords in .TXT </div>
					</div>
				</MenuItem>
				<CSVLink
					data={exportcsv}
					headers={csvheadersat}
					// asyncOnClick={true}
					filename={projectname + ".csv"}
					ref={csvLink}
					target="_blank"
				/>
			</ClickAway>
		</div>
	);
}
export default ProjectFileExport;
