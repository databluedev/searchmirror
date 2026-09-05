import React, { useState } from "react"
import { WithContext as ReactTags } from 'react-tag-input';
import { CloseIcon } from "../icons";
import { toast } from "react-toastify";

function LLMPrompts(props) {

    const separators = [",", "Enter"];

    const addPrompt = (prompt) => {
        let keyword = prompt.text.trim()
        if (keyword === "") {
            showToast("error", "Enter your prompts")
            return false;
        }
        else if (props.prompts.includes(keyword)) {
            showToast("error", "Prompt is already added")
            return false;
        }
        else if (props.prompts.length === 10) {
            showToast("error", "Maximum 10 prompts only allowed")
            return false;
        }
        else {
            let newPrompts = [keyword, ...props.prompts]
            props.handlePrompts(newPrompts)
        }
    }

    const handleDelete = (keyword) => {
        let newPrompts = [...props.prompts.filter((eachKeyword, index) => eachKeyword !== keyword)];
        props.handlePrompts(newPrompts)
    };


    const showToast = (type, message) => {
        toast.dismiss()
        if (type === "success") {
            toast.success(message)
        } else {
            toast.error(message)
        }
    }

    return (
        <div className="tags-input keyword">
            <div className="tag-input-box">
                <ReactTags
                    separators={separators}
                    handleAddition={addPrompt}
                    allowDeleteFromEmptyInput={false}
                    allowAdditionFromPaste={false}
                    allowUnique={false}
                    allowDragDrop={false}
                    maxLength={2048}
                    inputFieldPosition="top"
                    placeholder="Enter your prompts"
                />

                <ul className="m-t20">
                    {props.prompts.map((eachKeyword, index) => (
                        <li className="bgPrimaryClr" key={index}>
                            <span>{eachKeyword}</span>
                            <span className="close" onClick={() => handleDelete(eachKeyword)}>
                                <CloseIcon color="#ffffff" />
                            </span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    )
}
export default LLMPrompts
