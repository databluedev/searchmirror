import { Grid, Switch } from "@mui/material";
import React from "react";
import { AppButton, ParaLg } from "../../commonComponents/parts";
import styled from "@emotion/styled";
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
    "& .Mui-checked .MuiSwitch-input": {
        left: '-42px !important',
    },
    "& .MuiSwitch-input": {
        left: '-2px !important',
        width: "64px !important",
        height: "30px",
        top: "auto",
        borderRadius: "50px !important"
    },
    "& .MuiSwitch-switchBase": {
        padding: 2,
        "&.Mui-checked": {
            transform: "translateX(12px)",
            color: "var(--surface)",
            "& + .MuiSwitch-track": {
                opacity: 1,
                backgroundColor: theme.palette.mode === "dark" ? "#177ddc" : "#1890ff",
            },
        },
    },
    "& .MuiSwitch-thumb": {
        boxShadow: "0 2px 4px 0 rgb(0 35 11 / 20%)",
        width: "12px !important",
        height: "12px !important",
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

        "&:after, &:before": {
            color: "white",
            fontSize: "10px",
            position: "absolute",
            top: "7px",
        },
        "&:after": {
            content: "'Hide'",
            left: "10px",
        },
        "&:before": {
            content: "'Show'",
            right: "15px",
        },
    },
}));

