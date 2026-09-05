import React, { useState, useEffect } from "react";
import { AppButton, Text } from "../../commonComponents/parts";
import { Grid } from "@mui/material";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { useHistory } from "react-router-dom";
import { BrandKeywordInput } from "../../commonComponents/manage_tag";
import { toast } from 'react-toastify';
import "../../addProject/style.scss";

function BrandKeywords(props) {

    const [pageLoad, setpageLoad] = useState(true);
    const [btnloading, setBtnloading] = useState(false);

    const cookies = new Cookies();
    const usertoken = cookies.get('session_token')
    const userid = cookies.get('session_userid')
    const grpid = cookies.get('activegrp');
    const history = useHistory();

    // Brand Keywords
    const [brandKWS, setBrandKWS] = useState([]);

    const loadBrandedKeywords = () => {
        if (userid && grpid) {
            var data = {
                'userid': userid,
                'grpid': grpid,
                'type': "list",
            };
            axios.post(global.apiurl + '/project_branded_keywords', data, {
                headers: { 'Authorization': 'Token ' + usertoken }
            }).then(response => {
                return response.data;
            }).then(res => {
                if (res.status === "true") {
                    setBrandKWS(res.brand_keywords)
                }
            })
        }
    }

    const handleSaveKeywords = () => {

        if (brandKWS.length === 0) {
            toast.error("Add Keywords to Continue")
            return false;
        }

        if (userid && grpid) {
            var data = {
                'userid': userid,
                'grpid': grpid,
                'brand_keywords': brandKWS,
                'type': "save",
            };
            axios.post(global.apiurl + '/project_branded_keywords', data, {
                headers: { 'Authorization': 'Token ' + usertoken }
            }).then(response => {
                return response.data;
            }).then(res => {
                if (res.status === "true") {
                    toast.success(res.message)
                } else {
                    toast.error(res.message)
                }
            })
        }
    }

    useEffect(() => {
        if (!usertoken || !userid) {
            history.push("/login");
        }
        loadBrandedKeywords()
        setTimeout(() => {
            setpageLoad(false)
        }, 2000);
    }, [])

    return (
        <>

            {pageLoad ?
                <div className="d-flex justify-content-center align-items-center text-center h80vh">
                    <div className="loading" />
                </div>
                :
                <div className="m-t20">
                    <div className="m-b50">
                        <Grid container spacing={3} className="">
                            <Grid item xs={12} md={8} lg={8}>
                                <Text class="text-justify m-b2">
                                    Branded keywords are search queries that are directly associated with your brand, products, or services.
                                </Text>
                                {props.canManage ? <>
                                    <form>
                                        <Grid container spacing={3} className="">
                                            <Grid item xs={9} md={9} lg={9}>
                                                <div className="addtag m-b2">
                                                    <BrandKeywordInput selectedtags={brandKWS} tagupdatefun={(tag) => setBrandKWS(tag)} othertg={[]} othertagupdatefun={() => { }} othertags={[]} />
                                                    <div className="m-b20"> <AppButton value="Save" class="wd-btn-add " loading={btnloading} disabled={btnloading} noIcon="d-none" onclick={handleSaveKeywords}></AppButton></div>
                                                </div>
                                            </Grid>
                                        </Grid>
                                    </form>
                                </> : (
                                    <div className="m-t20">
                                        <Text class="secondaryClr m-b10">Read-only access.</Text>
                                        <Text>{brandKWS.length > 0 ? brandKWS.join(", ") : "No branded keywords configured."}</Text>
                                    </div>
                                )}
                            </Grid>
                        </Grid>
                    </div>
                </div>
            }
        </>
    );
}

export default BrandKeywords;
