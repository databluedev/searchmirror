import React, { useEffect, useState } from "react";
import { useHistory, useParams, useLocation } from "react-router-dom";
import "../llmTracker/style.scss";
import Cookies from 'universal-cookie';
import axios from 'axios';
import { Tooltip, Zoom } from "@mui/material";
import { BacklinkIcon } from '../commonComponents/icons';
import { Title, Para, AppIconButton } from '../commonComponents/parts';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import PageSkeleton, { Bone } from "../commonComponents/page_skeleton";

// The providers answer in markdown and there is no markdown dependency in the
// app, so the answer -- the whole point of this page -- used to render with its
// literal "**", "###" and "*" markers in the reader's face. This renders the
// small subset the providers actually emit as React nodes. Nothing reaches
// dangerouslySetInnerHTML: the text is provider output and stays text.
const inlineNodes = (text, keyPrefix) => {
    const out = [];
    const re = /(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`)/g;
    let last = 0;
    let match;
    let i = 0;
    while ((match = re.exec(text)) !== null) {
        if (match.index > last) out.push(text.slice(last, match.index));
        const tok = match[0];
        const key = keyPrefix + "-" + (i += 1);
        if (tok.startsWith("**")) out.push(<strong key={key} className="answerStrong">{tok.slice(2, -2)}</strong>);
        else if (tok.startsWith("`")) out.push(<code key={key} className="answerCode">{tok.slice(1, -1)}</code>);
        else out.push(<em key={key}>{tok.slice(1, -1)}</em>);
        last = match.index + tok.length;
    }
    if (last < text.length) out.push(text.slice(last));
    return out;
};

function AnswerBody({ text }) {
    const blocks = [];
    let para = [];
    let list = null;
    const flushPara = () => { if (para.length) { blocks.push({ t: "p", v: para.join(" ") }); para = []; } };
    const flushList = () => { if (list) { blocks.push(list); list = null; } };

    String(text || "").split("\n").forEach((raw) => {
        const line = raw.trim();
        if (!line) { flushPara(); flushList(); return; }

        const heading = /^(#{1,6})\s+(.*)$/.exec(line);
        if (heading) { flushPara(); flushList(); blocks.push({ t: "h", v: heading[2] }); return; }

        if (/^(\*\*\*|---|___)$/.test(line)) { flushPara(); flushList(); blocks.push({ t: "hr" }); return; }

        // "* item" is a bullet; "**Bold**" is not -- the space is what separates
        // them, so the marker has to be followed by whitespace.
        const bullet = /^[*-]\s+(.*)$/.exec(line);
        const numbered = /^\d+[.)]\s+(.*)$/.exec(line);
        if (bullet || numbered) {
            flushPara();
            const ordered = !!numbered;
            if (!list || list.ordered !== ordered) { flushList(); list = { t: "list", ordered, items: [] }; }
            list.items.push((bullet || numbered)[1]);
            return;
        }

        flushList();
        para.push(line);
    });
    flushPara();
    flushList();

    return (
        <div className="answerBody">
            {blocks.map((b, i) => {
                if (b.t === "h") return <h4 key={i} className="answerHeading">{inlineNodes(b.v, "h" + i)}</h4>;
                if (b.t === "hr") return <hr key={i} className="answerRule" />;
                if (b.t === "list") {
                    const Tag = b.ordered ? "ol" : "ul";
                    return (
                        <Tag key={i} className="answerList">
                            {b.items.map((item, j) => <li key={j}>{inlineNodes(item, i + "-" + j)}</li>)}
                        </Tag>
                    );
                }
                return <p key={i} className="answerPara">{inlineNodes(b.v, "p" + i)}</p>;
            })}
        </div>
    );
}

