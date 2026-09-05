import React, { useEffect, useState, useCallback } from "react";
import { Link, useHistory } from "react-router-dom";
import { Para, Title, SmallText, TextLg, Text, Tsk, AppIconButton } from "../../commonComponents/parts";
import { Grid, Tooltip, Pagination, Stack, MenuItem, Select } from "@mui/material";
import { GoOverviewPageIcon, ClockIcon, SearchIcon } from "../../commonComponents/icons";
import { url_to_host, Arrow } from "../../common_fun";
import Cookies from 'universal-cookie';
import { toast } from 'react-toastify';
import Zoom from '@mui/material/Zoom';
// import Pie from "../../commonComponents/pie";
import { DataEmptyIcon, RefreshIcon, DeleteIcon } from "../../commonComponents/icons";
import ClickAway from "../../commonComponents/click_away";
import { CompetitorEdit, CompetitorDelete, ModalBox } from "../../commonComponents/Modals";
import axios from "axios";
import LLMDatatable from "./llm_datatable";
import LLMTableSearch from "../../commonComponents/llm/llm_table_search";
import { LLMDeleteModal } from "../../commonComponents/llm/llm_delete_modal";


// Import model icons
import chatgptIcon from '../../../assets/images/chatGPT.svg';
import geminiIcon from '../../../assets/images/gemini.svg';
import claudeIcon from '../../../assets/images/claude.svg';
import perplexityIcon from '../../../assets/images/perplexity.svg';

// Down arrow component for dropdown
const Down = () => {
	return (
		<>
			<div className="downArrow">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="12.828"
					height="7.414"
					viewBox="0 0 12.828 7.414"
				>
					<path
						id="Path_380"
						data-name="Path 380"
						d="M0,5,5,0l5,5"
						transform="translate(11.414 6.414) rotate(180)"
						fill="none"
						stroke="#0a0a0a"
						strokeLinecap="round"
						strokeLinejoin="round"
						strokeWidth="2"
					/>
				</svg>
			</div>
		</>
	);
};

// Model icon mapping function
const getModelIcon = (modelName) => {
	const modelIcons = {
		'ChatGPT': chatgptIcon,
		'Gemini': geminiIcon,
		'Claude': claudeIcon,
		'Perplexity': perplexityIcon,
	};
	return modelIcons[modelName] || null;
};

// Model choices constant
// Order matches the table's provider columns, so the model tabs on the answer
// page read left-to-right in the same order the row did.
const MODEL_CHOICES = [
    ["ChatGPT", "ChatGPT"],
    ["Claude", "Claude"],
    ["Gemini", "Gemini"],
    ["Perplexity", "Perplexity"],
];


