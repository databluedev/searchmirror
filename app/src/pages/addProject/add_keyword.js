import React, { useState, useEffect } from "react";
import { Link, useHistory, useLocation } from "react-router-dom";
import Header from "../commonComponents/header";
import { TagsInput, KeywordInput } from "../commonComponents/manage_tag";
import { CloseIcon, DesktopIcon, MobileIcon } from "../commonComponents/icons";
import { Grid, InputLabel, Autocomplete, TextField, Chip } from "@mui/material";
import CountryFlag from "../commonComponents/country_flag";
import "./style.scss";
import { AppButton, SmallText, Input, SelectLang, KNRSelectRegion, Para, AppTooltip } from "../commonComponents/parts";
import { Switch } from "@mui/material";
import { styled } from "@mui/material/styles";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { toast } from 'react-toastify';
// import {fstLtrCapitalfun} from "../common_fun";   
import { CsvUpload } from "./components/csv_upload";
import { ModalBox, ConfirmModal, ConfirmDialog } from "../commonComponents/Modals";
import { revealFormError } from "../commonComponents/form_feedback";
import { findSearchRegion, normalizeSearchDefaults } from "../common_fun";
import { SerpDepthChoice, DEPTH_ADVANCED, ADVANCED_CONFIRM_BODY, PRECEDENCE_NOTE, readSerpDepth, writeSerpDepth } from "../projectSettings/components/serp_depth";


const AntSwitch = styled(Switch)(({ theme }) => ({
  width: 28,
  height: 16,
  padding: 0,
  display: "flex",
  "&:active": {
    "& .MuiSwitch-thumb": {
      width: 15,
    },
    "& .MuiSwitch-switchBase.Mui-checked": {
      transform: "translateX(9px)",
    },
  },
  "& .MuiSwitch-switchBase": {
    padding: 2,
    "&.Mui-checked": {
      transform: "translateX(12px)",
      color: "var(--surface)",
      "& + .MuiSwitch-track": {
        opacity: 1,
        backgroundColor: "var(--accent)",
      },
    },
  },
  "& .MuiSwitch-thumb": {
    boxShadow: "0 2px 4px 0 rgb(0 35 11 / 20%)",
    width: 12,
    height: 12,
    borderRadius: 6,
    transition: theme.transitions.create(["width"], {
      duration: 200,
    }),
  },
  "& .MuiSwitch-track": {
    borderRadius: 16 / 2,
    opacity: 1,
    backgroundColor:
      theme.palette.mode === "dark"
        ? "rgba(255,255,255,.35)"
        : "rgba(0,0,0,.25)",
    boxSizing: "border-box",
  },
}));

