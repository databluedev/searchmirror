import React, { useContext, useEffect, useMemo, useRef, useState } from "react";
import { Grid, Switch, TextField } from "@mui/material";
import styled from "@emotion/styled";
import axios from "axios";
import Cookies from "universal-cookie";
import { toast } from "react-toastify";

import { TeamContext } from "..";
import { AppButton, ParaLg, RefInput, TextLg } from "../../commonComponents/parts";

const MODULES = [
    { key: "Prjcts", label: "All Projects", locked: true, permissions: ["Add Project", "Delete Project", "Rename Project"] },
    { key: "Widgets", label: "Dashboard", permissions: ["Manage Widgets"] },
    { key: "Keyword", label: "Keywords", permissions: ["Add Keywords", "Delete Keywords", "Manual Refresh", "Manage Tag", "Manage Notes"] },
    { key: "LLMTracker", label: "Geo Citations", permissions: ["Manage Geo Citations"] },
    { key: "ContentPlanner", label: "Content Planner", permissions: ["Manage Content"] },
    { key: "CompAi", label: "Competitors", permissions: ["Add Competitor", "Re-analysis Competitor", "Delete Competitor"] },
    { key: "Reports", label: "Reports", permissions: ["Add Report", "Delete Report", "Enable Export", "Rename Report"] },
    { key: "Settings", label: "Project Settings", permissions: ["Manage Recipients", "Manage Branded Keywords", "Manage Connected Apps"] },
];

const DEFAULT_PRIVILEGES = { Prjcts: [], Widgets: [], Keyword: [] };

const AntSwitch = styled(Switch)(({ theme }) => ({
    width: 28,
    height: 16,
    padding: 0,
    display: "flex",
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
        width: 12,
        height: 12,
        borderRadius: 6,
    },
    "& .MuiSwitch-track": {
        borderRadius: 8,
        opacity: 1,
        backgroundColor: theme.palette.mode === "dark" ? "rgba(255,255,255,.35)" : "rgba(0,0,0,.25)",
        boxSizing: "border-box",
    },
}));

function Permission({ disabled = false, checked, label, onChange }) {
    return (
        <label className="customRadio d-flex labl">
            <input
                disabled={disabled}
                type="checkbox"
                checked={checked}
                onChange={(event) => onChange(event.target.checked)}
            />
            <div>
                <span className="border" />
                <span className="f14x">{label}</span>
            </div>
        </label>
    );
}

