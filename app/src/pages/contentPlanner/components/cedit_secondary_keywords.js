import React, { useState } from "react"
import { WithContext as ReactTags } from 'react-tag-input';
import { CloseIcon } from "../../commonComponents/icons";
import { toast } from "react-toastify";

function CEditSecondaryKeywords(props) {

    const separators = [",", "Enter"];

    const addSecondaryKeywords = (primaryKeyword) => {
        let keyword = primaryKeyword.text.trim()
        if (keyword === "") {
            showToast("error", "Enter your secondary keywords")
            return false;
        } else if (keyword === props.primaryKeyword) {
            showToast("error", "Secondary Keyword must not match your primary keyword.")
            return false;
        }
        else if (props.secondaryKeywords.includes(keyword)) {
            showToast("error", "Secondary Keyword is already added")
            return false;
        }
        else if (props.secondaryKeywords.length === 10) {
            showToast("error", "Maximum 10 keywords only allowed")
            return false;
        }
        else {
            let newSecondaryKeywords = [keyword, ...props.secondaryKeywords]
            props.handleSecondaryKeywords(newSecondaryKeywords)
        }
    }

    const handleDelete = (keyword) => {
        let newSecondaryKeywords = [...props.secondaryKeywords.filter((eachKeyword, index) => eachKeyword !== keyword)];
        props.handleSecondaryKeywords(newSecondaryKeywords)
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
                    handleAddition={addSecondaryKeywords}
                    allowDeleteFromEmptyInput={false}
                    allowAdditionFromPaste={false}
                    allowUnique={false}
                    allowDragDrop={false}
                    maxLength={2048}
                    inputFieldPosition="top"
                    placeholder="Secondary Keywords"
                />

                <ul className="m-t20">
                    {props.secondaryKeywords.map((eachKeyword, index) => (
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
export default CEditSecondaryKeywords
