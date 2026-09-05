import React, { useMemo, useState } from "react";
import Skeleton from '@mui/material/Skeleton';

import { Table, TableBody, TableCell, TableContainer, TableHead, TablePagination, TableRow, TableSortLabel, Tooltip } from "@mui/material";
import Zoom from '@mui/material/Zoom';

import { FillArrow } from "../../commonComponents/icons";

import { Tsk } from "../../commonComponents/parts";

const GSC_OVERVIEW={
    "R1" :{'dt':["GSC Queries Report", "Year 2024", "Total Clicks & Impressions"], 'ln':5},
    "R2" : {'dt':["Brand & Non-Brand Queries Bifurcation", "Year2024", "Brand Clicks & Impressions"], 'ln':7},
    "R3" : {'dt':["Brand & Non-Brand Queries Bifurcation", "Year2024", "Non-Brand Clicks & Impressions"], 'ln':7},
    "R4" : {'dt':["Total Clicks & Impressions as per available GSC Data", "Sum of Brand & Non-Brand as per Available Queries Data"], 'ln':4},
    "R5" : {'dt':["Brand & Non-Brand Queries Bifurcation", "Year2024", ["Brand Clicks & Impressions", "Non-Brand Clicks & Impressions"]], 'ln':[14, 14, 7]}
}
// const R1 = ["GSC Queries Report", "Year 2024", "Total Clicks & Impressions"]
// const R2 = ["Brand Clicks & Impressions", "Year2024", "Brand & Non-Brand Queries Bifurcation"]
// const R3 = ["Non-Brand Clicks & Impressions", "Year2024", "Brand & Non-Brand Queries Bifurcation"]
// const R4 = ["Total Clicks & Impressions as per available GSC Data", "Sum of Brand & Non-Brand as per Available Queries Data"]

