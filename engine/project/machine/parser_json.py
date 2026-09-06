from django.shortcuts import render
from django.conf import settings

from rest_framework_mongoengine import viewsets as meviewsets

from project.machine.models import BrandTracker, Keyword, Group, ManualRefresh, Mainsettings

import requests, json, time, csv
from bs4 import BeautifulSoup
from urllib import parse
import sys, os, random
from datetime import datetime, date

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse

from urllib.parse import urlparse
from threading import Timer

from project.machine import watchdog, formulate, centralised, encryption
from project.machine import automation_common as _at__common_

from unidecode import unidecode as _u__dcode_
import re



def __distinct_pages__(links):
	"""The pages that cannibalise a keyword, each counted once.

	Cannibalisation is more than one page of YOUR OWN site ranking for one
	keyword, so they compete with each other. The collector above appends every
	matching result, and the same URL can arrive more than once -- as an organic
	result and again as a sitelink or a variant. Counting the raw list therefore
	flagged a single page as cannibalising itself: seen in production on
	2026-09-06, where one keyword carried the identical URL twice and the
	keywords table told the owner to "fix cannibalization issues" for a page that
	has no competitor.

	Order is preserved -- it is the order the pages ranked in, which is the order
	someone reading the list expects.
	"""
	seen = list(dict.fromkeys(link for link in (links or []) if link))
	return seen if len(seen) > 1 else []

def trim(value):
    return value.strip()


def strip_www(host):
    """Drop a leading www. label from a host.

    Anchored to the front on purpose. A plain .replace("www.", "") deletes the
    substring wherever it appears, which mangles hosts that merely contain it
    ("wwww.com" -> "wcom") and is the only reason two spellings of the same
    domain could ever compare unequal here.
    """
    host = str(host or "").strip().lower()
    return host[4:] if host.startswith("www.") else host


def extract_domain(url, remove_http=True):
    uri = urlparse(url)
    if remove_http:
        if uri.netloc:
            domain_name = strip_www(uri.netloc)
        else:
            domainDivision = f"{uri.path}".split("/")
            domain_name = strip_www(domainDivision[0]) if len(domainDivision) > 0 else domainDivision
    else:
        domain_name = strip_www(uri.netloc)

    return domain_name


def exact_url_scheme(url):
    """Normalise a URL for exact-page comparison: no scheme, no www., no trailing slash.

    www. has to go here too. Without it a target entered as
    "https://example.com/pricing" never matched the SERP's
    "https://www.example.com/pricing", so every exactdomain keyword on a
    www-canonical site was silently recorded as not ranking -- a false
    negative that is written to the rank history as a real measurement.
    """
    parsed = urlparse(url)

    remainder = parsed.geturl()
    if parsed.scheme:
        remainder = remainder.replace("%s://" % parsed.scheme, "", 1)

    # Only the host is normalised. Paths are case-sensitive and must survive
    # byte for byte; a trailing slash is the one difference forgiven there.
    host, slash, path = remainder.partition("/")
    return (strip_www(host) + slash + path).rstrip("/")


def domain_competitors(domains, rank, per_list):
    top = before = after = list()

    if len(domains):
        top = domains[:per_list]
        kw_rank = rank
        if rank:
            rank = rank if rank < 1 else rank - 1
            domain_key_min = 0 if kw_rank < per_list else (rank - per_list) + 1
            if kw_rank >= 1:
                before = domains[domain_key_min:kw_rank]

            after = domains[rank : (rank + per_list)]

    compValue = {"tp": top, "bf": before, "ar": after}
    return compValue


def get_cite(citeBlock):
    citeLink = []
    try:
        if citeBlock and trim(citeBlock):
            citeLink = [trim(citeBlock)]
    except Exception as e:
        pass
    return citeLink


def get_title(titleBlock):
    try:
        return trim(titleBlock) if titleBlock and trim(titleBlock) else ""
    except Exception as e:
        pass

    return ""


def get_desc():
    return []


def extract_rating_from_snippet(text):
    try:
        match = re.search(r"Rating\s+(\d(?:\.\d)?)", text)
        if match:
            return match.group(1)
        return "0"
    except Exception as e:
        print(f"Error: {e}")
        return "0"


