import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Para, Title, SmallText, TextLg, Text, Tsk, AppIconButton } from "../../commonComponents/parts";
import { Grid, Tooltip, Pagination, Stack, MenuItem } from "@mui/material";
import { GoOverviewPageIcon, ClockIcon, SearchIcon } from "../../commonComponents/icons";
import { url_to_host, Arrow } from "../../common_fun";
import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import Zoom from '@mui/material/Zoom';
import { DataEmptyIcon, RefreshIcon, DeleteIcon } from "../../commonComponents/icons";
import ClickAway from "../../commonComponents/click_away";
import { CompetitorEdit, CompetitorDelete, ModalBox } from "../../commonComponents/Modals";
import axios from "axios";
import CEditDatatable from "./cedit_datatable";
import CEditTableSearch from "./cedit_table_search";
import { CEditDeleteModal } from "./cedit_delete_modal";


function CEditSearchList(props) {

    const [CGASearches, setCGASearches] = useState(Array(3).fill({}));
    const [apiLoading, setApiLoading] = useState(false);
    const [listData, setListData] = useState([]);
    const [filterData, setFilterData] = useState([]);
    const [clearSearch, setClearSearch] = useState(false);
    const [selectedKeywords, setSelectedKeywords] = useState([])
    const [deleteLoading, setDeleteLoading] = useState(false);
    const [open, setOpen] = useState(false);

    const tabledataUpdate = (data) => {
        setFilterData(data)
        setClearSearch(false)
    }

    const tablerefreshUpdate = () => {
        setFilterData(listData)
        setClearSearch(true)
    }

    const handleRowSelected = (state) => {
        const selectedIds = state.selectedRows.map(row => row.content_id);
        setSelectedKeywords(selectedIds)
    };

    useEffect(() => {
        if (props.allContentPlans) {
            setListData(props.allContentPlans)
            setFilterData(props.allContentPlans)
            setApiLoading(false)
        }
    }, [props.allContentPlans]);

    const handleDelete = () => {
        if (selectedKeywords.length === 0) {
            toast.error("Select content plans to continue")
        }
        else {
            setOpen(true)
        }
    }

    const deleteKeywords = async () => {
        if (selectedKeywords.length === 0) {
            toast.error("Select content plans to continue");
            return;
        }

        setDeleteLoading(true);

        const cookies = new Cookies();
        const userid = cookies.get('session_userid');
        const usertoken = cookies.get('session_token');
        const grpid = cookies.get('activegrp');

        if (!userid || !usertoken || !grpid) {
            toast.error("Something went wrong");
            setDeleteLoading(false);
            return;
        }

        try {
            const response = await axios.post(
                `${global.apiurl}/contentmanager/delete`,
                { userid: userid.toString(), grpid: grpid.toString(), content_ids: selectedKeywords },
                { headers: { Authorization: `Token ${usertoken}` } }
            );

            setDeleteLoading(false);
            setOpen(false);
            props.refetchContentPlans();

            response.data?.status === "true"
                ? toast.success("Content plans have been deleted successfully.")
                : toast.error("Something went wrong");

        } catch (error) {
            setDeleteLoading(false);
            setOpen(false);
            toast.error("Something went wrong");
        }
    };

    return (
        <>
            <div className="SR-table">
                <div className="header m-t20 m-b20">
                    <div className="right">
                        <CEditTableSearch tableData={filterData} tabledataUpdate={tabledataUpdate} tablerefreshUpdate={tablerefreshUpdate} clearSearch={clearSearch} />
                        <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"Reload the content plan list"} >
                            <div className="d-flex">
                                <AppIconButton
                                    // class={"boxIcon" + (selectedRowIds.length > 0 ? " kwselect" : "")}
                                    onclick={() => { setApiLoading(true); props.refetchContentPlans() }}
                                    Icon={!apiLoading ? <RefreshIcon height="18" width="18" color="currentColor" /> : <span className="loading loading--inline" />}
                                />
                            </div>
                        </Tooltip>
                        {props.canManage ? <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"Delete the selected content plans"} >
                            <div className="d-flex">
                                <AppIconButton
                                    onclick={handleDelete}
                                    class={"messageIcon"}
                                    Icon={<DeleteIcon />}
                                />
                            </div>
                        </Tooltip> : null}
                    </div>
                </div>
                <div id="listtable" className="table-responsive SR-Listtable">
                    {filterData.length > 0 ? <CEditDatatable data={filterData} tabledataUpdate={tabledataUpdate} handleRowSelected={handleRowSelected} canManage={props.canManage} />
                        : <div className="empty_list_table text-center justify-content-center">
                            <div>
                                <DataEmptyIcon />
                                <div className="ls-table-empty">
                                    No Lists Found
                                </div>
                            </div>
                        </div>
                    }
                </div>
            </div>
            {props.canManage ? <CEditDeleteModal open={open} modalClose={() => setOpen(false)} deleteLoading={deleteLoading} handleDelete={deleteKeywords} /> : null}


        </>
    );
}

export default CEditSearchList; 