function EcomWidgetTable({ children, ...props }) {
    const SkeletonColor = "var(--surface-2)"
    const [page, setPage] = useState(0)
    // The container used to cap at 360px while the footer said "1-30 of 30",
    // so a reader saw six rows, was told there were thirty, and the sixth was
    // sliced in half by the cap. The page size is now what is actually on
    // screen: no inner scroll, and the count in the footer is the truth.
    const [rowsPerPage, setRowsPerPage] = useState(10)
    const [order, setOrder] = useState('asc')
    // No column is sorted until one is clicked. The old default named a
    // "volume" column that no report has, so every row compared undefined
    // against undefined and the first click on a real column looked inert.
    const [orderBy, setOrderBy] = useState(null)

    const percentageRegEx = /^[+-]?\d+(\.\d+)?%$/
    const lenOfMtrics = ((props.metrics).length) - (props.metrics ? props.metrics : []).filter(item => item === '').length
    const lenOfChngunts = props.colcnt
    const columnCount = lenOfChngunts / lenOfMtrics
    // /^[+-]?\d+(\.\d+)?%$/
    const handleSessionKey = (id) => {
        if (typeof (id) === 'string' && id.search('~~') !== -1) {
            return parseFloat(id)
        }
        return id
    }

    const NoData = () => {
        return (
            <div className="d-flex justify-content-center align-items-center text-center reportEmptyRows">
                <div>
                    <div className="ls-table-empty">No rows</div>
                    <p className="ls-table-empty-body">
                        This report has no rows yet. Its next scheduled run will fill it in.
                    </p>
                </div>
            </div>
        );
    };

    const handleItem = (item) => {
        var psdItem = item
        if (Number(item)) {
            psdItem = Math.abs(item)
            psdItem = parseFloat(psdItem.toFixed(2))
        } else if (percentageRegEx.test(item)) {
            psdItem = percentageRegEx.test(item) ? Math.abs(parseFloat(item)) : item
        } else if (typeof (item) === 'string' && item.search('~~') !== -1) {
            psdItem = parseFloat(item)
        }
        return psdItem
    }

    // reportData[0] is the row array. A sheet whose window produced no rows
    // came through here as an empty array, and Object.keys(undefined) took the
    // whole page down with it. NoData was written for exactly this case and was
    // never reachable; it is now.
    const reportRows = Array.isArray(props.reportData[0]) ? props.reportData[0] : []
    const hasRows = reportRows.length > 0 && reportRows[0] && typeof reportRows[0] === 'object'
    const customColumns = hasRows
        ? Object.keys(reportRows[0]).map((item) => ({ id: item, label: item }))
        : []
    const piningIndex = customColumns.filter(item => item.id === 'Sr No' || item.id === 'Type')
    // console.log(piningIndex)

    const handleChangePage = (event, newPage) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event) => {
        setRowsPerPage(+event.target.value);
        setPage(0);
    };
    const handleRequestSort = (event, property) => {
        const isAsc = orderBy === property && order === 'asc';
        setOrder(isAsc ? 'desc' : 'asc');
        setOrderBy(property);
    };
    const createSortHandler = (property) => (event) => {
        handleRequestSort(event, property);
    };

    // Report cells are a mix of numbers, "12.5%", "3~~12" session keys, plain
    // text and the "NA" placeholder. Comparing those with < and > sorted them
    // lexically -- "100" landed before "5", and "NA" sorted among the numbers --
    // so a column that looked sorted was not. Numbers compare numerically,
    // text compares as text, and "not measured" always sits at the bottom
    // whichever way the column is pointing.
    const MISSING = new Set(['NA', '', '-'])

    function sortKey(value) {
        if (value === null || value === undefined || MISSING.has(value)) {
            return { missing: true }
        }
        if (typeof value === 'number' && !Number.isNaN(value)) {
            return { num: value }
        }
        if (typeof value === 'string') {
            if (percentageRegEx.test(value) || value.search('~~') !== -1) {
                const parsed = parseFloat(value)
                if (!Number.isNaN(parsed)) {
                    return { num: parsed }
                }
            }
            if (value.trim() !== '' && !Number.isNaN(Number(value))) {
                return { num: Number(value) }
            }
            return { text: value.toLowerCase() }
        }
        return { text: String(value).toLowerCase() }
    }

    function ascendingComparator(a, b, property) {
        const left = sortKey(a[property])
        const right = sortKey(b[property])
        if (left.missing || right.missing) {
            if (left.missing && right.missing) return 0
            return left.missing ? 1 : -1
        }
        if ('num' in left && 'num' in right) {
            return left.num - right.num
        }
        if ('num' in left) return -1
        if ('num' in right) return 1
        return left.text.localeCompare(right.text)
    }

    function getComparator(order, property) {
        return order === 'desc'
            ? (a, b) => -ascendingComparator(a, b, property)
            : (a, b) => ascendingComparator(a, b, property);
    }

    function stableSort(array, comparator) {
        const stabilizedThis = array.map((el, index) => [el, index]);
        stabilizedThis.sort((a, b) => {
            const order = comparator(a[0], b[0]);
            if (order !== 0) {
                return order;
            }
            return a[1] - b[1];
        });
        return stabilizedThis.map((el) => el[0]);
    }

    const visibleRows = useMemo(
        () => {
            const ordered = orderBy
                ? stableSort(reportRows, getComparator(order, orderBy))
                : reportRows;
            return ordered.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);
        },
        [order, orderBy, page, rowsPerPage, props.reportData, props.loading],
    );
    // A text cell claims 250px; a number claims 100px. isNaN('-') is true, so
    // the "not measured" placeholder counted as text and a column that was
    // nothing but dashes -- Avg. Volume on every report, since search volume
    // needs an OAuth that is not wired -- took 250px of the card and pushed the
    // Change column, the one the report exists for, off the right-hand edge.
    // Missing is missing, whatever shape it arrives in.
    // maxW250x / maxW100x named classes that are not declared anywhere; the
    // caps live in this page's stylesheet now.
    const isTextValue = (value) => (
        !MISSING.has(value)
        && value !== null
        && value !== undefined
        && isNaN(value)
        && !percentageRegEx.test(value)
        && !handleOvSession(value)
    )

    const getClassName = (value, index) => {
        if (!isTextValue(value)) {
            return "text-truncate-ecom minW100x";
        }
        return index === piningIndex.length
            ? "text-truncate-ecom minW250x piningCls"
            : "text-truncate-ecom minW250x";
    };

    const handleColor = (index) => {
        const colors = ['var(--surface)', 'var(--surface-2)']
        return colors[index % 2]
    }

    const handleOvSession = (item) => {
        if (typeof (item) === 'string' && item.search('~~') !== -1) {
            if (parseFloat(item)) {
                return true
            }
        }
        return false
    }
    function isValidURL(string) {
        try{
            new URL(string)
            return true
        }catch{
            return false
        } 
    }
    // Numbers, percentages and the "NA" placeholder centre in their column;
    // keywords and URLs stay left. This ran a console.log per cell, so a
    // thirty-row report wrote 240 lines to the console on every render.
    const isCenter=(value)=>{
        if (percentageRegEx.test(value) || Number(value) === Number(value) || value==='init' || value==="NA"){
            return 'text-center'
        }
    }

    // A tooltip that repeats a number the reader can already see is noise on
    // every cell of the table. Only text that the column can clip earns one.
    const needsTooltip = (value) => {
        if (typeof value !== 'string') return false
        if (percentageRegEx.test(value)) return false
        if (value.trim() !== '' && !Number.isNaN(Number(value))) return false
        return true
    }

    const isChangeColumn = (label) => typeof label === 'string' && /change/i.test(label)

    const changeDirection = (value) => {
        const parsed = typeof value === 'number' ? value : parseFloat(value)
        if (Number.isNaN(parsed) || parsed === 0) return null
        return parsed < 0
            ? <span className="arrow red m-l5" aria-label="down"><FillArrow /></span>
            : <span className="arrow green m-l5" aria-label="up"><FillArrow /></span>
    }

    if (!hasRows) {
        return <NoData />;
    }

    return (
        <>
            <TableContainer>
                <Table>
                    <TableHead className="reportsDnmcWdgtTable" style={{ position: 'sticky', top: 0, backgroundColor: "var(--surface)", zIndex: '2', fontFamily: 'inherit !important' }}>
                        {(props.sheet_type)&&
                        <>
                            {props.sheet_type==="R5"?
                                <>
                                   <TableRow>
                                        <TableCell colSpan={14} align="center">
                                            Brand & Non-Brand Queries Bifurcation
                                        </TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell colSpan={14} align="center">
                                            Year2024
                                        </TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell colSpan={7} align="center">
                                            Brand Clicks & Impressions
                                        </TableCell>
                                        <TableCell colSpan={7} align="center">
                                            Non-Brand Clicks & Impressions
                                        </TableCell>
                                    </TableRow>                                 
                                </>
                            :
                            GSC_OVERVIEW[props.sheet_type]['dt'].map((item, index)=>(
                                    // GSC_OVERVIEW is a module-level constant: this list can
                                    // neither reorder nor be filtered, so the index is a stable
                                    // identity. The unkeyed fragment was the array element.
                                    <TableRow key={index} className="fM">
                                        <TableCell colSpan={GSC_OVERVIEW[props.sheet_type]['ln']} align="center">
                                            {item}
                                        </TableCell>
                                    </TableRow>
                            ))
                            }
                        </>
                        }
                        {(props.metrics && props.colcnt) ?
                        <TableRow className="fM">
                            <>
                                    {props.metrics.map((item, index) => (
                                            // props.metrics is a fixed column layout whose
                                            // spacer entries are falsy, so the value is not an
                                            // identity; the index is. The unkeyed fragment
                                            // around the cell was the array element.
                                            <TableCell key={index} sx={{ backgroundColor: handleColor(index) }} className={!item ? "piningCls" : ""} align='center' colSpan={item ? columnCount : 1}>
                                                {item}
                                            </TableCell>
                                    ))}
                            </>
                        </TableRow>
                        : null}
                        <TableRow className="fM">
                            {customColumns.map((column, index) => (
                                <TableCell
                                    key={column.id}
                                    className={`${index === piningIndex.length ? 'text-truncate-ecom piningCls' : 'text-truncate-ecom text-center'}${column.label === 'Session primary channel group (Default Channel Group)' ? ' whiteInitial' : ''} ${column.label==='Type'?'text-left':''} ${column.label==='Sr No'?'text-center':''}`}
                                >
                                    <TableSortLabel
                                        active={orderBy === column.id}
                                        direction={orderBy === column.id ? order : 'asc'}
                                        onClick={createSortHandler(column.id)}
                                    >
                                        {column.label==='DEMO'?
                                       <Tsk/>
                                       :
                                        <span>{column.label}</span>
                                        }
                                    </TableSortLabel>
                                </TableCell>
                            ))}
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {(visibleRows)
                            .map((row, rwindex) => {
                                return (
                                    <TableRow hover key={rwindex}>
                                        {customColumns.map((column, clindex) => {
                                            // console.log(clindex)
                                            const value = row[column.id];
                                            return (
                                                value!=="DEMO" ?
                                                    <TableCell className={`${getClassName(value, clindex)} ${isCenter(value)}`} key={clindex}>
                                                        {value !== 'NA' && value !== null && value !== undefined && value !== '' ?
                                                            (needsTooltip(value) ?
                                                                <Tooltip classes={{ tooltip: "customTooltip text-center" }} placement={"top-start"} TransitionComponent={Zoom} title={isValidURL(value) ? <a href={value} target="_blank" rel="noreferrer">{value}</a> : handleSessionKey(value)} arrow={false}>
                                                                    <span style={{ 'maxWidth': '145px' }} className="cursorP text-truncate-ecom">{handleItem(value)}</span>
                                                                </Tooltip>
                                                                :
                                                                <span style={{ 'maxWidth': '145px' }} className="text-truncate-ecom">{handleItem(value)}</span>
                                                            )
                                                            :
                                                            <span style={{ maxWidth: '145px' }} className="text-truncate-ecom wd-subTitle" title="Not measured in this window">{"-"}</span>
                                                        }
                                                        {/* Direction is only meaningful in a change column. The
                                                            arrow used to fire on any negative number in any column,
                                                            and it only ever pointed down: the backend returns
                                                            past - live, so an improvement came through positive and
                                                            was drawn with no arrow at all, while the magnitude was
                                                            printed through Math.abs. A reader could not tell "moved
                                                            up five" from "did not move". Both directions are drawn
                                                            now, and only where a direction exists. */}
                                                        {isChangeColumn(column.label) ? changeDirection(value) : null}
                                                    </TableCell>
                                                    :
                                                    <TableCell key={`demo-${rwindex}-${clindex}`}>
                                                        <div className="d-flex align-items-center overflow-hidden">
                                                            <div className="d-flex align-items-center">
                                                                <div className="m-l8 wd-table-keyword">
                                                                    <Skeleton variant="rectangular" width={"100%"} height={18} sx={{ bgcolor: SkeletonColor }} />
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </TableCell>
                                            );
                                        })}
                                    </TableRow>
                                );
                            })}
                    </TableBody>
                </Table>
            </TableContainer>
            <TablePagination
                rowsPerPageOptions={[10, 25, 50]}
                className="reportsDnmcWdgtTbleFooter"
                component="div"
                count={reportRows.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={(event, page) => { setPage(page) }}
                onRowsPerPageChange={handleChangeRowsPerPage}
                showFirstButton
                showLastButton
            />
        </>
    )
}

export default React.memo(EcomWidgetTable);