# ── SERP FEATURE BLOCKS ──────────────────────────────────────────────────────
# DataBlue returns every non-organic block as its own top-level key, and Lite
# mode (advanced=false) already carries ads, featured_snippet, people_also_ask,
# local_results, knowledge_panel, videos and related_searches.  None of them
# were ever read here.  That is the whole reason Keyword.featured_snippet,
# .knowledge_panel and .ads have been False on every row since the JSON
# provider replaced the HTML scraper, and why Competitors renders
# "Feature Snippet 0 - Ads 0 - Review 0" no matter what Google returned.
#
# Three states are kept apart on purpose, because collapsing them is what makes
# "never looked" indistinguishable from "looked and found none":
#     present     - the block came back carrying content
#     absent      - this mode returns the block and it held nothing; count is a
#                   real measured 0
#     unavailable - this mode does not return the block at all; count is None,
#                   never 0, because nothing was counted
# A keyword whose serp_features is {} was never measured by this parser at all.
# Nothing downstream may read a missing block as a zero.

_LITE_FEATURE_BLOCKS_ = (
    "featured_snippet",
    "ads",
    "people_also_ask",
    "local_results",
    "knowledge_panel",
    "videos",
    "related_searches",
)

# Legacy snippets_details token per block.  These keys are not invented here:
# backend/serp/serializers.py already renders them as badges and
# keywordhistory.py already reads featured_box/ads.  The contract has been in
# place all along with nothing writing to it.
_FEATURE_SNIPPET_TOKENS_ = {
    "people_also_ask": "rqrs",
    "videos": "vdrs",
    "local_results": "lcrs",
}

# Field naming varies per block (an ad has url/displayed_url, an organic row has
# link/displayed_link, a PAA row has question/snippet), so every read goes
# through a candidate list rather than assuming one spelling.
# Verified against the raw responses on disk rather than against documentation.
# Field names observed there, per block:
#   ads               position title url displayed_url snippet
#   featured_snippet  title url content type
#   related_searches  query url
#   videos            title url
#   organic_results   position title url displayed_url snippet rank link displayed_link
#
# Two of those were being dropped. "query" is the ONLY readable text a related
# search carries -- without it an entry kept nothing but a google.<tld>
# redirect URL, so the block could be counted and never read. "content" is the
# featured snippet's actual answer text, which is the whole reason to look at
# a featured snippet at all.
_FEATURE_LINK_FIELDS_ = ("link", "url", "displayed_link", "displayed_url", "source_url", "website")
_FEATURE_TITLE_FIELDS_ = ("title", "question", "name", "heading", "query")
_FEATURE_DESC_FIELDS_ = ("snippet", "description", "answer", "desc", "text", "content")
_FEATURE_SLOT_FIELDS_ = ("block_position", "position_type", "placement", "slot")


def _feature_field(item, names):
    """First non-empty string among `names`, or ""."""
    if not isinstance(item, dict):
        return ""
    for name in names:
        value = item.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _feature_items(block):
    """Normalise a block to a list of dicts; an object becomes a one-item list."""
    if isinstance(block, list):
        return [item for item in block if isinstance(item, dict)]
    if isinstance(block, dict):
        return [block]
    return []


def _feature_entry(feature, item, targetLink, fallbackPosition):
    """One labelled row out of a feature block.

    "feature" rides on every row deliberately.  A feature block carries its own
    position and an ad at position 1 is not rank 1.  Nothing here touches
    postdata["rank"] or the `domains` competitor ladder -- those stay built from
    organic_results alone -- and the label is what keeps a later reader from
    merging the two by accident.
    """
    link = _feature_field(item, _FEATURE_LINK_FIELDS_)
    domain = extract_domain(link) if link else ""

    try:
        position = int(item.get("position") or fallbackPosition)
    except Exception:
        position = fallbackPosition

    return {
        "feature": feature,
        "position": position,
        "slot": (_feature_field(item, _FEATURE_SLOT_FIELDS_) or "unknown").lower(),
        "link": link,
        "domain": domain,
        "title": _feature_field(item, _FEATURE_TITLE_FIELDS_),
        "desc": _feature_field(item, _FEATURE_DESC_FIELDS_),
        "owned": bool(domain) and domain == targetLink,
    }


