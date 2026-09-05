import React, { useEffect, useState } from "react";
import { GoogleIcon, GoOverviewPageIcon } from "../../commonComponents/icons";
import { openLiveGoogleSerp } from "../../common_fun";
import { toast } from "react-toastify";
import { Tooltip } from "@mui/material";

function KWGooglePage(props) {

	const [grespg_loading, setGrespg_loading] = useState({});
	const busy = Object.keys(grespg_loading).length > 0;

	// One loading idiom: the top bar.
	useEffect(() => {
		const loader = global.PageTopLoader && global.PageTopLoader.current;
		if (!loader) return;
		if (busy) loader.continuousStart(); else loader.complete();
	}, [busy]);

	/* Google View Result Page */
	const glassview = async (key) => {
		const keywordId = parseInt(key.toString().split("~")[0], 10);
		if (!keywordId) return;
		setGrespg_loading({ [key]: true });
		try {
			await openLiveGoogleSerp(keywordId);
		} catch (error) {
			toast.error(error.message || "Could not open live Google results");
		} finally {
			setGrespg_loading({});
		}
	}

	return (
		props.pagetype === "kwoverview" ?
			<button type="button" disabled={busy} onClick={() => glassview(props.row.key)} className="kwFactAction d-flex align-items-center pClr f14x lh18x cursorP m-b15">
			   View live SERP
			   <div className="circleGpageArrow m-l5">
			      <GoOverviewPageIcon height={18} width={18} />
			   </div>
			</button>
		:
			<Tooltip classes={{ tooltip: "p-2" }} title={
			   <div className="lh18x">
			      <div className="f-semi f-sm pClr fM secndname"> Google </div>
			      	<div className="f12x fstname lightTxtClr"> Result page </div>
			   </div> } placement="top">
			   <button type="button" disabled={busy} aria-label={`Open live Google results for ${props.row.KW || "keyword"}`} className="iconAction cursorP d-flex" onClick={() => glassview(props.row.key)} >
					<GoogleIcon />
				</button>
         </Tooltip>
	);
}
export default KWGooglePage;