function LLMSearchList(props) {
    const history = useHistory();
    const [CGASearches, setCGASearches] = useState(Array(3).fill({}));
    const [apiLoading, setApiLoading] = useState(false);
    const [listData, setListData] = useState([]);
    const [filterData, setFilterData] = useState([]);
    const [clearSearch, setClearSearch] = useState(false);
    const [selectedprompts, setSelectedprompts] = useState([])
    const [deleteLoading, setDeleteLoading] = useState(false);
    const [open, setOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');

    const tabledataUpdate = (data) => {
        // Apply current filters to the new data
        let filteredData = data;
        
        // Apply search filter only (model filtering removed)
        if (searchQuery && searchQuery.trim() !== '') {
            filteredData = filteredData.filter(item => 
                item.prompt && item.prompt.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }
        
        setFilterData(filteredData);
        // Don't interfere with search state when updating table data
        // setClearSearch(false)
    }

    const tablerefreshUpdate = () => {
        // Apply current filters instead of showing all data
        let filteredData = listData;
        
        // Apply search filter only (model filtering removed)
        if (searchQuery && searchQuery.trim() !== '') {
            filteredData = filteredData.filter(item => 
                item.prompt && item.prompt.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }
        
        setFilterData(filteredData);
        // Don't clear search - preserve user's filters
        // setClearSearch(true)
    }

    const handleRowSelected = (state) => {
        const selectedIds = state.selectedRows.map(row => row.prompt_id);
        setSelectedprompts(selectedIds)
    };

    // Helper function to apply filters consistently
    const applyFilters = (data) => {
        let filteredData = data || listData;
        
        // Apply search filter only (model filtering removed)
        if (searchQuery && searchQuery.trim() !== '') {
            filteredData = filteredData.filter(item => 
                item.prompt && item.prompt.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }
        
        return filteredData;
    };

    // Model change handler removed since model dropdown is hidden

    const handleSearch = (searchValue) => {
        // Update search query first
        setSearchQuery(searchValue);
        
        // Use the helper function to apply filters consistently
        const filteredData = applyFilters(listData);
        setFilterData(filteredData);
        
        // Call parent component to fetch filtered data
        if (props.onSearch) {
            props.onSearch(searchValue);
        }
    };

    const handleRefresh = () => {
        setApiLoading(true);
        // Don't reset the search query - keep user's selections
        // setSearchQuery('');
        // Apply current filters to refreshed data
        if (props.refetchLLMPrompts) {
            props.refetchLLMPrompts();
        }
    };

    useEffect(() => {
        if (props.allLLMPrompts) {
            setListData(props.allLLMPrompts)
            // Don't override current filters - let the other useEffect handle filtering
        }
    }, [props.allLLMPrompts]);

    // Apply search filter when listData changes
    useEffect(() => {
        if (listData.length > 0) {
            let filteredData = listData;
            
            // Apply search filter only (model filtering removed since dropdown is hidden)
            if (searchQuery && searchQuery.trim() !== '') {
                filteredData = filteredData.filter(item => 
                    item.prompt && item.prompt.toLowerCase().includes(searchQuery.toLowerCase())
                );
            }
            
            setFilterData(filteredData);
        }
    }, [listData, searchQuery]);



    // Ensure search value is properly synchronized with parent
    useEffect(() => {
        if (props.searchValue !== undefined) {
            setSearchQuery(props.searchValue);
        }
    }, [props.searchValue]);

    // Model synchronization removed since model dropdown is hidden

    // Every model that answered this prompt, in the order the table shows them.
    // The detail page's own payload covers one model, so the row is the only
    // place that knows the others exist -- it hands them over as router state
    // and the page renders a tab for each.
    const answeringModels = (promptData) => MODEL_CHOICES
        .map(([value]) => ({
            key: value.toLowerCase(),
            label: value,
            analyticsId: promptData[`${value.toLowerCase()}_analytics_id`],
            mentioned: !!promptData[`is_mentioned_in_${value.toLowerCase()}`],
        }))
        .filter((m) => !!m.analyticsId);

    // Opening a DONE prompt from the row. It used to fall through a fixed
    // chatgpt -> claude -> gemini -> perplexity chain, so with more than one
    // model configured the row ALWAYS opened ChatGPT -- and if the model that
    // named the brand was Gemini, the mention was unreachable and the page said
    // "ChatGPT did not name your brand". Open the answer that named the brand
    // when there is one, otherwise the first that answered, and carry the rest.
    const handleRowOpen = (promptData) => {
        const models = answeringModels(promptData);
        const target = models.find((m) => m.mentioned) || models[0];
        if (!target) {
            toast.error("No stored answer for this prompt yet.");
            return;
        }
        history.push(`/prompt/citations/${target.analyticsId}?model=${target.key}`, { models });
    };

    const handleCitationsClick = (promptData, modelType = 'total') => {
        // The list endpoint returns <model>_analytics_id for every provider, so
        // resolve by the model that was clicked. This used to switch on chatgpt
        // and claude only, so clicking a Gemini or Perplexity cell opened
        // ChatGPT's row (or nothing) instead of the model the user asked for.
        const key = (modelType || 'total').toLowerCase();
        const models = answeringModels(promptData);
        const analyticsId = promptData[`${key}_analytics_id`];

        if (!analyticsId) {
            // No row for the model that was clicked: open what there is rather
            // than silently substituting a different model behind that title.
            handleRowOpen(promptData);
            return;
        }

        history.push(`/prompt/citations/${analyticsId}?model=${key}`, { models });
    };

    const handleDelete = () => {
        if (selectedprompts.length === 0) {
            toast.error("Select Prompts to Continue")
        }
        else {
            setOpen(true)
        }
    }

    const deleteKeywords = async () => {
        if (selectedprompts.length === 0) {
            toast.error("Select Prompts to Continue");
            return;
        }

        setDeleteLoading(true);

        const cookies = new Cookies();
        const userid = cookies.get('session_userid');
        const usertoken = cookies.get('session_token');

        if (!userid || !usertoken) {
            toast.error("Something went wrong");
            setDeleteLoading(false);
            return;
        }

        try {
            const response = await axios.post(
                `${global.apiurl}/llmtracker/delete`,
                { userid: userid.toString(), prompt_ids: selectedprompts },
                { headers: { Authorization: `Token ${usertoken}` } }
            );

            setDeleteLoading(false);
            setOpen(false);
            props.refetchLLMPrompts();

            response.data?.status === "true"
                ? toast.success("Prompts have been deleted successfully.")
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
                        <LLMTableSearch 
                            tableData={filterData} 
                            tabledataUpdate={tabledataUpdate} 
                            tablerefreshUpdate={tablerefreshUpdate} 
                            clearSearch={clearSearch}
                            onSearch={handleSearch}
                            searchValue={searchQuery}
                        />
                        
                        {/* Models Dropdown - Hidden */}
                        {/* <div>
                            <Select
                                fullWidth
                                className="project-toggleSelect sm"
                                labelId="demo-simple-select-error-label"
                                id="demo-simple-select-error"
                                IconComponent={Down}
                                inputProps={{ "aria-label": "Without label" }}
                                value={selectedModel}
                                onChange={(event) => {
                                    handleModelChange(event.target.value);
                                }}
                                renderValue={(selectedId) => {
                                    const icon = getModelIcon(selectedId);
                                    return (
                                        <div className="d-flex align-items-center">
                                            {icon && <img src={icon} alt={selectedId} width={20} height={20} className="m-r5" />}
                                            <span>{selectedId}</span>
                                        </div>
                                    );
                                }}
                            >
                                {MODEL_CHOICES.map(([value, label]) => (
                                    <MenuItem key={value} value={value}>
                                        <div className="d-flex align-items-center">
                                            <img src={getModelIcon(value)} alt={label} width={20} height={20} className="m-r5" />
                                            <span>{label}</span>
                                        </div>
                                    </MenuItem>
                                ))}
                            </Select>
                        </div> */}
                        
                        <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"Reset all the filters"} >
                            <div className="d-flex">
                                <AppIconButton
                                    // class={"boxIcon" + (selectedRowIds.length > 0 ? " kwselect" : "")}
                                    onclick={handleRefresh}
                                    Icon={!apiLoading ? <RefreshIcon height="18" width="18" color="currentColor" /> : <span className="loading loading--inline" />}
                                />
                            </div>
                        </Tooltip>
                        {props.canManage ? <Tooltip classes={{ tooltip: "Tltpsmall text-center" }} placement="top" title={"Delete the selected prompts"} >
                            <div className="d-flex">
                                <AppIconButton
                                    onclick={handleDelete}
                                    class={"messageIcon"}
                                    Icon={<DeleteIcon />}
                                />
                            </div>
                        </Tooltip> : null}
                        <div>
                            {/*  <KWDelete selectedRowIds={selectedRowIds} updatefullpage={props.updatefullpage} basedata={props.basedata} /> */}
                        </div>
                    </div>
                </div>
                <div id="listtable" className="table-responsive SR-Listtable">
                    {filterData.length > 0 ? <LLMDatatable data={filterData} tabledataUpdate={tabledataUpdate} handleRowSelected={handleRowSelected} onCitationsClick={handleCitationsClick} onRowOpen={handleRowOpen} canManage={props.canManage} />
                        : <div className="empty_list_table text-center justify-content-center">
                            <div>
                                <DataEmptyIcon />
                                <div className="ls-table-empty">
                                    No Prompts Found
                                </div>
                            </div>
                        </div>
                    }
                </div>
            </div>
            {props.canManage ? <LLMDeleteModal open={open} modalClose={() => setOpen(false)} deleteLoading={deleteLoading} handleDelete={deleteKeywords} /> : null}

        </>
    );
}

export default LLMSearchList; 