def _response_depth(bsoup, requestedAdvanced=None):
    """Which depth actually produced this response: "lite", "advanced", "unknown".

    The provider echoes what it ran under search_parameters.advanced, and that
    is what was measured as opposed to what was asked for, so it is read first.
    "unknown" is a real answer and is treated as "we cannot claim ai_overview
    was looked for" -- never as Lite, which would record an unrequested block
    as a measured absence.
    """
    params = bsoup.get("search_parameters") if isinstance(bsoup, dict) else None
    advanced = params.get("advanced") if isinstance(params, dict) else None
    if advanced is None:
        advanced = requestedAdvanced
    if advanced is None:
        return "unknown"
    return "advanced" if bool(advanced) else "lite"


def extract_serp_features(bsoup, targetLink, requestedAdvanced=None):
    """Read every non-organic block out of one DataBlue response.

    Returns (features, snippetDetails, snippetTokens):
        features       -> Keyword.serp_features, the honest tri-state record
        snippetDetails -> Keyword.snippets_details, the legacy shape that
                          keywordhistory.py and the serp serializers read
        snippetTokens  -> the SNIPPETS list centralised.mongopush turns into the
                          featured_snippet / knowledge_panel / ads booleans
    """
    depth = _response_depth(bsoup, requestedAdvanced)
    features = {
        "source": "datablue",
        "mode": depth,
        "target": targetLink,
        "measured_at": str(datetime.now()),
        "blocks": {},
    }
    snippetDetails = {}

    if not isinstance(bsoup, dict):
        return features, snippetDetails, []

    for feature in _LITE_FEATURE_BLOCKS_:
        # The provider omits null fields, so a key that never arrived is weaker
        # evidence than a key that arrived empty.  Both are absences, and
        # `reported` is what tells them apart without pretending either is a
        # measurement it is not.
        reported = feature in bsoup
        rawItems = _feature_items(bsoup.get(feature))
        if feature == "featured_snippet":
            # DataBlue reuses this slot for the AI Overview and marks it
            # type="ai_overview". Counting it here would report an AI answer as
            # a won featured snippet.
            rawItems = [
                item for item in rawItems
                if str(item.get("type") or "").strip().lower() != "ai_overview"
            ]
        entries = [
            _feature_entry(feature, item, targetLink, index + 1)
            for index, item in enumerate(rawItems)
        ]
        owned = any(entry["owned"] for entry in entries)

        record = {
            "state": "present" if entries else "absent",
            "count": len(entries),
            "reported": reported,
            "owned": owned,
            # Capped: this is a summary written to every keyword every day, not
            # an archive.  The raw response is already on disk.
            "items": entries[:10],
        }

        if feature == "ads":
            topAds = [entry for entry in entries if entry["slot"] == "top"]
            bottomAds = [entry for entry in entries if entry["slot"] == "bottom"]
            unknownAds = [entry for entry in entries if entry["slot"] not in ("top", "bottom")]
            # DataBlue's ad rows carry a position but no placement, so the
            # above/below-the-fold split is usually not measurable.  Unplaced
            # ads are counted on their own rather than folded into top_count,
            # which would publish a guess as a measurement.
            record["top_count"] = len(topAds)
            record["bottom_count"] = len(bottomAds)
            record["unknown_slot_count"] = len(unknownAds)

            if entries:
                snippetDetails["ads"] = {
                    "status": "yes" if owned else "no",
                    "top_result": [{"link": e["link"], "title": e["title"]} for e in topAds],
                    "bottom_result": [{"link": e["link"], "title": e["title"]} for e in bottomAds],
                    "unknown_result": [{"link": e["link"], "title": e["title"]} for e in unknownAds],
                    "top_count": len(topAds),
                    "bottom_count": len(bottomAds),
                    "present": "top" if topAds else ("bottom" if bottomAds else "yes"),
                }

        elif feature == "featured_snippet":
            if entries:
                box = entries[0]
                # keywordhistory.snippetsHistory dereferences link/title/desc
                # and status without guarding, so all four are always written.
                snippetDetails["featured_box"] = {
                    "status": "yes" if box["owned"] else "no",
                    "link": box["link"],
                    "title": box["title"],
                    "desc": box["desc"],
                    "cite": box["domain"],
                    "img": "",
                }

        elif feature == "knowledge_panel":
            if entries:
                snippetDetails["knowledge_box"] = {"present": "yes"}

        elif entries and feature in _FEATURE_SNIPPET_TOKENS_:
            snippetDetails[_FEATURE_SNIPPET_TOKENS_[feature]] = "yes"

        features["blocks"][feature] = record

    # AI OVERVIEW -- only returned when advanced=true (docs.datablue.dev/google-serp).
    # Under Lite it was never requested, so it is "unavailable" with a null
    # count.  Recording it as an absent 0 would claim a measurement that was
    # never paid for.  Nothing renders this yet; it is stored so the GEO half of
    # the product has the answer text and its cited sources.
    aiBlock = bsoup.get("ai_overview") if depth == "advanced" else None
    if depth != "advanced":
        features["ai_overview"] = {
            "state": "unavailable",
            "count": None,
            "reported": False,
            "owned": None,
        }
    else:
        # The block is {"content": str, "sources": [{"title", "url"}]}, so the
        # cited sites are one level down; reading the block itself yields no
        # link and would report owned=False for every keyword.
        aiSources = aiBlock.get("sources") if isinstance(aiBlock, dict) else None
        aiPresent = isinstance(aiBlock, dict) and bool(
            aiBlock.get("content") or aiBlock.get("sources")
        )
        aiEntries = [
            _feature_entry("ai_overview", item, targetLink, index + 1)
            for index, item in enumerate(_feature_items(aiSources))
        ]
        features["ai_overview"] = {
            "state": "present" if aiPresent else "absent",
            "count": len(aiEntries),
            "reported": "ai_overview" in bsoup,
            "owned": any(entry["owned"] for entry in aiEntries),
            "sources": [
                {"domain": e["domain"], "link": e["link"], "title": e["title"]}
                for e in aiEntries
                if e["domain"]
            ],
            # Verbatim provider block. The shape is undocumented, so it is
            # stored as sent rather than flattened into fields that may not
            # exist.
            "raw": aiBlock,
        }

    return features, snippetDetails, list(snippetDetails.keys())


