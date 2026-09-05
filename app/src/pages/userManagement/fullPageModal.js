import { Button, Fade, Modal } from "@mui/material";
import { Box } from "@mui/system";
import React from "react";
import { Para, Title } from "../commonComponents/parts";
import { CloseIconlg } from "../commonComponents/icons";

export const CoverModal = ({ children, ...props }) => {
    return (
        <>
            <Modal
                className={`workspaceModal ${props.className || ""}`}
                open={props.open}
                onClose={props.handleClose}
                aria-labelledby="workspace-modal-title"
                aria-describedby="workspace-modal-description"
                closeAfterTransition
                hideBackdrop
            >
                <Fade in={props.open} {...(props.open ? { timeout: 1000 } : { timeout: 500 })}>
                    <Box className="fp-modal-box drp-modal">
                        <header className="fp-modal-header">
                            <div className="d-flex align-items-center justify-content-between px-2">
                                <div>
                                    <Title id="workspace-modal-title" class="fp-modal-title">
                                        {props.mnhdr}
                                    </Title>
                                    <Para id="workspace-modal-description" class="fp-modal-sub-title mb-0">
                                        {props.subhdr}
                                    </Para>
                                </div>

                                <div style={{ flex: "0 0 auto" }}>
                                    <Button aria-label="Close" title="Close" onClick={props.handleClose} className="wd-CloseButton">
                                        <CloseIconlg color="#0a0a0a" />
                                    </Button>
                                </div>
                            </div>
                        </header>
                        {children}
                    </Box>
                </Fade>
            </Modal>
        </>
    )
}
