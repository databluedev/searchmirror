import { ModalBox } from "../Modals"
import { AppButton } from "../parts"
import { Box } from "@mui/system"

export function LLMDeleteModal(props) {
    return (
        <ModalBox title={''} open={props.open} handleClose={props.modalClose} onClose={props.modalClose}>
            <div className="px-4 project-delete">
                <div className="pb-2 f20x">Delete selected prompts?</div>
                <div>This will permanently delete the prompts and their associated analysis and citations.</div>

                <div className="pb-4 d-flex flex-wrap justify-content-end">
                    <Box
                        className="addButton pt-3 m-r15"
                        sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto", color: 'var(--ink-3)' }}
                    >
                        <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn" noIcon="d-none"></AppButton>
                    </Box>
                    <Box
                        className="addButton pt-3"
                        sx={{ minWidth: "100px", maxWidth: "150px", flex: "0 0 auto" }}
                    >
                        <AppButton loading={props.deleteLoading} onclick={props.handleDelete} class="Btn" noIcon="d-none" value="Confirm" color="primary" />
                    </Box>
                </div>
            </div>
        </ModalBox>
    )
}