function AddKeyword(props) {

  const history = useHistory();
  const location = useLocation();
  // One ref per validated field. A blocked submit scrolls the offending
  // field into view and focuses it, so the failure cannot happen off-screen.
  const wsurlRef = React.useRef(null);
  const regionRef = React.useRef(null);
  const langRef = React.useRef(null);
  const keywordRef = React.useRef(null);

  const [domainname, setDomainname] = useState('');
  const [wsurl, setWsurl] = useState('');
  const [wsurlerrmsg, setWsurlerrmsg] = useState('');
  const [lang, setLang] = useState("");
  const [langerrmsg, setLangerrmsg] = useState('');
  // Region and keywords used to block submit with no message at all, or with a
  // toast that vanished before the user looked back at the form.
  const [rgnerrmsg, setRgnerrmsg] = useState('');
  const [kwerrmsg, setKwerrmsg] = useState('');
  const [btnloading, setBtnloading] = useState(false);
  const [langoptions, setLangoptions] = useState([]);
  const [remainkeyaddcount, setRemainkeyaddcount] = useState(0);
  // Same sentinel as addProject/index.js:101. Under BYOK the keyword
  // allowance defaults to serp.models.UNMETERED (1e9) and this value is
  // allowance-minus-used, so it arrives as ~999,999,99x -- just under the
  // sentinel, never equal to it. A real plan cap is in the tens or
  // hundreds; anything past a million is the unmetered value, not a limit
  // worth printing (this page was offering "999999962 keywords").
  const kwUnlimited = remainkeyaddcount > 1000000;
  const [platform, setPlatform] = useState("desktop");
  // Keyword.exactdomain. It is read by the engine's matcher
  // (parser_json.py: exact_url_scheme vs extract_domain) and has always been
  // hardcoded false here, so a live matching rule had no control at all.
  const [exactdomain, setExactdomain] = useState(false);

  // Depth is a property of the PROJECT (Groups.serp_advanced) -- there is no
  // per-keyword column, so the form says so rather than implying one. Written
  // only on submit, so abandoning the form changes nothing. depthSaved is the
  // server's value, depthValue the form's; both start null so nothing renders
  // a selection before the read lands.
  const isTeam = props.fullbasedata && props.fullbasedata.ac_typ === "team";
  const [depthSaved, setDepthSaved] = useState(null);
  const [depthValue, setDepthValue] = useState(null);
  const [depthError, setDepthError] = useState("");
  const [depthConfirm, setDepthConfirm] = useState(false);

  const [tagopt, setTagopt] = useState(true);
  const [othertg, setOthertg] = useState([]);
  const [othertags, setOthertags] = useState([]);
  const [selectedtags, setSelectedtags] = useState([]);
  const [keywordlist, setKeywordlist] = useState([]);
  const [onCallLoad, setOnCallLoad] = useState(true);

  const [rgoptions, setRgoptions] = useState([]);
  const [fltrregion, setfltrRegion] = useState([]);
  const [region, setRegion] = useState("");
  const [isocode, setIsocode] = useState("");
  const [countryname, setCountryname] = useState("");

  // One keyword tracked in several countries becomes one row per country, so
  // every extra country multiplies both the keyword count and the daily bill.
  // It is therefore opt-in: the form is a single-country form until the user
  // opens this, and the primary region above stays the default.
  const [extraRegions, setExtraRegions] = useState([]);
  const [multiOpen, setMultiOpen] = useState(false);
  // Pages per check, from /kwaddcost. null means it was not read -- the cost
  // line then says so rather than printing a 1 that would understate the bill.
  const [pagesPerCheck, setPagesPerCheck] = useState(null);

  const countryCount = 1 + extraRegions.length;
  // The plan allowance counts ROWS, and this add writes one row per country.
  const keywordLimit = countryCount > 1 ? Math.floor(remainkeyaddcount / countryCount) : remainkeyaddcount;
  const rowsToAdd = keywordlist.length * countryCount;
  // Per keyword until there is a list to total. An empty list is "not entered
  // yet", and "0 searches a day" is a bill, not a blank.
  const searchesPerKeyword = pagesPerCheck === null ? null : countryCount * pagesPerCheck;
  const searchesPerDay = pagesPerCheck === null ? null : rowsToAdd * pagesPerCheck;


  useEffect(() => {
    global.PageTopLoader.current.continuousStart();
    const cookies = new Cookies();
    const usertoken = cookies.get('session_token')
    const userid = cookies.get('session_userid')
    const grpid = cookies.get('activegrp');

    const data = {
      'userid': userid,
      // With no project the activegrp cookie is unset, and axios drops an
      // undefined value from the JSON body entirely. 0 is the explicit "no
      // project" value addProject/index.js:152 already sends, so the two
      // sibling pages state the same thing the same way rather than one
      // omitting the field and the other zeroing it. (/getsetting tolerates
      // both -- an absent key used to 500 and no longer does.)
      'grpid': grpid || 0
    };
    axios.post(global.apiurl + '/getsetting', data, {
      headers: { 'Authorization': 'Token ' + usertoken }
    }).then(response => {
      return response.data;
    }).then(res => {
      if (res.status !== "true") {
        const msg = res.message;
        toast.error(msg)
      } else {
        if (res.g_l === 0 || res.k_l === 0) {
          history.push('/projects');
        }

        if (res.u_kw >= res.pKL) {
          history.push("/keywords");
        }

        setLangoptions(res.lnge)
        setRgoptions(res.rg)
        setfltrRegion(res.rg)
        setRemainkeyaddcount(res.pKL - res.u_kw)
        setDomainname(res.dN)

        const defaults = normalizeSearchDefaults(
          res.rg,
          res.lnge,
          res.DR,
          location.customData ? location.customData.regionCode : "",
        );
        setIsocode(defaults.isocode)
        setRegion(defaults.region)
        setCountryname(defaults.countryname)
        setLang(defaults.language)

        if (location.customData) {
          setKeywordlist([location.customData.keyword])
        }

        setOthertags(res.o_tg)
        setOthertg(res.o_tg)
      }
    }).catch((error) => {

    });

    // Pages per check. Failure is silent on purpose: pagesPerCheck stays null
    // and the cost line drops the multiplier instead of inventing one.
    axios.post(global.apiurl + '/kwaddcost', { 'userid': userid }, {
      headers: { 'Authorization': 'Token ' + usertoken }
    }).then(response => {
      if (response.data && response.data.status === "true") {
        const pages = parseInt(response.data.pages, 10);
        if (pages > 0) {
          setPagesPerCheck(pages);
        }
      }
    }).catch(() => { });

    // /prjctserpmode is missing from backend/account/team_permissions.py, so a
    // member's token is refused on the read too. Members get a sentence, not a 403.
    const depthAbort = new AbortController();
    if (grpid && !isTeam) {
      readSerpDepth(grpid, depthAbort.signal).then((adv) => {
        setDepthSaved(adv);
        setDepthValue(adv);
      }).catch((error) => {
        if (axios.isCancel(error)) {
          return;
        }
        setDepthError("Could not read this project's extraction depth.");
      });
    }

    setTimeout(() => {
      global.PageTopLoader.current.complete();
    }, 1000);

    return () => depthAbort.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const addKeyword = (event) => {
    const cookies = new Cookies();
    const userid = cookies.get('session_userid');

    var pattern = new RegExp('^((ft|htt)ps?:\\/\\/)?' + // protocol
      '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|' + // domain name and extension
      '((\\d{1,3}\\.){3}\\d{1,3}))' + // OR ip (v4) address
      '(\\:\\d+)?' + // port
      '(\\/[-a-z\\d%@_.~+&:]*)*' + // path
      '(\\?[;&a-z\\d%@_.,~+&:=-]*)?' + // query string
      '(\\#[-a-z\\d_]*)?$', 'i'); // fragment locator

    if (wsurl.charAt(0) === "/") {
      var extraurl = wsurl.slice(1, wsurl.length)
    } else {
      var extraurl = wsurl
    }

    if (domainname.endsWith("/")) {
      var url = domainname + extraurl;
    } else {
      var url = domainname + "/" + extraurl;
    }

    if (userid) {
      if (!url.trim()) {
        setWsurlerrmsg("Enter URL");
        revealFormError("Enter URL", wsurlRef);
        return false
      } else if (!pattern.test(url)) {
        setWsurlerrmsg("Enter a valid URL");
        revealFormError("Enter a valid URL", wsurlRef);
        return false
      } else if (region.length === 0) {
        setRgnerrmsg("Select your region");
        revealFormError("Select your region", regionRef);
        return false
      } else if (lang.length === 0) {
        setLangerrmsg("Select your language")
        revealFormError("Select your language", langRef);
        return false
      } else if (exactdomain && !extraurl.trim()) {
        // Without a path the target is the domain root, so "only this page"
        // would silently mean "only the home page".
        setWsurlerrmsg("Enter the page that must rank, or switch back to matching any page");
        revealFormError("Enter the page that must rank", wsurlRef);
        return false
      } else if (keywordlist.length === 0) {
        setKwerrmsg("Add at least one keyword to track")
        revealFormError("Add at least one keyword to track", keywordRef);
        return false
      } else {
        addfreshkeyfn(extraurl, keywordlist, exactdomain);
      }
    }
  }

  const addfreshkeyfn = (wsurl, keywordlist, exactdomain) => {
    const cookies = new Cookies();
    const userid = cookies.get('session_userid');
    const usertoken = cookies.get('session_token')
    const grpid = cookies.get('activegrp');

    setBtnloading(true)

    if (wsurl.charAt(0) === "/") {
      var extraurl = wsurl.slice(1, wsurl.length)
    } else {
      extraurl = wsurl
    }

    if (domainname.endsWith("/")) {
      var url = domainname + extraurl;
    } else {
      var url = domainname + "/" + extraurl;
    }

    const data = {
      'userid': userid,
      'grpid': grpid,
      'url': url,
      'keyword': keywordlist,
      'platform': platform,
      'region': region,
      'countryname': countryname,
      'isocode': isocode,
      // Every country this add writes a row for, primary first. The backend
      // reads the isocode and country name off the Region row for each one, so
      // the three can never disagree.
      'regions': [region].concat(extraRegions.map((rg) => rg.RN)),
      'language': lang,
      'exactdomain': exactdomain,
    };

    if (tagopt === true && selectedtags.length > 0) {
      data['tags'] = selectedtags;
    }

    if (onCallLoad === true) {
      setOnCallLoad(false)

      // Depth first: /addkeyv3 queues a run for the whole project as soon as it
      // returns, so a later write would miss the run this submit starts. Only
      // fired when the value changed, and a failure does not cancel the add.
      const depthChanged = depthSaved !== null && depthValue !== null && depthValue !== depthSaved;
      const depthStep = depthChanged
        ? writeSerpDepth(grpid, depthValue).then((adv) => {
          setDepthSaved(adv);
          setDepthValue(adv);
        }).catch(() => {
          toast.warning("Extraction depth was not changed. The keywords are still being added at the project's current depth.")
          setDepthValue(depthSaved);
        })
        : Promise.resolve();

      depthStep.then(() => axios.post(global.apiurl + '/addkeyv3', data, {
        headers: { 'Authorization': 'Token ' + usertoken }
      })).then(response => {
        return response.data;
      }).then(resp => {
        if (resp.status === 'true') {
          if (resp.message === 'warning') {
            toast.warning(resp.errormsg)
          }
          setTimeout(() => {
            if (resp.Engmd === 0) {
              toast.error("Manual refresh is currently disabled. You'll have it back soon.")
            }

            var data = props.projectList.map((item, i) => item.GY === parseInt(grpid) ? { ...item, 'kw_c': item.kw_c + resp.kwcnt } : item)
            props.baseauthdataUpdate(data)
            history.push('/keywords');

          }, 1500);
        } else {
          setBtnloading(false)

          if (resp.message === 'warning') {
            toast.warning(resp.errormsg)
          } else {
            toast.error(resp.message)
          }
        }
        setOnCallLoad(true)
      }).catch(err => {
        setOnCallLoad(true)
        setBtnloading(false)
      });
    }
  }


  const selectlstChange = (event) => {
    const { target: { value }, } = event;

    setLangerrmsg('');
    setLang(value);
  };

  // Moving up in cost asks first; moving down does not.
  const handleDepthChange = (next) => {
    if (next === depthValue) {
      return;
    }
    if (next === DEPTH_ADVANCED) {
      setDepthConfirm(true);
      return;
    }
    setDepthValue(next);
  };

  const keywordDelete = (i) => {
    setKeywordlist([...keywordlist.filter((tag, index) => index !== i)]);
  };

  const rgselectlstChange = (event) => {
    const { target: { value }, } = event;
    const selected = findSearchRegion(rgoptions, value);
    setRegion(selected ? selected.RN : "");
    setCountryname(selected ? selected.Rcnt : "");
    setIsocode(selected ? selected.Rcd : "");
    // Promoting a country to primary must not leave it in the extras too --
    // that would be a second row for the same search.
    if (selected) {
      setExtraRegions((current) => current.filter((rg) => rg.RN !== selected.RN));
    }
    setRgnerrmsg("");
  }

  const regionListdataUpdate = (data) => {
    setfltrRegion(data);
  }

  const menuOpen = () => {
    setfltrRegion(rgoptions);
  }

  const Improved = (
    <div>
      <Para class="m-0">
        Add relevent tags to your keywords .
      </Para>
    </div>
  );

  return (
    <>
      {/* "light": the dark ground renders the confirm button black on near-black. */}
      <ModalBox className="light" title="" open={depthConfirm} onClose={() => setDepthConfirm(false)}>
        <ConfirmDialog
          title="Switch this project to Advanced?"
          cancelTitle="Cancel"
          confirmTitle="Switch to Advanced"
          modalCancel={() => setDepthConfirm(false)}
          modalConfirm={() => { setDepthConfirm(false); setDepthValue(DEPTH_ADVANCED); }}
          content={ADVANCED_CONFIRM_BODY + " The change is saved when you add these keywords."}
        />
      </ModalBox>

      <section className="layout addProject">
        <div>
          <Header
            rightside="d-none"
            title="Add Keyword"
            subTitle="Enter the required details in all the specified fields below"
            class=""
            backlink={location.customData ? location.customData.backlink : "/keywords"}
          />

          <div>
            <div className="m-b70">
              <Grid container spacing={3} className="">
                <Grid item xs={12} md={5} lg={3}>
                  <div className="m-b20">
                    <InputLabel shrink>
                      Project domain <span className="redClr">*</span>
                    </InputLabel>
                    <Input placeholder="https://www.tracker.example" value={domainname} disabled={true} variant="" />
                  </div>
                  {/* Was "URL slug", which named the input's format rather
                      than its job. It builds Keyword.site_url -- the page you
                      expect to rank -- and is what the keywords table shows
                      under each keyword. */}
                  <div className="m-b20" ref={wsurlRef}>
                    <InputLabel shrink>
                      Target page
                    </InputLabel>
                    <Input placeholder="blog/rank-higher-on-google/" value={wsurl} onchange={(e) => { setWsurl(e.target.value); setWsurlerrmsg("") }} errmsg={wsurlerrmsg} error={wsurlerrmsg.length > 0} />
                    <SmallText class="secondaryClr d-block m-t5">
                      The page on {domainname || "your domain"} you expect to rank for these
                      keywords. Leave it empty to track the site itself.
                    </SmallText>
                  </div>

                  {/* exactdomain. The label is the consequence, not the flag
                      name -- "exact domain" describes neither option. */}
                  <div className="m-b20">
                    <InputLabel shrink>
                      Rank counts when
                    </InputLabel>
                    <div className="depthChoice" role="radiogroup" aria-label="What counts as your result">
                      {[
                        {
                          value: false,
                          name: "Any page on the domain ranks",
                          desc: "Whichever of your pages Google shows is recorded as your position.",
                        },
                        {
                          value: true,
                          name: "Only the target page ranks",
                          desc: "A different page of yours in the results is recorded as not ranking.",
                        },
                      ].map((opt) => (
                        <label className={"depthOption" + (exactdomain === opt.value ? " isOn" : "")} key={opt.name}>
                          <input
                            type="radio"
                            name="exactdomain"
                            checked={exactdomain === opt.value}
                            onChange={() => { setExactdomain(opt.value); setWsurlerrmsg("") }}
                          />
                          <span className="depthOptionMark" aria-hidden="true" />
                          <span className="depthOptionBody">
                            <span className="depthOptionName">{opt.name}</span>
                            <span className="depthOptionDesc">{opt.desc}</span>
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>
                  <div className=" m-b20" ref={regionRef}>
                    <InputLabel shrink>
                      Region <span className="redClr">*</span>
                    </InputLabel>
                    <KNRSelectRegion rgName="aprgrndrName text-truncate" className="rgaddKwd" placeholder={"Region"} menuOpen={menuOpen} fullList={rgoptions} menulist={fltrregion} value={region !== "" ? "" + isocode + " " + region + " (" + countryname + ")" : countryname} onchange={rgselectlstChange} regionUpdate={regionListdataUpdate} rgcode={isocode} rgname={region} rgcnt={countryname} errmsg={rgnerrmsg} error={rgnerrmsg.length > 0 && region.length === 0} />

                    {/* Opt-in second country onwards. Closed, this is one line
                        of text and the form behaves exactly as it did. */}
                    {multiOpen || extraRegions.length > 0 ? (
                      <div className="moreCountries">
                        <InputLabel shrink>
                          Also track in
                        </InputLabel>
                        <Autocomplete
                          multiple
                          disableCloseOnSelect
                          className="countryPicker"
                          options={rgoptions.filter((rg) => rg.RN !== region)}
                          value={extraRegions}
                          onChange={(e, next) => setExtraRegions(next)}
                          getOptionLabel={(rg) => rg.Rcnt}
                          isOptionEqualToValue={(rg, picked) => rg.RN === picked.RN}
                          renderOption={(optionProps, rg) => (
                            <li {...optionProps} key={rg.RN}>
                              <CountryFlag width="24" height="16" code={rg.Rcd} alt="" className="m-r10" style={{ borderRadius: "3px" }} />
                              <span>{rg.Rcnt}</span>
                              <span className="countryDomain">{rg.RN}</span>
                            </li>
                          )}
                          renderTags={(picked, getTagProps) =>
                            picked.map((rg, i) => (
                              <Chip
                                {...getTagProps({ index: i })}
                                key={rg.RN}
                                label={rg.Rcnt}
                                icon={<CountryFlag width="18" height="12" code={rg.Rcd} alt="" style={{ borderRadius: "2px" }} />}
                              />
                            ))
                          }
                          renderInput={(params) => (
                            <TextField {...params} placeholder={extraRegions.length > 0 ? "" : "Search countries"} />
                          )}
                        />
                        <SmallText class="secondaryClr d-block m-t5">
                          Each keyword is tracked separately in every country, so each one is
                          its own row and its own daily search.
                        </SmallText>
                      </div>
                    ) : (
                      <button type="button" className="moreCountriesOpen" onClick={() => setMultiOpen(true)}>
                        + Track these keywords in more countries
                      </button>
                    )}
                  </div>
                  <div className=" m-b20" ref={langRef}>
                    <InputLabel shrink>
                      Language <span className="redClr">*</span>
                    </InputLabel>

                    <SelectLang placeholder={"Select the language"} value={lang} menulist={langoptions} onchange={selectlstChange} errmsg={langerrmsg} error={langerrmsg.length > 0} />

                  </div>
                  <div className="platformSelect">
                    <InputLabel shrink>
                      Platform <span className="redClr">*</span>
                    </InputLabel>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "85px 85px",
                        gap: "15px",
                      }}
                    >
                      <label className="labl">
                        <input type="radio" name="radioname" value="desktop" onClick={(e) => { setPlatform(e.target.value) }} defaultChecked />

                        <div>
                          <div className="icon">
                            <DesktopIcon />
                          </div>
                          Desktop
                        </div>
                      </label>
                      <label className="labl">
                        <input type="radio" name="radioname" value="mobile" onClick={(e) => { setPlatform(e.target.value) }} />

                        <div>
                          <div className="icon">
                            <MobileIcon />
                          </div>
                          Mobile
                        </div>
                      </label>
                    </div>
                  </div>

                  {/* Platform is per keyword, depth is per project -- the note
                      says which, so the pairing does not imply otherwise. */}
                  <div className="depthSelect">
                    <InputLabel shrink>
                      SERP extraction depth
                    </InputLabel>
                    {depthError ? (
                      <Para class="secondaryClr m-b0">
                        {depthError} You can still add keywords; set the depth on the{" "}
                        <Link className="depthLink" to="/settings/apikey">DataBlue API Key tab</Link>.
                      </Para>
                    ) : isTeam ? (
                      <Para class="secondaryClr m-b0">
                        Extraction depth is set by the account owner and applies to every keyword
                        in this project.
                      </Para>
                    ) : depthValue === null ? (
                      /* Reading. Two unselected radios would read as "neither",
                         which is not what is true. */
                      <Para class="secondaryClr m-b0">Reading this project's extraction depth…</Para>
                    ) : (
                      <SerpDepthChoice
                        value={depthValue}
                        onChange={handleDepthChange}
                        name="serpdepth-addkeyword"
                        note={
                          <>
                            The default for <span className="depthScopeStrong">every keyword in
                            this project</span>, not only the ones added here
                            {depthSaved !== null && depthValue !== depthSaved
                              ? ", and the change is saved when you add these keywords"
                              : ""}
                            . {PRECEDENCE_NOTE} Open a keyword after adding it to give that one
                            its own depth or its own pages per check. Pages for the whole account
                            is on the{" "}
                            <Link className="depthLink" to="/settings/apikey">DataBlue API Key tab</Link>.
                          </>
                        }
                      />
                    )}
                  </div>
                </Grid>
                <Grid item xs={12} md={8} lg={5}>
                  <div className="keyword" ref={keywordRef}>
                    <div className="parent">
                      <div>
                        <h2 className="smallTitle m-b5">
                          Keywords <span className="redClr">*</span>
                        </h2>
                        <SmallText class="mb-0">
                          {kwUnlimited
                            ? "Add as many keywords as you like"
                            : countryCount > 1
                              ? `You can add up to ${keywordLimit} keywords across ${countryCount} countries`
                              : `You can add up to ${keywordLimit} keywords`}
                        </SmallText>
                      </div>

                      <CsvUpload keywordlist={keywordlist} kwupdatefun={(kw) => setKeywordlist(kw)} limit={keywordLimit} />
                    </div>


                    <div className={"box" + (kwerrmsg && keywordlist.length === 0 ? " boxError" : "")}>
                      <div
                        style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}
                      >
                        <div className="w-100">
                          <KeywordInput selectedtags={keywordlist} tagupdatefun={(tag) => setKeywordlist(tag)} limit={keywordLimit} invalid={kwerrmsg.length > 0 && keywordlist.length === 0} errorid="addkeyword-keywords-error" />
                        </div>
                        {keywordlist.map((tag, index) => (
                          <div className="tag new" key={index}>
                            {tag}
                            <span className="close" onClick={() => keywordDelete(index)}>
                              <CloseIcon color="var(--surface)" />
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Clears itself as soon as a keyword exists. */}
                    {kwerrmsg && keywordlist.length === 0 ?
                      <div className="fieldError m-b5" id="addkeyword-keywords-error">{kwerrmsg}</div>
                      : null}

                    {kwUnlimited ? null : (
                    <SmallText class="d-flex justify-content-end">
                      Remaining:{" "}
                      <span className="txtClr m-l5">{keywordLimit - keywordlist.length} keywords</span>
                    </SmallText>
                    )}
                  </div>
                </Grid>
                <Grid item xs={12} md={5} lg={4}>
                  <div className="addtag">
                    <div className="d-flex align-items-center justify-content-between p-b5">
                      <div>
                        <h2 className="smallTitle m-b5">Add Tags
                          <span className="m-l5">
                            <AppTooltip place="bottom-start" title={Improved} />
                          </span>
                        </h2>
                        <SmallText class="mb-0">Enter multiple tags separated by comma</SmallText>
                      </div>
                      <div>
                        <AntSwitch
                          checked={tagopt}
                          onChange={(e) => { setTagopt(e.target.checked) }}
                          inputProps={{ "aria-label": "ant design" }}
                        />
                      </div>
                    </div>
                    {tagopt ? <TagsInput selectedtags={selectedtags} tagupdatefun={(tag) => setSelectedtags(tag)} othertg={othertg} othertagupdatefun={(tag) => setOthertg(tag)} othertags={othertags} /> : null}
                  </div>
                </Grid>
              </Grid>
            </div>
            {/* Sits immediately above the submit button because it is the one
                thing that must be read before it: every country multiplies the
                daily spend on the account's own DataBlue key, and the multiplier
                is invisible in the fields above. */}
            <div className="addCost">
              <div className="addCostHead">
                What this will cost
              </div>
              <div className="addCostLine">
                {keywordlist.length > 0 ? (
                  <>
                    <span className="addCostFigure">{keywordlist.length} {keywordlist.length === 1 ? "keyword" : "keywords"}</span>
                    {" × "}
                    <span className="addCostFigure">{countryCount} {countryCount === 1 ? "country" : "countries"}</span>
                    {" = "}
                    <span className="addCostFigure">{rowsToAdd} tracked {rowsToAdd === 1 ? "keyword" : "keywords"}</span>
                    {" added to this project."}
                  </>
                ) : (
                  <>
                    {"Every keyword you add is tracked in "}
                    <span className="addCostFigure">{countryCount} {countryCount === 1 ? "country" : "countries"}</span>
                    {", so each one becomes " + countryCount + " tracked " + (countryCount === 1 ? "keyword" : "keywords") + "."}
                  </>
                )}
              </div>
              <div className="addCostLine">
                {pagesPerCheck === null ? (
                  /* Pages could not be read. Printing 1 here would state a bill
                     that is wrong for every account tracking more pages. */
                  <>
                    {"Each of those is one DataBlue search per result page you track, every day, on your own key. Your pages-per-check setting is on the "}
                    <Link className="depthLink" to="/settings/apikey">DataBlue API Key tab</Link>.
                  </>
                ) : keywordlist.length > 0 ? (
                  <>
                    {"That is "}
                    <span className="addCostFigure">{searchesPerDay} DataBlue {searchesPerDay === 1 ? "search" : "searches"} every day</span>
                    {" — " + rowsToAdd + " × " + pagesPerCheck + " " + (pagesPerCheck === 1 ? "result page" : "result pages") + " per check — billed to your own key, on every scheduled run."}
                  </>
                ) : (
                  <>
                    {"Each keyword you add costs "}
                    <span className="addCostFigure">{searchesPerKeyword} DataBlue {searchesPerKeyword === 1 ? "search" : "searches"} every day</span>
                    {" — " + countryCount + " × " + pagesPerCheck + " " + (pagesPerCheck === 1 ? "result page" : "result pages") + " per check — billed to your own key, on every scheduled run."}
                  </>
                )}
              </div>
              {depthValue === DEPTH_ADVANCED ? (
                <div className="addCostLine">
                  Advanced is on for this project, so each of those searches is billed at the
                  higher Advanced rate.
                </div>
              ) : null}
              {countryCount > 1 ? (
                <div className="addCostLine addCostWarn">
                  {countryCount} countries multiplies this project's daily spend by {countryCount}
                  {" compared with tracking one country."}
                </div>
              ) : null}
            </div>

            <div className="footer">
              <div>
                <Link to={"/keywords"}>
                  <AppButton value="Cancel" color="white" class="borderBtn" noIcon="d-none"></AppButton>
                </Link>
              </div>
              <div>
                <AppButton noIcon="d-none" value="Add Keyword" color="primary" type="submit" onclick={addKeyword} loading={btnloading} disabled={btnloading} />
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

export default AddKeyword;