# ── JSON RANK PARSER ─────────────────────────────────────────────────────────
def engineParseData(engineMode, soupdata, postdata):
    try:
        flager = 0
        postdata["rank"] = 0

        if soupdata and (engineMode == "ENGINE" or engineMode == "MANUAL"):
            pageUuid = str("-")
            pageUuidUrl = str("-")

            cqlRawId = _at__common_.__uuid__()
            if cqlRawId != 0:
                pageUuid = str(cqlRawId)
                pageUuidUrl = str(encryption.encode_page_url(postdata["fk_user_id"], postdata["id"], cqlRawId))

            bsoup = soupdata

            resultAbout = "-"
            resultTime = "-"

            gAliasKey = ""

            xpdTotalContent = {}
            mongoResults = {}

            targetLink = extract_domain(postdata["target"])

            # SERP FEATURES.  Read before the organic ladder is walked and kept
            # entirely separate from it: nothing below adds a feature row to
            # `domains` or advances postdata["rank"], so an ad at ad-position 1
            # can never be written as organic rank 1.
            serpFeatures, xpdTotalContent, snippetTokens = extract_serp_features(
                bsoup, targetLink, postdata.get("advanced")
            )

            mongoResults.update(
                [
                    ("ID", postdata["id"]),
                    ("WRONGKEYWORD", 0),
                    ("URL", postdata["target"]),
                    ("KEYALIAS", gAliasKey),
                    ("TOTAL_RESULTS", resultAbout),
                    ("TOTAL_TIME", resultTime),
                    ("PAGE_UUID", pageUuid),
                    ("PAGE_UUID_URL", pageUuidUrl),
                    ("TARGET", targetLink),
                    ("SERP_FEATURES", serpFeatures),
                ]
            )

            exactDomain = postdata["exactdomain"]
            keywordTarget = postdata["target"]

            domains = list()
            targetMax = 10

            mongoFlag = 0
            mongoLiveRank = 0
            ratingContent = 0
            reviewsContent = 0
            reviewsText = ""
            cannibalisationResult = []
            snippetRating = "0"

            if "organic_results" in bsoup:
                centerdata = bsoup["organic_results"]
                urlList = []
                urlList.append(targetLink)

                gMainClassBodyContents = [ele for ele in urlList if (ele in str(centerdata))] if centerdata else ""

                if centerdata:
                    for each_set in centerdata:
                        keywordLink = each_set["link"]
                        # Cheap containment pre-filter before the real
                        # comparison below. It has to be case-insensitive:
                        # targetLink is a normalised host and keywordLink is
                        # whatever the provider returned, and a miss here means
                        # the exact comparison never runs at all.
                        keywordLinkMatch = str(keywordLink or "").lower()
                        if keywordLink and mongoFlag == 0:
                            if keywordLinkMatch.find(targetLink) > -1:
                                if exactDomain:
                                    if exact_url_scheme(keywordLink) == exact_url_scheme(keywordTarget):
                                        keywordTarget = keywordLink
                                        mongoFlag = 1

                                elif extract_domain(keywordLink) == extract_domain(keywordTarget):
                                    keywordTarget = keywordLink
                                    mongoFlag = 1

                                if mongoFlag == 1:
                                    mongoLiveRank = each_set["rank"]
                                    snippetRating = extract_rating_from_snippet(each_set["snippet"])

                                    todaySnip = {
                                        "lk": keywordLink,
                                        "tt": get_title(each_set["title"]),
                                        "ds": get_desc(),
                                        "mt": get_cite(each_set["displayed_link"]),
                                        "rt": ratingContent,
                                        "rv": reviewsText,
                                        "dt": str(datetime.now()),
                                        "img": "",
                                    }

                        # CANNIBALISATION
                        if keywordLinkMatch.find(targetLink) > -1:
                            if extract_domain(keywordLink) == targetLink:
                                cannibalisationResult.append(keywordLink)

                        # UPDATING DOMAIN TO COMPETITOR LIST
                        if postdata["rank"] <= (mongoLiveRank + (targetMax - 1)) or mongoLiveRank == 0:
                            domains.append({"rn": str(each_set["rank"]), "dn": extract_domain(keywordLink), "lk": keywordLink})

                        if bool(gMainClassBodyContents) == False and (postdata["rank"]) >= targetMax:
                            break

                        postdata["rank"] += 1

                if mongoFlag > 0:

                    xpdCompContent = domain_competitors(domains, mongoLiveRank, targetMax)

                    mongoResults.update(
                        [
                            ("URL", keywordTarget),
                            ("RANK", mongoLiveRank),
                            ("RATINGS", ratingContent),
                            ("SNIPPET_RATING", snippetRating),
                            ("REVIEWS", reviewsContent),
                            ("SNIPPETS", snippetTokens),
                            ("SNIPPET_DETAILS", xpdTotalContent),
                            ("COMPETITORS", xpdCompContent),
                            ("TODAY", todaySnip if "todaySnip" in locals() else {}),
                            ("CANNIBALISATION", __distinct_pages__(cannibalisationResult)),
                        ]
                    )
                    flager = centralised.mongopush(engineMode, mongoResults)

                elif mongoFlag == 0:

                    xpdCompContent = domain_competitors(domains, 0, targetMax)

                    mongoResults.update(
                        [
                            ("URL", postdata["target"]),
                            ("RANK", 0),
                            ("RATINGS", 0),
                            ("SNIPPET_RATING", "0"),
                            ("REVIEWS", 0),
                            ("SNIPPETS", snippetTokens),
                            ("SNIPPET_DETAILS", xpdTotalContent),
                            ("COMPETITORS", xpdCompContent),
                            ("TODAY", {}),
                            ("CANNIBALISATION", __distinct_pages__(cannibalisationResult)),
                        ]
                    )
                    flager = centralised.mongopush(engineMode, mongoResults)
                else:
                    flager = 4001
            else:
                flager = 4002

    except Exception as e:
        flager = 4003
        parseError = str(e)

    if flager == 1:
        return flager
    elif flager == 4001:
        watchdog.coreLog(" > DESKTOP - UNEXPECTED ERROR ON RANK >> KEY_ID " + str(postdata["id"]), engineMode)
    elif flager == 4002:
        watchdog.coreLog(" > DESKTOP - NO DATA SET INSIDE RSO >> KEY_ID " + str(postdata["id"]), engineMode)
    elif flager == 4003:
        watchdog.coreLog(" > DESKTOP - PARSE EXCEPTION >> KEY_ID " + str(postdata["id"]) + " >>> " + parseError, engineMode)
    else:
        watchdog.coreLog(" > DESKTOP - RSO - GOOGLE PAGE FORMAT ERROR >> KEY_ID " + str(postdata["id"]), engineMode)

    # One keyword that would not parse is one keyword's failure. It used to
    # stop the whole project (ENGINE) or latch core_manual_mode=False on the
    # single global settings row (MANUAL) -- a row with no tenant on it, so one
    # account's bad response disabled refresh for every account, permanently,
    # because nothing ever switched it back on. The caller records the failure
    # against this keyword, counts the attempt and schedules the retry.
    return 0


