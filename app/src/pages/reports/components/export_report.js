import axios from "axios";
import React, { useState } from "react";
import { FormControl } from "@mui/material";
import { toast } from "react-toastify";
import Cookies from "universal-cookie";

import { AppButton } from "../../commonComponents/parts";


function downloadFilename(headers) {
    const disposition = headers && headers["content-disposition"];
    const match = disposition && disposition.match(/filename="?([^";]+)"?/i);
    return match ? match[1] : "searchmirror-keyword-ranking.csv";
}


function ExportReport() {
    const [isExporting, setIsExporting] = useState(false);

    const handleReport = async () => {
        if (isExporting) return;
        setIsExporting(true);

        const cookies = new Cookies();
        const grpid = cookies.get('activegrp');
        if (!grpid) { return; }   // no project: nothing to export
        try {
            const response = await axios.post(
                global.apiurl + '/local_report_export',
                {
                    userid: cookies.get('session_userid'),
                    grpid: cookies.get('activegrp'),
                },
                {
                    headers: { Authorization: 'Token ' + cookies.get('session_token') },
                    responseType: 'blob',
                }
            );
            const objectUrl = window.URL.createObjectURL(response.data);
            const link = document.createElement('a');
            link.href = objectUrl;
            link.download = downloadFilename(response.headers);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(objectUrl);
            toast.success("Keyword ranking report downloaded.");
        } catch (error) {
            const status = error && error.response && error.response.status;
            if (status === 403) {
                toast.error("You do not have permission to export reports.");
            } else {
                toast.error("Report download failed. Please try again.");
            }
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <FormControl sx={{ m: 1, minWidth: 120 }}>
            <AppButton
                value="Export"
                color="white"
                class="borderBtn"
                noIcon="d-none"
                type="button"
                loading={isExporting}
                disabled={isExporting}
                onclick={handleReport}
            />
        </FormControl>
    );
}

export default React.memo(ExportReport);