function AccessManagement() {
    return (
        <>
            <div className="drp-form">
                <Grid container spacing={2}>
                    <Grid item xs={12} md={12} lg={4}>
                        <Grid container spacing={2}>
                            <Grid padding={'0px'} item xs={12} md={12} lg={12}>
                                <Grid container spacing={2}>
                                    <Grid item xs={12} lg={12}>
                                        <div className="border bdr-5x bg-white">
                                            <div className="d-flex align-items-center justify-content-between p-t15 p-b5 px-3">
                                                {/* <Text class="m-0">All Project</Text> */}
                                                <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                                    All Projects
                                                </ParaLg>
                                                <AntSwitch
                                                    className="textSwitch"
                                                    checked={true}
                                                    // checked={overviewswt}
                                                    // onChange={overviewSwtFun}
                                                    inputProps={{ "aria-label": "ant design" }}
                                                />
                                            </div>
                                            <div className="p-b15 p-t5 d-grid gap-3 px-3">
                                                <div className="customRadio">
                                                    <label className="d-flex labl">
                                                        <input type="checkbox" name="radioname" value={"clicks"}
                                                        // checked={handleGeneralChecked("clicks")}
                                                        // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                        />
                                                        <div>
                                                            <span className="border" />
                                                            <span className="f14x">Add Project</span>
                                                        </div>
                                                    </label>
                                                </div>
                                                <div className="customRadio">
                                                    <label className="d-flex labl">
                                                        <input type="checkbox" name="radioname" value={"clicks"}
                                                        // checked={handleGeneralChecked("clicks")}
                                                        // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                        />
                                                        <div>
                                                            <span className="border" />
                                                            <span className="f14x">Delete Project</span>
                                                        </div>
                                                    </label>
                                                </div>
                                                <div className="customRadio">
                                                    <label className="d-flex labl">
                                                        <input type="checkbox" name="radioname" value={"clicks"}
                                                        // checked={handleGeneralChecked("clicks")}
                                                        // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                        />
                                                        <div>
                                                            <span className="border" />
                                                            <span className="f14x">Rename Project</span>
                                                        </div>
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                    </Grid>
                                    <Grid item xs={12} lg={12}>
                                        <div className="border bdr-5x bg-white">
                                            <div className="d-flex align-items-center justify-content-between p-b5 p-t15 px-3">
                                                {/* <Text class="m-0">Widgets</Text> */}
                                                <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                                    Widgets
                                                </ParaLg>
                                                <AntSwitch
                                                    checked={true}
                                                    className="textSwitch"
                                                    // checked={overviewswt}
                                                    // onChange={overviewSwtFun}
                                                    inputProps={{ "aria-label": "ant design" }}
                                                />
                                            </div>
                                            <div className="p-b15 p-t5 d-grid gap-3 px-3">
                                                <div className="customRadio">
                                                    <label className="d-flex labl">
                                                        <input type="checkbox" name="radioname" value={"clicks"}
                                                        // checked={handleGeneralChecked("clicks")}
                                                        // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                        />
                                                        <div>
                                                            <span className="border" />
                                                            <span className="f14x">Manage Widgets</span>
                                                        </div>
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                    </Grid>
                                    <Grid item xs={12} md={12} lg={12}>
                                        <div className="border bdr-5x bg-white h-100">
                                            <div className="d-flex align-items-center justify-content-between p-b5 p-t15 px-3">
                                                {/* <Text class="m-0">Keywords</Text> */}
                                                <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                                    Keywords
                                                </ParaLg>
                                                <AntSwitch
                                                    checked={true}
                                                    className="textSwitch"
                                                    // checked={overviewswt}
                                                    // onChange={overviewSwtFun}
                                                    inputProps={{ "aria-label": "ant design" }}
                                                />
                                            </div>
                                            <div className="p-b15 p-t5 d-grid gap-3 px-3">
                                                <div className="customRadio">
                                                    <label className="d-flex labl">
                                                        <input type="checkbox" name="radioname" value={"clicks"}
                                                        // checked={handleGeneralChecked("clicks")}
                                                        // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                        />
                                                        <div>
                                                            <span className="border" />
                                                            <span className="f14x">Add Keywords</span>
                                                        </div>
                                                    </label>
                                                </div>
                                                <div className="customRadio">
                                                    <label className="d-flex labl">
                                                        <input type="checkbox" name="radioname" value={"clicks"}
                                                        // checked={handleGeneralChecked("clicks")}
                                                        // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                        />
                                                        <div>
                                                            <span className="border" />
                                                            <span className="f14x">Delete Keywords</span>
                                                        </div>
                                                    </label>
                                                </div>
                                                <div className="customRadio">
                                                    <label className="d-flex labl">
                                                        <input type="checkbox" name="radioname" value={"clicks"}
                                                        // checked={handleGeneralChecked("clicks")}
                                                        // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                        />
                                                        <div>
                                                            <span className="border" />
                                                            <span className="f14x">Manual Refresh</span>
                                                        </div>
                                                    </label>
                                                </div>
                                                <div className="customRadio">
                                                    <label className="d-flex labl">
                                                        <input type="checkbox" name="radioname" value={"clicks"}
                                                        // checked={handleGeneralChecked("clicks")}
                                                        // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                        />
                                                        <div>
                                                            <span className="border" />
                                                            <span className="f14x">Manage Tag</span>
                                                        </div>
                                                    </label>
                                                </div>
                                            </div>
                                        </div>
                                    </Grid>
                                </Grid>
                            </Grid>
                        </Grid>
                    </Grid>
                    <Grid item xs={12} md={12} lg={4}>
                        <Grid container spacing={2}>

                            <Grid item xs={12} md={12} lg={12}>
                                <div className="border bdr-5x bg-white h-100">
                                    <div className="d-flex align-items-center justify-content-between p-b5 p-t15 px-3">
                                        {/* <Text class="m-0">Keywords</Text> */}
                                        <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                            Competitor AI
                                        </ParaLg>
                                        <AntSwitch
                                            className="textSwitch"
                                            // checked={overviewswt}
                                            // onChange={overviewSwtFun}
                                            inputProps={{ "aria-label": "ant design" }}
                                        />
                                    </div>
                                    <div className="p-b15 p-t5 d-grid gap-3 px-3">
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Add Competitor</span>
                                                </div>
                                            </label>
                                        </div>
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Re-analysis Competitor</span>
                                                </div>
                                            </label>
                                        </div>
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Delete Competitor</span>
                                                </div>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </Grid>
                            <Grid item xs={12} lg={12}>
                                <div className="border bdr-5x bg-white">
                                    <div className="d-flex align-items-center justify-content-between p-b5 p-t15 px-3">
                                        {/* <Text class="m-0">Widgets</Text> */}
                                        <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                            Settings
                                        </ParaLg>
                                        <AntSwitch
                                            className="textSwitch"
                                            // checked={overviewswt}
                                            // onChange={overviewSwtFun}
                                            inputProps={{ "aria-label": "ant design" }}
                                        />
                                    </div>
                                    <div className="p-b15 p-t5 d-grid gap-3 px-3">
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Manage Branded Keywords</span>
                                                </div>
                                            </label>
                                        </div>
                                    </div>
                                    <div className="p-b15 p-t5 d-grid gap-3 px-3">
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Manage Connected Apps (GSC and GA)</span>
                                                </div>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </Grid>
                            <Grid item xs={12} md={12} lg={12}>
                                <div className="border bdr-5x bg-white">
                                    <div className="d-flex align-items-center justify-content-between p-t15 p-b5 px-3">
                                        {/* <Text class="m-0">All Project</Text> */}
                                        <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                            Content Audit
                                        </ParaLg>
                                        <AntSwitch
                                            className="textSwitch"
                                            // checked={overviewswt}
                                            // onChange={overviewSwtFun}
                                            inputProps={{ "aria-label": "ant design" }}
                                        />
                                    </div>
                                    <div className="p-b15 p-t5 d-grid gap-3 px-3">
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Add Page</span>
                                                </div>
                                            </label>
                                        </div>
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Page Re-audit</span>
                                                </div>
                                            </label>
                                        </div>
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Manage Primary Keywords</span>
                                                </div>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </Grid>
                        </Grid>
                    </Grid>
                    <Grid item xs={12} md={12} lg={4}>
                        <Grid container spacing={2}>
                            <Grid item xs={12} lg={12}>
                                <div className="border bdr-5x bg-white">
                                    <div className="d-flex align-items-center justify-content-between p-t15 p-b5 px-3">
                                        {/* <Text class="m-0">All Project</Text> */}
                                        <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                            Backlink Manager
                                        </ParaLg>
                                        <AntSwitch
                                            className="textSwitch"
                                            // checked={overviewswt}
                                            // onChange={overviewSwtFun}
                                            inputProps={{ "aria-label": "ant design" }}
                                        />
                                    </div>
                                    <div className="p-b15 p-t5 d-grid gap-3 px-3">
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Add Backlink</span>
                                                </div>
                                            </label>
                                        </div>
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Manage Upload</span>
                                                </div>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </Grid>
                            <Grid item xs={12} lg={12}>
                                <div className="border bdr-5x bg-white">
                                    <div className="d-flex align-items-center justify-content-between p-b5 p-t15 px-3">
                                        {/* <Text class="m-0">Widgets</Text> */}
                                        <ParaLg class="fB m-b0 lh26x d-flex align-items-center">
                                            Keyword Research
                                        </ParaLg>
                                        <AntSwitch
                                            className="textSwitch"
                                            // checked={overviewswt}
                                            // onChange={overviewSwtFun}
                                            inputProps={{ "aria-label": "ant design" }}
                                        />
                                    </div>
                                    <div className="p-b15 p-t5 d-grid gap-3 px-3">
                                        <div className="customRadio">
                                            <label className="d-flex labl">
                                                <input type="checkbox" name="radioname" value={"clicks"}
                                                // checked={handleGeneralChecked("clicks")}
                                                // onChange={(e) => handleGeneralMetrics(e.target.value, e.target.checked)}
                                                />
                                                <div>
                                                    <span className="border" />
                                                    <span className="f14x">Enable Strategy Planner and Enterprise Navigator</span>
                                                </div>
                                            </label>
                                        </div>
                                    </div>
                                </div>
                            </Grid>

                        </Grid>
                    </Grid>
                </Grid>
                <div className="d-flex justify-content-end">
                    <AppButton class="w200x" value={'Save'} />
                </div>
            </div>
        </>
    )
}

export default AccessManagement