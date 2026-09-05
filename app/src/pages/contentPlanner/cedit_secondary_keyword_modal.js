import { Modal, Box, Button, Fade, Tooltip, Zoom } from "@mui/material";
import { Title, Para } from "../commonComponents/parts";

export const CEditSecondaryKeywordChipModal = (props) => {
    return (
        <Modal className="modal-wd-graph-modal" open={props.open} onClose={props.modalClose} closeAfterTransition
            aria-labelledby="modal-modal-title" aria-describedby="modal-modal-description"
        >
            <Fade in={props.open} {...(props.open ? { timeout: 750 } : { timeout: 1000 })}>
                <Box className="wd-modal-box add-popup" >
                    <header className="wd-history-header modal-border">
                        <div className="d-flex align-items-center justify-content-between">
                            <div>
                                <Title className="wd-history-title">Secondary Keywords</Title>
                                <Para className="wd-history-sub-title mb-0">List of secondary keywords focused on this selected page.
                                </Para>
                            </div>
                            <div style={{ flex: "0 0 auto" }}>
                                <Button onClick={props.modalClose} className="wd-CloseButton chip-popup-close">
                                    <svg id="Component_69_46" data-name="Component 69 – 46" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
                                        <path id="Path_410" data-name="Path 410" d="M13.4,12l6.3-6.3a.99.99,0,0,0-1.4-1.4L12,10.6,5.7,4.3A.99.99,0,0,0,4.3,5.7L10.6,12,4.3,18.3A.908.908,0,0,0,4,19a.945.945,0,0,0,1,1,.908.908,0,0,0,.7-.3L12,13.4l6.3,6.3a.967.967,0,0,0,1.4,0,.967.967,0,0,0,0-1.4Z"
                                            transform="translate(-4 -4)" fill="#0a0a0a" />
                                    </svg>
                                </Button>
                            </div>
                        </div>
                        <div className="modal_addtag add-tag-margin">
                            <div className="tags-input keyword">
                                <div className="fM f-md mb-3 mt-4"></div>
                                <ul className="maxh110x overflow-y-auto">
                                    {props.secondaryKeywords.length > 0 && props.secondaryKeywords.map((eachKeyword, index) => (
                                        <li className="cursorP" key={index}><span className="p-r10">{eachKeyword}</span></li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    </header>
                </Box>
            </Fade>
        </Modal>
    )

}