function CitationsPage(props) {
    const history = useHistory();
    const { id } = useParams(); // Route parameter is 'id', not 'analytics_id'
    const location = useLocation();
    const [citationsData, setCitationsData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [showFull, setShowFull] = useState(false);


    // Get model type from URL query params
    const queryParams = new URLSearchParams(location.search);
    const modelType = queryParams.get('model') || 'total';

    // Every model that answered this prompt, handed over by the table row that
    // opened the page. The row knows all four analytics ids; this page's own
    // payload describes one model only, so without them the other answers are
    // unreachable and the reader is not told they exist. Absent on a direct
    // URL visit, which is why nothing here depends on it.
    const siblings = (location.state && Array.isArray(location.state.models)) ? location.state.models : [];

    useEffect(() => {
        if (id) {
            fetchCitationsData();
        } else {
            setError('Analytics ID not provided');
            setLoading(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [id]);

    const fetchCitationsData = async () => {
        setLoading(true);
        setError(null);
        setShowFull(false);

        try {
            const cookies = new Cookies();
            const usertoken = cookies.get('session_token');
            const userid = cookies.get('session_userid');
            const grpid = cookies.get('activegrp');
            if (!grpid) { return; }   // no project: nothing to ask about

            if (!usertoken || !userid) {
                history.push("/login");
                return;
            }

            const requestData = {
                userid: userid,
                groupid: grpid,
                analytics_id: id,
                model: modelType // Include model type in the request
            };


            const response = await axios.post(global.apiurl + '/llmtracker/citations', requestData, {
                headers: { 'Authorization': 'Token ' + usertoken }
            });


            if (response.data && response.data.status === "true") {
                setCitationsData(response.data.data);
            } else {
                setError(response.data.message || 'Failed to fetch citations data');
            }
        } catch (error) {
            console.error('Error fetching citations:', error);
            setError('Failed to fetch citations data');
        } finally {
            setLoading(false);
        }
    };

    const handleBackClick = () => {
        history.goBack();
    };

    // Which tab is current is a question about the MODEL, not the row id -- the
    // ?model= param is what the fetch is keyed on, so it is what decides.
    const isCurrentModel = (sib) =>
        (modelType && modelType !== "total") ? sib.key === modelType : sib.analyticsId === id;

    const openModel = (sib) => {
        if (!sib || !sib.analyticsId || isCurrentModel(sib)) return;
        history.replace(`/prompt/citations/${sib.analyticsId}?model=${sib.key}`, { models: siblings });
    };

    // docs/DESIGN.md, "Loading": the shape of this page never varies -- header,
    // the model tab strip, the answer card, the rival-brands card -- so the wait
    // is drawn as that shape rather than as a bar on a blank h100vh with the
    // word "Loading" under it.
    if (loading) {
        return (
            <PageSkeleton label="Loading this answer" className="kr_layout">
                <Bone height="34px" width="320px" />
                <Bone height="360px" />
                <Bone height="160px" />
            </PageSkeleton>
        );
    }

    // Both of these were hand-rolled Bootstrap: a heading painted with
    // Bootstrap's danger utility -- the last such use in app/src/pages, and a
    // red _tokens.scss does not define -- over an ad-hoc flex column. They are
    // the house .emptyState block now (docs/DESIGN.md: micro-label, one
    // sentence, one action), the same one the dashboard's states use.
    if (error) {
        return (
            <div className="emptyState h100vh">
                <p className="emptyState__label">Answer unavailable</p>
                <p className="emptyState__body">{error}</p>
                <div className="emptyState__action">
                    <Button variant="secondary" onClick={handleBackClick}>
                        Go back
                    </Button>
                </div>
            </div>
        );
    }

    if (!citationsData) {
        return (
            <div className="emptyState h100vh">
                <p className="emptyState__label">No answer stored</p>
                <p className="emptyState__body">
                    This prompt has no stored answer for the selected model, so there is nothing to read here yet.
                </p>
                <div className="emptyState__action">
                    <Button variant="secondary" onClick={handleBackClick}>
                        Go back
                    </Button>
                </div>
            </div>
        );
    }

    const model = citationsData.model || "This model";

    // The rival brands this one answer named, from the brand extraction in
    // backend/llmtracker/brands.py -- NOT from `citations`, which this panel
    // used to read. See the block above the panel for why that field could not
    // answer the question the panel asks.
    //
    // `brands_scored` is the whole point of the payload carrying three fields
    // rather than one. An empty list means one of two opposite things -- the
    // answer named no tracked rival, or nothing has ever scanned it -- and the
    // panel must not render those identically.
    //
    // The API sends `true` or `null`, never `false`: a row exists for this
    // answer or it does not, and "no row" cannot distinguish "never scanned"
    // from "no rivals to scan for". So `=== true` is the only safe read, and
    // the no-rivals case is decided by `brands_tracked` before this is
    // consulted at all.
    const brands = Array.isArray(citationsData.brands_named) ? citationsData.brands_named : [];
    const brandsScored = citationsData.brands_scored === true;
    const brandsTracked = Number(citationsData.brands_tracked) || 0;

    return (
        <section className="layout kr_layout">
            <header>
                <div className="d-flex justify-content-between flex-wrap gap-3">
                    <div className="d-flex flex-wrap gap-3 align-items-center">
                        <span>
                            <AppIconButton
                                Icon={<BacklinkIcon />}
                                onclick={handleBackClick}
                            />
                        </span>
                        <div>
                            {/* The page is the model's answer, not a list of
                                links -- the old "Citations for X" title named
                                the smallest and least reliable thing on it. */}
                            <Title class="wd-title">{model}&rsquo;s answer</Title>
                            <Para class="wd-subTitle m-b0 d-flex align-items-center lh14x">What this model said, and whether it named your brand</Para>
                        </div>
                    </div>
                </div>
            </header>
            <div className="container-fluid">
                {/* One prompt can have an answer from every configured model.
                    Opening the row picked one of them silently; these make the
                    others visible and reachable. */}
                {siblings.length > 1 ? (
                    <div className="answerModelTabs" role="tablist" aria-label="Models that answered this prompt">
                        {siblings.map((sib) => (
                            <button
                                key={sib.key}
                                type="button"
                                role="tab"
                                aria-selected={isCurrentModel(sib)}
                                className={"answerModelTab" + (isCurrentModel(sib) ? " is-active" : "")}
                                onClick={() => openModel(sib)}
                            >
                                {sib.label}
                                {sib.mentioned ? <span className="answerModelTabDot" aria-hidden="true" /> : null}
                            </button>
                        ))}
                    </div>
                ) : null}

                <div className="row mb-4">
                    <div className="col-12">
                        <Card className="p-4">
                            {citationsData.prompt ? (
                                <p className="text-[13px] text-ink-3 mb-2">Prompt: <span className="text-ink">{citationsData.prompt}</span></p>
                            ) : null}
                            <div className="flex items-center flex-wrap gap-3 mb-2">
                                <Badge variant={citationsData.is_mention ? "up" : "default"}>
                                    {citationsData.is_mention ? `Mentioned${citationsData.mention_count ? " ×" + citationsData.mention_count : ""}` : "Not mentioned"}
                                </Badge>
                                {/* Sentiment is a lexicon score over the WHOLE answer, and it is
                                    stored for every row whether or not the brand appears. Rendering
                                    it unconditionally put a green "Positive" beside "Not mentioned"
                                    on five of this project's eight prompts -- the score was the
                                    model's enthusiasm for a competitor, read by the user as regard
                                    for them. It only says anything about the brand when the brand
                                    is in the answer, so it only renders then, and the label says
                                    whose tone it is. */}
                                {(citationsData.is_mention && citationsData.sentiment) ? (
                                    <Tooltip
                                        classes={{ tooltip: "Tltpsmall text-center" }}
                                        placement="top"
                                        TransitionComponent={Zoom}
                                        title="Tone of the whole answer, scored by a general-purpose lexicon. It is not a judgement of how your brand was described."
                                    >
                                        <span className="d-inline-flex">
                                            {/* Only a hostile answer gets colour: green here would be a
                                                third green pill on a row where the mention badge is the
                                                claim worth reading, and the design contract reserves
                                                green and red for direction. */}
                                            <Badge variant={citationsData.sentiment === "negative" ? "down" : "default"}>
                                                Answer tone: {citationsData.sentiment}
                                            </Badge>
                                        </span>
                                    </Tooltip>
                                ) : null}
                                {/* position_score is 1 − (offset of the first mention / answer
                                    length): an inverted relative offset, not a share or a
                                    confidence. Printed as "High (100%)" it invited both readings.
                                    Say where in the answer the brand first appears instead. */}
                                {(citationsData.is_mention && typeof citationsData.position_score === "number") ? (() => {
                                    const offset = Math.round((1 - Math.max(0, Math.min(1, citationsData.position_score))) * 100);
                                    const where = offset <= 20 ? "in the opening" : offset <= 60 ? "mid-answer" : "near the end";
                                    return (
                                        <Tooltip
                                            classes={{ tooltip: "Tltpsmall text-center" }}
                                            placement="top"
                                            TransitionComponent={Zoom}
                                            title={`Your brand first appears about ${offset}% of the way into this answer.`}
                                        >
                                            <span className="d-inline-flex">
                                                <Badge variant="default">Named {where}</Badge>
                                            </span>
                                        </Tooltip>
                                    );
                                })() : null}
                            </div>
                            <p className="text-[13px] text-ink-3 mb-3">
                                {citationsData.is_mention
                                    ? `Your brand was named ${citationsData.mention_count || 1} time${(citationsData.mention_count || 1) > 1 ? "s" : ""} in ${model}'s answer.`
                                    : `${model} did not name your brand in its answer.`}
                            </p>
                            {(() => {
                                const full = citationsData.response_text || citationsData.context_summary || "";
                                if (!full) {
                                    return <p className="mb-0 text-ink-3 text-[13px]">The answer text was not stored for this run.</p>;
                                }
                                const isLong = full.length > 900;
                                const shown = showFull || !isLong ? full : full.slice(0, 900).trimEnd() + "…";
                                return (
                                    <>
                                        <AnswerBody text={shown} />
                                        {/* This was a ghost Button stripped of its chrome and
                                            forced to --accent, which rendered as a bare blue
                                            link -- a control the app has nowhere else, and one
                                            that spends the "act on this" colour on a disclosure
                                            toggle. It is the house secondary pill now, the same
                                            control as .answerModelTab directly above it. */}
                                        {isLong ? (
                                            <Button
                                                type="button"
                                                variant="secondary"
                                                size="sm"
                                                className="mt-3"
                                                aria-expanded={showFull}
                                                onClick={() => setShowFull((v) => !v)}
                                            >
                                                {showFull ? "Show less" : "Show full answer"}
                                            </Button>
                                        ) : null}
                                    </>
                                );
                            })()}
                        </Card>
                    </div>
                </div>

                {/* This panel read `citations` and was titled "Domains named in
                    this answer". `citations` is the domain-shaped-substring
                    array the audit retired: it matches any token in the prose
                    that happens to carry a dot and a valid TLD, which for an
                    ungrounded model is close to nothing. Across all eight of
                    this project's stored answers it holds exactly one value,
                    `searchapi.io`, scraped out of the heading
                    "### 6. **SearchApi.io**" -- a competitor's brand name, not
                    a source, and not even one the brand extractor tracks.

                    So the panel was empty on 7 of 8 answers and wrong on the
                    8th. On the answer it called empty, the model had named
                    fourteen rivals -- Playwright, Puppeteer, Crawlee, Scrapy,
                    Zyte, Apify, Bright Data among them -- printed in full in
                    the card directly above this one. A reader comparing the two
                    would conclude the product cannot see what is in front of it,
                    and they would be right.

                    It reads the brand extraction now (backend/llmtracker/
                    brands.py), which counts a name however it is written --
                    "Bright Data" has no dot and could never appear before. The
                    heading says brands because brands is what is counted; these
                    answers contain no URLs, so nothing here was ever cited or
                    linked and the panel no longer implies it was. */}
                <div className="row">
                    <div className="col-12">
                        <Card>
                            <CardHeader>
                                <CardTitle>Rival brands named in this answer</CardTitle>
                                <CardDescription className="text-[12px] mb-0">
                                    {brandsTracked === 0 ? (
                                        // Checked FIRST, and not behind `brandsScored`: with no
                                        // rivals to score against, the scorer writes no rows, so
                                        // `brands_scored` is null here and always will be. What is
                                        // missing is the rival list, not the measurement, and
                                        // "named none of the 0 rivals tracked" is true and useless.
                                        <>
                                            No rivals are tracked for this project yet, so there was nothing to look
                                            for in this answer. Add the brands you compete with and every stored
                                            answer is re-counted for them — no model is called again.
                                        </>
                                    ) : !brandsScored ? (
                                        // NOT the same sentence as "none named", and deliberately
                                        // so: an unscanned answer is missing evidence, not evidence
                                        // of absence. Rendering the two alike is the defect this
                                        // panel is being fixed for.
                                        <>
                                            This answer has not been scanned for rival brands yet, so nothing below is
                                            a measurement — an empty list here would mean we did not look, not that
                                            {" "}{model} named nobody.
                                        </>
                                    ) : brands.length > 0 ? (
                                        <>
                                            {model} named {brands.length} of the {brandsTracked} rival
                                            {brandsTracked === 1 ? "" : "s"} tracked for this project, counted in its own
                                            wording. The number beside each is how many times it appears in this one
                                            answer — it is a count, not a share of anything.
                                        </>
                                    ) : (
                                        <>
                                            {model} named none of the {brandsTracked} rival
                                            {brandsTracked === 1 ? "" : "s"} tracked for this project in this answer.
                                            This answer was scanned: the list is empty because nothing matched.
                                        </>
                                    )}
                                </CardDescription>
                            </CardHeader>
                            {brandsScored && brands.length > 0 ? (
                                <CardContent>
                                    <div className="answerBrandList">
                                        {brands.map((brand, index) => (
                                            <div key={brand.name || index} className="answerBrand">
                                                <span className="answerBrandName">{brand.name}</span>
                                                <span className="answerBrandCount">
                                                    &times;{Number(brand.mentions) || 0}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            ) : null}
                        </Card>
                    </div>
                </div>
            </div>
        </section>
    );
}

export default CitationsPage;
