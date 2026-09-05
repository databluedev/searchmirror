import { useState, useEffect } from "react";
import axios from "axios";
import { ModalBox } from "../../commonComponents/Modals";
import { AppButton } from "../../commonComponents/parts";

export function useFetch({ url, data, usertoken, trigger, setTrigger }) {
    const [loader, setLoader] = useState(false);
    const [resData, setData] = useState([]);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            if (!trigger) return; // Wait until 'trigger' is set to true
            setLoader(true);
            try {
                const response = await axios.post(url, data, {
                    headers: { 'Authorization': 'Token ' + usertoken }
                });
                if (response.data.st === 1) {
                    setData(response.data.dt);
                }
            } catch (err) {
                setError(err);
            } finally {
                setLoader(false);
            }
            setTrigger(false)
        };

        fetchData();
    }, [url, data, usertoken, trigger]); // Depend on 'trigger'

    return { resData, loader, error };
}

export function ConfirmDeleteModal(props) {
    return (
    <ModalBox title={''} open={props.open} handleClose={props.modalClose} onClose={props.modalClose}>
        <div className="px-4 project-delete">
            <div className="pb-2 f20x">{props.mnhdr}</div>
            <div>{props.subhdr}</div>

            <div className="pb-4 d-flex flex-wrap justify-content-end">
                <div
                    className="addButton pt-3 m-r15 min-w-[100px] max-w-[150px] flex-none text-ink-3"
                >
                    <AppButton value="Cancel" onclick={props.modalClose} color="white" class="Btn" noIcon="d-none"></AppButton>
                </div>
                <div
                    className="addButton pt-3 min-w-[100px] max-w-[150px] flex-none"
                >
                    <AppButton loading={props.delLoad} onclick={props.onSubmit} class="Btn" noIcon="d-none" value="Confirm" color="primary" />
                </div>
            </div>
        </div>
    </ModalBox>
    )
}
