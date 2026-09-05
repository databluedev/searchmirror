import React, { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";

function CEditTableSearch({ ...props }) {
    const searchInptRef = React.useRef(null);
    const [searchVal, setSearchVal] = useState("");
    const [auditData, setAuditData] = useState([]);
    useEffect(() => {
        setAuditData(props.tableData)
        if (props.clearSearch) {
            searchInptRef.current.value = '';
        }

    }, [props.tableData, props.clearSearch])

    function searchByKeyword(e) {
        if ((e.key === "Enter" || e.charCode === 13) && searchVal !== e.target.value && e.target.value) {
            setSearchVal(e.target.value)
            props.tabledataUpdate(auditData.filter(item => JSON.stringify(item.primary_keyword).toLowerCase().indexOf(e.target.value.toLowerCase()) !== -1));
        }
        else if (e.target.value === "") {
            setSearchVal("")
            props.tablerefreshUpdate();
        }
        else {
            // Do Nothing
        }
    }

    return (
        <div className="relative">
            <Input
                ref={searchInptRef}
                type="search"
                id="outlined-basic"
                className="pr-9"
                placeholder="Search"
                autoComplete="off"
                onChange={searchByKeyword}
                onKeyPress={searchByKeyword}
            />
            <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-ink-3">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 14 14">
                    <path id="Path_426" data-name="Path 426" d="M16.77,15.666,14.126,13.03A6.158,6.158,0,0,0,15.44,9.22a6.22,6.22,0,1,0-6.22,6.22,6.158,6.158,0,0,0,3.81-1.314l2.636,2.644a.781.781,0,1,0,1.1-1.1ZM4.555,9.22A4.665,4.665,0,1,1,9.22,13.885,4.665,4.665,0,0,1,4.555,9.22Z" transform="translate(-3 -3)" fill="currentColor" />
                </svg>
            </span>
        </div>
    )
}
export default CEditTableSearch