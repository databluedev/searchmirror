import React, { useState, useEffect } from "react";
import { Para, TextLg, Text, SmallText, Title, AppTooltip, Tsk } from "../../commonComponents/parts";
import { Grid, Box, Rating, Tooltip, Zoom } from "@mui/material";
import Pie from "../../commonComponents/pie";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { FillArrow, DesktopSmallIcon, MobileSmallIcon, StarFullIcon, FeatureSnptIcon, AdbottomIcon, AdTopBottomIcon, AdTopIcon } from "../../commonComponents/icons";
import { Arrow } from "../../common_fun";


export const SerpOverview = (props) => {
	// const [value, setValue] = useState(2);
	const [prjtstatus, setPrjtstatus] = useState({});
	const [loading, setLoading] = useState(true);

	const Comparison = (
		<div>
			<Para class="m-0">
				View the status of keywords that are categorized based on top 100 positions. The 'Today' and 'Best' for each category denotes the number of keywords. It also provides you details on the number of keywords that haven't ranked.
			</Para>
			{/*This gives you the present ranking and the best ranking of your top 100 keywords on Google's SERP along with number of keywords that haven't ranked.*/}
			{/* <p className="mb-0 m-t10 fB pClr">More info</p> */}
		</div>
	);
	//
	const Device = (
		<div>
			<Para class="m-0">
				The total number of keywords, whose rankings are tracked on mobile as well as the desktop is shown here.
			</Para>
			{/*This shows the number of keywords ranked for this project on mobile tracking and on desktop tracking.*/}
		</div>
	);
	const Performance = (
		<div>
			<Para class="m-0">
				Observe the number of keywords improved and declined in rankings, along with those keywords that haven't seen any change in their ranking positions. Later, analyze your day's performance based on this data.
			</Para>
			{/*This shows the the number of keywords improved and declined in rankings with the keywords without any change in their rankings. All of these determines the performance of your site.*/}
		</div>
	);
	const SScore = (
		<div>
			<Para class="m-0">
				Each tracked keyword contributes according to its current Google position. First position has the most weight; an unranked keyword contributes zero. The result is normalized to a score out of 100.
			</Para>
		</div>
	);
	const Features = (
		<div>
			<Para class="m-0">
				Know the change in your keyword ratings and when your site gets featured in the feature snippets. These are just two vital SERP features, scroll down to the bottom of this page and know about the remaining features from the SERP Legend.
			</Para>
		</div>
	);
	const Google = (
		<div>
			<Para class="m-0">
				Google search Ads for the keywords of this project.
			</Para>
		</div>
	);

	/* Every row of the Comparison card carries the same four cells, so the row
	   is written once and the six categories read from the same three maps. The
	   old markup repeated the block per category and set the column widths by
	   hand on every cell (40% + 30% + 30% + 30% = 130%), which overflowed the
	   card. The cells are now one grid -- see .cmpTable in _surfaces.scss. */
	const comparisonRows = [
		{ label: "Top 1", key: "1" },
		{ label: "Top 3", key: "3" },
		{ label: "Top 10", key: "10" },
		{ label: "Top 50", key: "50" },
		{ label: "Top 100", key: "100" },
		{ label: "Not Ranked", key: "nr" },
	];

	const ratingRows = [
		{ key: "R2", stars: 2, band: "(0-2)" },
		{ key: "R4", stars: 4, band: "(2-4)" },
		{ key: "R5", stars: 5, band: "(4-5)" },
	];

	const adsRows = [
		{ label: "Above & below the fold", key: "Atb", icon: <AdTopBottomIcon /> },
		{ label: "Above the fold", key: "At", icon: <AdTopIcon /> },
		{ label: "Below the fold", key: "Ab", icon: <AdbottomIcon /> },
	];

	// The bucket is absent until the request lands. Reading a key off it while
	// it is still undefined threw; show the skeleton instead.
	const cell = (bucket, key) =>
		bucket ? bucket[key] : (loading ? <Tsk width={30} /> : null);


	useEffect(() => {
		// The request and the settle timeout below both outlive a route change
		// unless they are torn down here; their callbacks then call setPrjtstatus
		// and setLoading on a component that is already gone.
		const controller = new AbortController();
		let settleTimer = null;
		setPrjtstatus({})
		setLoading(true)
		const cookies = new Cookies();
		const usertoken = cookies.get('session_token')
		const userid = cookies.get('session_userid')
		const grpid = cookies.get('activegrp')
		if (!grpid) { return; }   // no project: nothing to ask about

		var data = {
			'userid': userid,
			'grpid': grpid,
		};
		axios.post(global.apiurl + '/projectoverview', data, {
			headers: { 'Authorization': 'Token ' + usertoken },
			signal: controller.signal
		}).then(response => {
			return response.data;
		}).then(res => {
			if (res.status !== "true") {
				//props.updateOverview("close");
			} else {
				settleTimer = setTimeout(() => {
					setPrjtstatus(res.data)
					setLoading(false)
				}, 1000)
			}
		}).catch((error) => {
			// history.push("/")
		});

		return () => {
			controller.abort();
			clearTimeout(settleTimer);
		};

	}, [props.basedata]);

	/* Is there a previous measurement to compare this score against? t_c is how
	   many the score is built from -- the same field /erocs_wdt returns as
	   dt.t_c. Below 2 there is no yesterday, and yss is a fallback value rather
	   than a reading: /projectoverview zeroes it, /homeauth copies ss, and both
	   are guesses about a day that was never measured. Absent t_c (an older
	   backend) this is false and the comparison is simply not drawn, which is
	   the safe direction -- silence is not a wrong claim. */
	const hasPrevious = Number(prjtstatus.t_c) > 1;

	return (
		<Grid container spacing={2} className={"projectSection m-t20 " + props.className}>
			<Grid item xs={12} md={12} lg={12} xl={4} className="ovCol">
				<div className="whiteCard">

					<div className="cardHead">
						<TextLg class="mb-0 lineHAuto">
							Comparison
							<span className="m-l5">
								<AppTooltip place="bottom-end" title={Comparison} />
							</span>
						</TextLg>
					</div>

					<div className="cmpTable">
						<span className="ovHead">Status</span>
						<span className="ovHead">Today</span>
						<span className="ovHead">Yesterday</span>
						<span className="ovHead">Best</span>

						{comparisonRows.map((row) => (
							<React.Fragment key={row.key}>
								<div className="ovLabel">{row.label}</div>
								<div className="ovNum">{cell(prjtstatus.tR, row.key)}</div>
								<div className="ovNum">{cell(prjtstatus.yR, row.key)}</div>
								<div className="ovNum">{cell(prjtstatus.bR, row.key)}</div>
							</React.Fragment>
						))}
					</div>
				</div>
			</Grid>

			<Grid item xs={12} md={12} lg={12} xl={8}>
				<Grid container spacing={2}>
					<Grid item xs={12} md={12} lg={12} xl={3} className="ovCol">
						<div className="whiteCard">
							<div className="cardHead">
								<TextLg class="mb-0 lineHAuto">
									Device
									<span className="m-l5">
										<AppTooltip place="bottom-end" title={Device} />
									</span>
								</TextLg>
							</div>
							<div>
								<div className="ovRow">
									<div className="ovLabel">
										<DesktopSmallIcon />
										<span>Desktop</span>
									</div>
									<div className="ovNum">{loading ? <Tsk width={20} /> : prjtstatus.pD}</div>
								</div>
								<div className="ovRow">
									<div className="ovLabel">
										<span className="w15x text-center"><MobileSmallIcon /></span>
										<span>Mobile</span>
									</div>
									<div className="ovNum">{loading ? <Tsk width={20} /> : prjtstatus.pM}</div>
								</div>
							</div>
						</div>
					</Grid>
					<Grid item xs={12} md={12} lg={12} xl={5} className="ovCol">
						<div className="whiteCard">
							<div className="cardHead">
								<TextLg class="mb-0 lineHAuto">
									Today's Performance
									<span className="m-l5">
										<AppTooltip place="bottom-end" title={Performance} />
									</span>
								</TextLg>
							</div>
							<Grid container spacing={1}>
								<Grid item xs={4} md={4} className="p-l0">
									<div className="status bg-transparent p-0">
										<Text class="ovTileLabel mb-2 d-flex align-items-center gap-1 justify-content-center">
											<span className="lineHTen">Improved</span>
										</Text>
										<Title class="my-1 d-flex align-items-center gap-2 justify-content-center">
											<Tooltip title={"Yesterday it was " + prjtstatus.yik} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
												<div className="d-flex align-items-center gap-2">
													<span>{loading ? <Tsk width={20} /> : prjtstatus.ik}</span>
													<Arrow status={prjtstatus.ik - prjtstatus.yik} type={"normal"} y_sts={prjtstatus.yik} tooltip={false} />
												</div>
											</Tooltip>
										</Title>
									</div>
								</Grid>

								<Grid item xs={4} md={4}>
									<div className="status bg-transparent p-0">
										<Text class="ovTileLabel mb-2 d-flex align-items-center gap-1 justify-content-center">
											<span className="lineHTen">Declined</span>
										</Text>
										<Title class="my-1 d-flex align-items-center gap-2 justify-content-center">
											<Tooltip title={"Yesterday it was " + prjtstatus.ydk} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
												<div className="d-flex align-items-center gap-2">
													<span>{loading ? <Tsk width={20} /> : prjtstatus.dk}</span>
													<Arrow status={prjtstatus.dk - prjtstatus.ydk} type={"Declined"} y_sts={prjtstatus.ydk} tooltip={false} />
												</div>
											</Tooltip>
										</Title>
									</div>
								</Grid>

								<Grid item xs={4} md={4}>
									<div className="status bg-transparent p-0">
										<Text class="ovTileLabel mb-2 d-flex align-items-center gap-1 justify-content-center">
											<span className="lineHTen">No Change</span>
										</Text>
										<Title class="my-1 d-flex align-items-center gap-2 justify-content-center">
											<span>{loading ? <Tsk width={20} /> : prjtstatus.nk}</span>
											{/*<Arrow status={prjtstatus.nk-prjtstatus.ynk} type={"normal"} y_sts={prjtstatus.ynk} />*/}
										</Title>
									</div>
								</Grid>
							</Grid>
						</div>
					</Grid>
					<Grid item xs={12} md={12} lg={12} xl={4} className="ovCol">
						<div className="whiteCard">
							<div className="cardHead">
								<TextLg class="mb-0 lineHAuto">
									Search Visibility Score
									<span className="m-l5">
										<AppTooltip place="bottom-end" title={SScore} />
									</span>
								</TextLg>
							</div>
							<div
								className="d-flex justify-content-between align-items-center position-relative"
								style={{ height: "57px" }}
							>
								<div>
									{loading ?
										<TextLg class="fB m-b7 lh20x">
											<Tsk width={100} />
										</TextLg>
										: !hasPrevious ?
											/* Fewer than two measurements, so there is no
											   direction to report. yss is a fallback in this
											   state -- /projectoverview zeroes it where
											   /homeauth copies ss -- and either one turned a
											   single reading into a confident "Rising" or
											   "Dropping". Never-measured and measured-once are
											   different facts and say so separately. */
											<TextLg class="rankFlat fB m-b7 lh20x">
												{Number(prjtstatus.t_c) === 1 ? "Measured once" : "Not measured yet"}
											</TextLg>
											: (prjtstatus.ss - prjtstatus.yss) > 0 ?
											<TextLg class="rankUp fB m-b7 lh20x">
												<Tooltip title={"Yesterday it was " + prjtstatus.yss} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
													<div>
														Rising
														<span className={"arrow green m-l5"}>
															<FillArrow />
														</span>
													</div>
												</Tooltip>
											</TextLg>
											: (prjtstatus.ss - prjtstatus.yss) < 0 ?
												<TextLg class="rankDown fB m-b7 lh20x">
													<Tooltip title={"Yesterday it was " + prjtstatus.yss} TransitionComponent={Zoom} placement="top" classes={{ tooltip: "Tltpsmall" }}>
														<div>
															Dropping
															<span className={"arrow red m-l5"}>
																<FillArrow />
															</span>
														</div>
													</Tooltip>
												</TextLg>
												:
												<TextLg class="rankFlat fB m-b7 lh20x">No change</TextLg>
									}
									<SmallText class="fB d-flex align-items-center">
										<div className="m-r5 mb-0 txtClr d-flex align-items-center"> Best : {loading ? <Tsk className="m-l5" width={20} height={18} /> : <span className="ovNum m-l5">{prjtstatus.bss}</span>}</div>
										{/*<span className="arrow primary d-flex">
			                  <FillArrow />
			                </span>*/}
									</SmallText>
								</div>
								<div
									style={{
										position: "absolute",
										right: "-8px",
										top: "0",
									}}
								>
									{/* The arc's colour is the direction of ss - yss, so on a
									    first measured day it would read a fallback as movement.
									    Passing ss as its own previous value makes the delta
									    zero, which draws the neutral --flat arc. */}
									<Pie type="ss" serpscore={prjtstatus.ss} yserpscore={hasPrevious ? prjtstatus.yss : prjtstatus.ss} loading={loading} />
								</div>
							</div>
						</div>
					</Grid>
					<Grid item xs={12} md={12} lg={12} xl={6} className="ovCol">
						<div className="whiteCard">
							<div className="cardHead">
								<TextLg class="mb-0 lineHAuto">
									SERP Features
									<span className="m-l5">
										<AppTooltip place="bottom-end" title={Features} />
									</span>
								</TextLg>
							</div>

							<div>
								<div className="ovRow">
									<span className="ovHead">Your Ratings</span>
									<StarFullIcon color="var(--ink)" />
								</div>

								{ratingRows.map((row) => (
									<div className="ovRow" key={row.key}>
										<span className="ovLabel">
											<Rating
												name="read-only"
												value={row.stars}
												readOnly
												size="small"
												emptyIcon={<StarFullIcon color="var(--line)" />}
												icon={<StarFullIcon color="var(--ink)" />}
											/>
											<span>{row.band}</span>
										</span>
										<div className="ovNum">
											{prjtstatus[row.key] !== undefined
												? prjtstatus[row.key]
												: (loading ? <Tsk width={30} /> : null)}
										</div>
									</div>
								))}
							</div>

							{/* <div>
		              <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
		                <span className="fM">Feature Snippet</span>
		                <div>
		                  <FeatureSnptIcon color="#436DCF" />
		                </div>
		              </div>

		              <div className="d-flex justify-content-between align-items-center brdBottom m-b10 p-b10 ">
		                <span>Available</span>
		                <div className="fB">{ (prjtstatus.So || !loading) ? prjtstatus.So : <Tsk width={20} /> }</div>
		              </div>
		              <div className="d-flex justify-content-between align-items-center">
		                <span>Yours</span>
		                <div className="fB">{ (prjtstatus.Sp || !loading) ? prjtstatus.Sp : <Tsk width={20} /> }</div>
		              </div>
		            </div> */}

						</div>
					</Grid>
					<Grid item xs={12} md={12} lg={12} xl={6} className="ovCol">
						<div className="whiteCard">
							<div className="cardHead">
								<TextLg class="mb-0 lineHAuto">
									Google Search Ads
									<span className="m-l5">
										<AppTooltip place="bottom-end" title={Google} />
									</span>
								</TextLg>
							</div>

							<div className="adsTable">
								<span className="ovHead">Area</span>
								<span className="ovHead">You</span>
								<span className="ovHead">Others</span>

								{adsRows.map((row) => (
									<React.Fragment key={row.key}>
										<div className="ovLabel">{row.icon} {row.label}</div>
										<div className="ovNum">{cell(prjtstatus.Ay, row.key)}</div>
										<div className="ovNum">{cell(prjtstatus.Ao, row.key)}</div>
									</React.Fragment>
								))}
							</div>
						</div>
					</Grid>
				</Grid>
			</Grid>
		</Grid>
	);
}
