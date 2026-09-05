import { ModalBox } from "../../commonComponents/Modals"
import { AppButton } from "../../commonComponents/parts"

export function CEditDeleteModal(props) {
    return (
        <ModalBox title={''} open={props.open} handleClose={props.modalClose} onClose={props.modalClose}>
            <div className="px-4 project-delete">
                <div className="pb-2 f20x">Delete selected content plans?</div>
                <div>This action also removes the saved article for each plan.</div>

                <div className="pb-4 d-flex flex-wrap justify-content-end">
                    <div className="addButton pt-3 m-r15 min-w-[100px] max-w-[150px] flex-[0_0_auto] text-ink-3">
                        <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn" noIcon="d-none"></AppButton>
                    </div>
                    <div className="addButton pt-3 min-w-[100px] max-w-[150px] flex-[0_0_auto]">
                        <AppButton loading={props.deleteLoading} onclick={props.handleDelete} class="Btn" noIcon="d-none" value="Confirm" color="primary" />
                    </div>
                </div>
            </div>
        </ModalBox>
    )
}