# ── JSON BRAND PARSER ────────────────────────────────────────────────────────
def engineBrandParseData(engineMode, soupdata, postdata):
    """Parse DataBlue JSON response for brand/conquestor tracking.

    Checks which URLs from postdata['url_list'] appear in organic results
    and writes position data to MongoDB.
    """
    try:
        flager = 0

        if not soupdata or engineMode != "BRAND":
            return 0

        bsoup = soupdata
        if "organic_results" not in bsoup:
            watchdog.coreLog(" > BRAND - NO organic_results IN RESPONSE >> BD_ID " + str(postdata["id"]), "BRAND")
            return 0

        centerdata = bsoup["organic_results"]
        if not centerdata:
            watchdog.coreLog(" > BRAND - EMPTY organic_results >> BD_ID " + str(postdata["id"]), "BRAND")
            return 0

        targetLink  = extract_domain(postdata.get("target", ""))
        url_list    = postdata.get("url_list", []) or []
        targetMax   = 10

        # Build domain list from all organic results (for competitor context)
        domains = []
        for each_set in centerdata:
            _link_ = each_set.get("link", "")
            _rank_ = each_set.get("rank", 0)
            if _link_:
                domains.append({"rn": str(_rank_), "dn": extract_domain(_link_), "lk": _link_})

        # Check each URL in the brand's url_list for presence in SERP
        url_results = []
        for _tracked_url_ in url_list:
            _tracked_domain_ = extract_domain(_tracked_url_)
            _found_rank_   = 0
            _found_link_   = ""
            _found_title_  = ""
            _found_cite_   = ""

            for each_set in centerdata:
                _link_ = each_set.get("link", "")
                _rank_ = each_set.get("rank", 0)
                if _link_ and _link_.find(_tracked_domain_) > -1:
                    _found_rank_  = _rank_
                    _found_link_  = _link_
                    _found_title_ = each_set.get("title", "")
                    _found_cite_  = each_set.get("displayed_link", "")
                    break

            url_results.append({
                "url":   _tracked_url_,
                "rank":  _found_rank_,
                "link":  _found_link_,
                "title": _found_title_,
                "cite":  _found_cite_,
            })

        # Primary target presence (domain-level, same as rank parser)
        mongoFlag     = 0
        mongoLiveRank = 0
        foundLink     = postdata.get("target", "")
        todaySnip     = {}

        for each_set in centerdata:
            _link_ = each_set.get("link", "")
            if _link_ and _link_.find(targetLink) > -1:
                mongoFlag     = 1
                mongoLiveRank = each_set.get("rank", 0)
                foundLink     = _link_
                todaySnip = {
                    "lk":  _link_,
                    "tt":  get_title(each_set.get("title", "")),
                    "ds":  get_desc(),
                    "mt":  get_cite(each_set.get("displayed_link", "")),
                    "rt":  0,
                    "rv":  "",
                    "dt":  str(datetime.now()),
                    "img": "",
                }
                break

        xpdCompContent = domain_competitors(domains, mongoLiveRank, targetMax)

        mongoResults = {
            "ID":           postdata["id"],
            "URL":          foundLink if mongoFlag else postdata.get("target", ""),
            "TARGET":       targetLink,
            "RANK":         mongoLiveRank,
            "RATINGS":      0,
            "REVIEWS":      0,
            "SNIPPETS":     [],
            "SNIPPET_DETAILS": {},
            "COMPETITORS":  xpdCompContent,
            "TODAY":        todaySnip,
            "URL_RESULTS":  url_results,
            "CANNIBALISATION": [],
        }

        flager = centralised.mongopush(engineMode, mongoResults)

    except Exception as e:
        watchdog.coreLog(" > BRAND - PARSE EXCEPTION >> BD_ID " + str(postdata.get("id", "?")) + " >>> " + str(e), "BRAND")
        return 0

    if flager == 1:
        return flager

    watchdog.coreLog(" > BRAND - MONGO PUSH FAILED >> BD_ID " + str(postdata["id"]), "BRAND")
    return 0
