import React, { useState, useEffect } from 'react';
import { Route, Redirect, useLocation, Switch, useHistory } from 'react-router-dom';
import { getToken } from './common';
import { Sidebar, MobSidebar } from "../commonComponents/sidebar";
import { useMediaQuery } from "@mui/material";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';
import { Logout } from "../common_fun";
import { GoogleOAuthProvider } from '@react-oauth/google';
import Notfound from "../404";
import { allowsTeamAction, allowsTeamModule } from "../../utils/team_permissions";

const Dashboard = React.lazy(() => import('../dashboard'));
const AddProject = React.lazy(() => import('../addProject'));
const AddKeyword = React.lazy(() => import('../addProject/add_keyword'));
const Widget = React.lazy(() => import('../widget'));
const SerpRank = React.lazy(() => import('../serpRank'));
const KeywordOverview = React.lazy(() => import('../keywordOverview'));
const SettingsManagement = React.lazy(() => import('../projectSettings'));
const CompetitorAnalysis = React.lazy(() => import('../competitor'));
const CompetitorsComparison = React.lazy(() => import('../competitor/competitorsComparison'));

const ReportManagement = React.lazy(() => import('../reports'));

// CONTENT EDITOR
const ContentPlanner = React.lazy(() => import("../contentPlanner"))
const CEditor = React.lazy(() => import("../contentPlanner/cedit_editor"))

// GEO CITATIONS
const LLMTracker = React.lazy(() => import("../llmTracker"))
const LLMCitations = React.lazy(() => import("../citations"))

