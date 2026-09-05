import { InputAdornment, TextField } from "@mui/material";
import React, { useEffect, useState, useCallback } from "react";

function LLMTableSearch({ onSearch, searchValue, ...props }) {
    const searchInptRef = React.useRef(null);
    const [searchVal, setSearchVal] = useState(searchValue || "");
    
    // Update local state when prop changes
    useEffect(() => {
        if (searchValue !== undefined) {
            setSearchVal(searchValue);
        }
    }, [searchValue]);
    
    useEffect(() => {
        if (props.clearSearch) {
            setSearchVal('');
            if (onSearch) {
                onSearch('');
            }
        }
    }, [props.clearSearch, onSearch]);

    const handleSearchChange = (e) => {
        const value = e.target.value;
        setSearchVal(value);
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSearch();
        }
    };

    const handleSearch = () => {
        if (onSearch) {
            onSearch(searchVal);
        }
    };

    const handleClearSearch = () => {
        setSearchVal('');
        if (onSearch) {
            onSearch(''); // Clear search results
        }
    };

    return (
        <>
            <TextField
                inputRef={searchInptRef}
                type="search"
                id="outlined-basic"
                variant="outlined"
                placeholder="Search prompts..."
                autoComplete="off"
                value={searchVal}
                onChange={handleSearchChange}
                onKeyPress={handleKeyPress}
                size="small"
                style={{ minWidth: '250px' }}
                InputProps={{
                    endAdornment: (
                        <InputAdornment position="end">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14">
                                <path id="Path_426" data-name="Path 426" d="M16.77,15.666,14.126,13.03A6.158,6.158,0,0,0,15.44,9.22a6.22,6.22,0,1,0-6.22,6.22,6.158,6.158,0,0,0,3.81-1.314l2.636,2.644a.781.781,0,1,0,1.1-1.1ZM4.555,9.22A4.665,4.665,0,1,1,9.22,13.885,4.665,4.665,0,0,1,4.555,9.22Z" transform="translate(-3 -3)" fill="currentColor" />
                            </svg>
                        </InputAdornment>
                    )
                }}
            />
        </>
    )
}
export default LLMTableSearch