function AddRoles() {
    const roleRef = useRef();
    const [roleError, setRoleError] = useState("");
    const [privileges, setPrivileges] = useState(DEFAULT_PRIVILEGES);
    const { rlEdNm, rlEdPrvlgs, handleRolesInitializer, rlId, setRoles } = useContext(TeamContext);

    useEffect(() => {
        if (roleRef.current) roleRef.current.value = rlEdNm || "";
        setPrivileges(
            rlEdPrvlgs && Object.keys(rlEdPrvlgs).length
                ? rlEdPrvlgs
                : DEFAULT_PRIVILEGES
        );
        setRoleError("");
    }, [rlEdNm, rlEdPrvlgs]);

    const allSelected = useMemo(
        () => MODULES.every(({ key, permissions }) => (
            Object.prototype.hasOwnProperty.call(privileges, key)
            && permissions.every((permission) => privileges[key].includes(permission))
        )),
        [privileges]
    );

    const setModule = (module, enabled) => {
        if (module.locked) return;
        setPrivileges((current) => {
            const next = { ...current };
            if (enabled) next[module.key] = next[module.key] || [];
            else delete next[module.key];
            return next;
        });
    };

    const setPermission = (module, permission, enabled) => {
        setPrivileges((current) => {
            const selected = current[module.key] || [];
            return {
                ...current,
                [module.key]: enabled
                    ? Array.from(new Set([...selected, permission]))
                    : selected.filter((item) => item !== permission),
            };
        });
    };

    const selectAll = (enabled) => {
        if (!enabled) {
            setPrivileges({ Prjcts: [] });
            return;
        }
        setPrivileges(Object.fromEntries(
            MODULES.map(({ key, permissions }) => [key, [...permissions]])
        ));
    };

    const saveRole = () => {
        const roleName = (roleRef.current?.value || "").trim();
        if (!roleName) {
            setRoleError("Enter a role name");
            return;
        }

        const cookies = new Cookies();
        const payload = {
            id: rlId,
            userid: cookies.get("session_userid"),
            rl: roleName,
            mdles: privileges,
        };
        const config = { headers: { Authorization: `Token ${cookies.get("session_token")}` } };
        const request = typeof rlId === "number"
            ? axios.put(`${global.apiurl}/my_view/`, payload, config)
            : axios.post(`${global.apiurl}/my_view/`, payload, config);

        setRoles((current) => ({ ...current, adRlLod: true }));
        request.then(({ data }) => {
            if (data.st !== 1) {
                toast.error(data.dt || "Role could not be saved");
                return;
            }
            toast.success(data.dt);
            handleRolesInitializer();
        }).catch(() => {
            toast.error("Role could not be saved");
        }).finally(() => {
            setRoles((current) => ({ ...current, adRlLod: false, addRolOpn: false }));
        });
    };

    return (
        <div className="p-l30 p-b70 p-r40 rlFrm">
            <div className="border bdr-5x p-4 m-b20">
                <ParaLg class="fB m-b5">Role details</ParaLg>
                <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                        <RefInput label="Role" span="*" spanclassname="redClr p-l5">
                            <TextField
                                placeholder="Manager"
                                error={Boolean(roleError)}
                                helperText={roleError}
                                fullWidth
                                inputRef={roleRef}
                                onChange={() => setRoleError("")}
                            />
                        </RefInput>
                    </Grid>
                </Grid>
            </div>

            <div className="border p-4 bdr-5x">
                <div className="d-flex align-items-center justify-content-between p-b15">
                    <div>
                        <ParaLg class="fB m-b5">Assign privileges</ParaLg>
                        <p className="lightTxtClr m-b0">Choose the product areas and actions this role can use.</p>
                    </div>
                    <Permission label="Select all" checked={allSelected} onChange={selectAll} />
                </div>

                <Grid container spacing={2}>
                    {MODULES.map((module) => {
                        const enabled = Object.prototype.hasOwnProperty.call(privileges, module.key);
                        return (
                            <Grid item xs={12} md={6} lg={4} key={module.key}>
                                <div className={`border bdr-5x bg-white bxShdw h-100 ${enabled ? "" : "modDesctd"}`}>
                                    <div className="d-flex align-items-center justify-content-between p-t15 p-b5 px-3">
                                        <TextLg class="fB m-b0 lh26x">{module.label}</TextLg>
                                        <AntSwitch
                                            checked={enabled}
                                            disabled={module.locked}
                                            onChange={(event) => setModule(module, event.target.checked)}
                                            inputProps={{ "aria-label": `${module.label} access` }}
                                        />
                                    </div>
                                    <div className="p-b15 p-t5 d-grid gap-3 px-3">
                                        {module.permissions.map((permission) => (
                                            <Permission
                                                key={permission}
                                                label={permission}
                                                disabled={!enabled}
                                                checked={enabled && privileges[module.key].includes(permission)}
                                                onChange={(checked) => setPermission(module, permission, checked)}
                                            />
                                        ))}
                                    </div>
                                </div>
                            </Grid>
                        );
                    })}
                </Grid>

                <div className="d-flex justify-content-end m-t30">
                    <AppButton
                        noIcon="d-none"
                        value={typeof rlId === "number" ? "Update Role" : "Create Role"}
                        onclick={saveRole}
                    />
                </div>
            </div>
        </div>
    );
}

export default AddRoles;