const CommonRoutes = (props) => {
	const history = useHistory();
	const [project_list, setProject_list] = useState([]);
	// const [demodata, setDemodata] = useState([]);
	const [fullbasedata, setFullbasedata] = useState({});
	const [effectupdate, setEffectupdate] = React.useState(false);

	const [fullpageloader, setFlpgloader] = useState(true);
	const cookies = new Cookies();
	const userid = cookies.get('session_userid')

	useEffect(() => {
		const cookies = new Cookies();
		const usertoken = cookies.get('session_token')
		const userid = cookies.get('session_userid')
		if (!usertoken || !userid) {
			history.push("/login");
		}

		const data = {
			'userid': userid,
		};
		axios.post(global.apiurl + '/baseauth', data, {
			headers: { 'Authorization': 'Token ' + usertoken }
		}).then(response => {
			return response.data;
		}).then(res => {
			if (res.status !== "true") {
				setFlpgloader(false);
				toast.error(res.message);
			} else {

				if (res.lg === 1) {
					toast.warning("Session timeout! Log in again")
					Logout()
					return false;
				}

				setFullbasedata(res.data)
				setProject_list(res.data.slt)
				props.setUserType(res.data.ac_typ)
				props.setTeamModules(
					res.data.ac_typ === "team" ? (res.data.team_modules || {}) : null
				)

				// if (res.data.hasOwnProperty("dmdata")){
				// 	setDemodata(res.data.dmdata)
				// }
				// console.log("base auth cookies", cookies.get('activegrp'));

				// A browser that visited a previous build still carries the 'dmo'
				// cookie described below. Drop it so the account is re-pointed at a
				// real project rather than kept broken by its own history.
				if (cookies.get('activegrp') === 'dmo') {
					cookies.remove('activegrp', { path: '/' });
				}

				if (typeof (cookies.get('activegrp')) === "undefined" || cookies.get('activegrp') === "") {
					cookies.remove('checkedListAll', { path: '/' });
					if (res.data.slt.length > 0) {
						cookies.set('activegrp', res.data.slt[0].GY, { path: '/', maxAge: global.cookiesexpire });

						// if(domainslug === "/app/dashboard") {                         
						//    	this.props.history.push('/app')                          
						// }
					}
					// With no projects there is no active group, and the cookie stays
					// unset. It used to be set to the literal string 'dmo', which every
					// caller then sent on as grpid -- and the backend parses grpid as an
					// integer, so the first call any screen made on a brand-new account
					// returned a 500 ("Field 'id' expected a number but got 'dmo'").
					// Absent is the honest value: the `if (userid && grpid)` guards those
					// callers already carry then skip the request instead of asking about
					// a project that does not exist.
					// else if(res.data.hasOwnProperty("dmdata") && res.data.dmdata.length > 0){
					//       	cookies.set('activegrp', res.data.dmdata[0].GY, { path: '/', maxAge: global.cookiesexpire });
					//   	}
				}
				setTimeout(() => {
					setFlpgloader(false);
				}, 1000);

			}
		}).catch((error) => {
			setFlpgloader(false);
			// history.push("/")
		});

		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [effectupdate]);

	const baseauthUpdate = (data) => {
		if (data === "update") {
			setEffectupdate(!effectupdate)
		}
	};

	const baseauthdataUpdate = (data) => {
		setProject_list(data)
	};


	/* docs/DESIGN.md, "Loading": a --surface-2 skeleton in the shape of the page
	   that is about to arrive -- a header row, a stat strip and a table. The
	   three bouncing dots this replaced were the only purple left in the app and
	   they appeared on every route change. */
	const pageloader = (
		<div className="layout" role="status" aria-live="polite" aria-busy="true">
			<span className="visually-hidden">Loading</span>
			<div className="pageSkeleton" aria-hidden="true">
				<div className="pageSkeleton__head">
					<div className="skeleton skeleton--title" />
					<div className="skeleton skeleton--action" />
				</div>
				<div className="pageSkeleton__stats">
					<div className="skeleton skeleton--stat" />
					<div className="skeleton skeleton--stat" />
					<div className="skeleton skeleton--stat" />
					<div className="skeleton skeleton--stat" />
				</div>
				<div className="pageSkeleton__table">
					<div className="skeleton skeleton--row skeleton--row-head" />
					<div className="skeleton skeleton--row" />
					<div className="skeleton skeleton--row" />
					<div className="skeleton skeleton--row" />
					<div className="skeleton skeleton--row" />
					<div className="skeleton skeleton--row" />
				</div>
			</div>
		</div>
	);
	const isTeam = fullbasedata.ac_typ === "team";
	const allowsModule = (module) => allowsTeamModule(fullbasedata, module);
	const allowsAction = (module, action) => (
		allowsTeamAction(fullbasedata, module, action)
	);
	const landingRoute = isTeam ? "/projects" : "/dashboard";

	return (
		<>
			{fullpageloader ?
				pageloader
				:
				<React.Suspense fallback={pageloader}>
						<Switch>
							{allowsModule("Prjcts") ? <Route path="/projects"><Dashboard fullbasedata={fullbasedata} projectList={project_list} baseauth={baseauthUpdate} /></Route> : null}
							{!isTeam ? <Route path="/addproject"><AddProject fullbasedata={fullbasedata} projectList={project_list} baseauth={baseauthUpdate} /></Route> : null}
							{allowsAction("Keyword", "Add Keywords") ? <Route path="/addkeyword"><AddKeyword fullbasedata={fullbasedata} projectList={project_list} baseauth={baseauthUpdate} baseauthdataUpdate={baseauthdataUpdate} /></Route> : null}
							{allowsModule("Widgets") ? <Route path="/dashboard" ><Widget fullbasedata={fullbasedata} projectList={project_list} baseauth={baseauthUpdate} /></Route> : null}
							{allowsModule("Keyword") ? <Route exact path="/keywords"><SerpRank fullbasedata={fullbasedata} projectList={project_list} baseauth={baseauthUpdate} baseauthdataUpdate={baseauthdataUpdate} /></Route> : null}
							{allowsModule("Keyword") ? <Route exact path="/keywords/:kwid/:kwname"><KeywordOverview fullbasedata={fullbasedata} /></Route> : null}
							{allowsModule("Reports") ? <Route exact path="/reports"><ReportManagement fullbasedata={fullbasedata} projectList={project_list} baseauth={baseauthUpdate} baseauthdataUpdate={baseauthdataUpdate} /></Route> : null}
							{/* Settings is one page now. These are the addresses the old
							    avatar-menu entries used, kept so existing links and
							    bookmarks land on the matching tab instead of 404ing. */}
							{!isTeam ? <Redirect exact from="/account" to="/settings/account" /> : null}
							{!isTeam ? <Redirect exact from="/account/settings" to="/settings/profile" /> : null}
							{!isTeam ? <Redirect exact from="/account/apikey" to="/settings/apikey" /> : null}
							{!isTeam ? <Redirect exact from="/account/aikeys" to="/settings/aikeys" /> : null}
							{!isTeam ? <Redirect exact from="/user" to="/settings/members" /> : null}
							{allowsModule("Settings") ? <Route exact path="/settings"><SettingsManagement fullbasedata={fullbasedata} projectList={project_list} /></Route> : null}
							{allowsModule("Settings") ? <Route exact path="/settings/:settingSlug"><SettingsManagement fullbasedata={fullbasedata} projectList={project_list} /></Route> : null}
							{allowsModule("Settings") ? <Route exact path="/settings/:settingSlug/:groupId"><SettingsManagement fullbasedata={fullbasedata} projectList={project_list} /></Route> : null}
							{allowsModule("CompAi") ? <Route exact path="/competitors"><CompetitorAnalysis fullbasedata={fullbasedata} projectList={project_list} baseauth={baseauthUpdate} baseauthdataUpdate={baseauthdataUpdate} /></Route> : null}
							{allowsModule("CompAi") ? <Route exact path="/competitors/keywords"><CompetitorsComparison fullbasedata={fullbasedata} projectList={project_list} baseauth={baseauthUpdate} baseauthdataUpdate={baseauthdataUpdate} /></Route> : null}
									{/* CONTENT EDITOR */}
									{allowsModule("ContentPlanner") ? <Route exact path="/contentplanner"><ContentPlanner projectList={project_list} fullbasedata={fullbasedata} baseauth={baseauthUpdate} /></Route> : null}
									{allowsModule("ContentPlanner") ? <Route exact path="/contentplanner/editor/:content_id"><CEditor projectList={project_list} fullbasedata={fullbasedata} baseauth={baseauthUpdate} /></Route> : null}
									{/* CONTENT EDITOR */}

									{/* GEO CITATIONS */}
									{allowsModule("LLMTracker") ? <Route exact path="/llmtracker"><LLMTracker projectList={project_list} fullbasedata={fullbasedata} baseauth={baseauthUpdate} /></Route> : null}
									{allowsModule("LLMTracker") ? <Route exact path="/prompt/citations/:id"><LLMCitations projectList={project_list} fullbasedata={fullbasedata} baseauth={baseauthUpdate} /></Route> : null}
									{/* GEO CITATIONS */}

							{/*<Route exact path="/keyword/:kwid/:kwname"><KeywordOverview /></Route>*/}
							<Redirect exact from="/app" to={landingRoute} />
							<Redirect from="*" to={landingRoute} />
						</Switch>
				</React.Suspense>
			}
		</>
	)
}

// handle the private routes
const PrivateRoute = (props) => {
	const location = useLocation();
	const smallView = useMediaQuery("(max-width:575.98px)");
	const smallAboveView = useMediaQuery("(min-width:576px)");
	const [username, setUsername] = useState('');
	const [useremail, setUseremail] = useState('');
	const [userType, setUserType] = useState()
	const [teamModules, setTeamModules] = useState(null)

	useEffect(() => {
		const cookies = new Cookies();
		setUsername(cookies.get('session_username'))
		setUseremail(cookies.get('session_usermail'))
	}, []);

	const routesPathList = () => {
		const routeList = [
			'projects',
			'addproject',
			'addkeyword',
			'dashboard',
			// 'serprank',
			'keywords',
			'reports',
			'account',
			'settings',
			'app',
			'competitors',
			'user',
			'contentplanner',
			'llmtracker',
			'prompt'

		]
		return routeList.includes(location.pathname.split('/')[1]) ? true : false;
	};

	return (
		<>
			{getToken() ?
				<>
					{(routesPathList() && smallAboveView) ?
						<Sidebar userType={userType} teamModules={teamModules} uname={username} uemail={useremail} >
							<CommonRoutes userType={userType} setUserType={setUserType} setTeamModules={setTeamModules} />
						</Sidebar>
						: (routesPathList() && smallView) ?
							<MobSidebar userType={userType} teamModules={teamModules} uname={username} uemail={useremail} >
								<CommonRoutes userType={userType} setUserType={setUserType} setTeamModules={setTeamModules} />
							</MobSidebar>
							:
							<Notfound />
					}
				</>
				:
				<Redirect to={{ pathname: '/login' }} />
			}
		</>
	)
}

export default PrivateRoute;
