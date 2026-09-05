import { Grid, } from "@mui/material";
import React, { useEffect, useState } from "react";
import Pie from "./common/common";

function OverallPageScore(props) {
    const styles = {
        overview_score_text: {
            "font-size": "16px",
            "line-height": "24px"
        },
    };
    let [score, setScore] = useState(0)

    useEffect(() => {
        setScore(props.score)
    }, [props.score]);

    return (
        <>
            <div className="mt-2">
                {
                    score &&
                        (score >= 70) ?
                        <Pie serpscore={score} yserpscore={100} text="Good !" firstcolor={"#B9ED9F"} secondcolor={"#43CF62"} /> :
                        (score < 30 && score > 0) ? <Pie serpscore={score} yserpscore={100} text="Bad !" firstcolor={"#ECB8B8"} secondcolor={"#CF4343"} />
                            : (score >= 30 && score < 70) ? <Pie serpscore={score} yserpscore={100} text="Okay !" firstcolor={"#FFDEAA"} secondcolor={"#e5a34f"} />
                                : <Pie serpscore={score} yserpscore={100} text="" firstcolor={"#ffffff"} secondcolor={"#ffffff"} />
                }
            </div>
        </>
    )
}
export default OverallPageScore;