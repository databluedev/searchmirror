"""Which rival brands the models named, read out of answers already stored.

WHY THIS EXISTS
---------------
``views.extract_domains`` finds domain-shaped substrings. That is the right
tool for "which sites did the model link", and it is the wrong tool for "who is
winning the answers you lose", because an ungrounded model links nothing: every
answer this project has stored contains zero ``http(s)://`` URLs. The one value
it ever produced for project 4 -- ``searchapi.io`` -- is a markdown heading
naming a competitor whose brand happens to end in ``.io``. ``Bright Data``,
``Apify``, ``Scrapy``, ``Zyte`` and ``Octoparse`` have no dot in their names and
so could never appear, though ``Bright Data`` is named in six of the six answers
that did not name the brand.

So the rival set has to come from the *prose*, not from the links in it. Nothing
here calls a provider: every name below is read back out of
``LLMPromptAnalytics.response_text``, which was already paid for.

TWO LAYERS, AND ONLY ONE OF THEM IS A MEASUREMENT
-------------------------------------------------
**Detection** (``extract_brand_candidates``) is a *candidate generator*. It
guesses at brand names from typography, and it is wrong in both directions: it
misses ``Oxylabs`` when the model drops it into a prose list with no emphasis,
and it proposes ``Cloudflare`` and ``PerimeterX``, which are anti-bot vendors
rather than rivals. Its output is a suggestion for a human to curate
(``LLMCompetitor.source == "detected"``), never a number to publish.

**Scoring** (``score_group_competitors``) is the measurement. Given a name, it
counts occurrences exactly, with ``views.count_merged_matches`` -- the same
span-merging counter that counts the account's own brand. One definition of "an
occurrence" for both sides, or the comparison between them means nothing.

WHAT IS DELIBERATELY NOT HERE
-----------------------------
No share of voice. A share needs a denominator, and the only honest denominators
available are "you plus the rivals we happen to have detected" -- which moves
when detection improves rather than when the world does. ``answers_lost_to``
below states its denominator in the payload instead: how many answers did not
name you, and in how many of those was this rival named.

No 0-100 visibility score normalised across every domain in the database. That
construction makes one account's number move when an unrelated account runs a
crawl.
"""

import re


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

# Words that carry no brand on their own. A candidate is rejected when EVERY
# word in it is generic ("Key Features", "Scraping Browser"), which is the rule
# that keeps "Bright Data" -- "data" is generic, "bright" is not.
_GENERIC_WORDS = frozenset("""
best top key features feature pricing price cost costs cons pros drawbacks
limitations caveats languages language example examples tools tool toolkit
recommended supported engines engine proxies proxy browser browsers headers
header address concurrency retries retry handshake tab network networks canvas
fingerprint fingerprinting randomization stealth plugins plugin platform
platforms api apis sdk sdks service services solution solutions library
libraries framework frameworks scraping scraper scrapers crawling crawler
crawlers extraction parsing rendering data dataset datasets web website
websites page pages site sites overview summary conclusion note notes tip tips
warning caveat verdict comparison table matrix winner alternative alternatives
choice choices option options use using used cases case scenario scenarios
workflow workflows pipeline pipelines free paid open source enterprise cloud
self hosted hosting managed unmanaged speed performance reliability scale
scaling support docs documentation setup integration integrations request
requests response responses session sessions rotation bypass blocked blocking
volume limits quota quotas dashboard interface visual code no-code low-code
snippet injection queue queues processing distributed backoff practice
practices guidelines legal ethical compliance strength strengths area areas
step steps mention honorable pick guide review reviews search results result
management orchestration compliance governance privacy control access common
simple advanced modern native powered first driven ready friendly premium
bot bots anti-bot unlocker unblocker captcha captchas rendering headless
for of to in on at by from with and or the a an vs versus per via into over
under about across after before between during without within than then
""".split())

# First words that begin a sentence, not a brand. Applied to the first word
# only -- "Bright" starts a brand, "Best" starts a heading.
_PHRASE_STOPWORDS = frozenset("""
The This That These Those For With When Where While What Which Who Whom Why How
However Although Because Since Therefore Thus Also And But Or If Then Than
According Consider Choose Pick Use Using Avoid Implement Respect Send Inspect
Rotate Scrape Patch Handle Build Buy Make Get Set Put Run Try Look Read Write
Do Does Don You Your Our We They It Its Their There Here Just Only Both Each
Every All Any Some Most More Less Many Few Note Overall Finally Next Previous
Before After Above Below Instead Rather Whether Unless Until Once Again
Versus Vs Common Popular Recommended Typical Regular Standard Basic Simple
""".split())

# Acronyms that are vocabulary, not vendors. Deliberately does NOT contain AWS,
# GCP, IBM or Azure: for "who is named in the answers you lose", the hyperscalers
# are competitors when they are named as one.
_ACRONYM_STOPWORDS = frozenset("""
AI API SEO GEO SERP LLM RAG SDK URL HTML CSS XML JSON CSV YAML SQL NOSQL HTTP
HTTPS TLS SSL DNS IP TCP UDP CPU GPU RAM ROM OS CLI GUI UI UX IDE DX CI CD QA
SAAS PAAS IAAS B2B B2C ROI KPI GDPR CCPA PII DDOS DOS CAPTCHA ETL ELT JS TS PHP
PDF FAQ TLDR OK NA TBD IMO EU US UK USA MVP SLA TOS EULA REST SOAP GRPC JWT
OAUTH SSO VPN CDN WAF ISP ASN ZIP SGE SPA DOM GET POST PUT PATCH HEAD DELETE
JA3 JA4 IDS IPS RPA OCR CSV TSV UTC ID IDS URI URN MIME UA
""".split())

# Hosts that are never a rival when they turn up as a cited source: platforms
# everybody links, and the placeholder domains that appear in examples.
_NON_BRAND_HOSTS = frozenset("""
facebook.com twitter.com x.com linkedin.com instagram.com youtube.com
tiktok.com pinterest.com reddit.com github.com gitlab.com bitbucket.org
stackoverflow.com wikipedia.org medium.com substack.com w3.org mozilla.org
schema.org gravatar.com gstatic.com googleapis.com googleusercontent.com
doubleclick.net cloudfront.net amazonaws.com example.com example.org
example.net localhost target-website.com yourdomain.com
""".split())

# Languages, runtimes and stock infrastructure. Real products, none of them the
# rival a tracked brand is losing an answer to.
_NON_BRAND_TERMS = frozenset(term.lower() for term in """
Python Java JavaScript TypeScript Ruby PHP Golang Rust Kotlin Swift Perl Scala
Elixir Node NodeJS Node.js Deno Bun Django Flask FastAPI Rails Laravel Spring
Docker Kubernetes Linux Windows MacOS Ubuntu Debian Nginx Apache Celery
Markdown Chrome Firefox Safari Edge Chromium WebKit Blink Webdriver
DoS DDoS GraphQL WebGL WebRTC WebSocket WebSockets DevTools
PostgreSQL MySQL MariaDB MongoDB SQLite Redis Memcached RabbitMQ Kafka
Elasticsearch OpenSearch Airflow Terraform Ansible Jenkins
""".split())

# The same platforms as `_NON_BRAND_HOSTS`, spelled the way prose spells them.
# Derived rather than typed twice: a host excluded as a citation and its bare
# name admitted as a brand is the same list disagreeing with itself, which is
# how "YouTube" was proposed as a rival while "youtube.com" was filtered out.
_NON_BRAND_TERMS = _NON_BRAND_TERMS | frozenset(
    host.split(".")[0] for host in _NON_BRAND_HOSTS
)


# ---------------------------------------------------------------------------
# Candidate discovery
# ---------------------------------------------------------------------------

# A model's answer is markdown, and markdown is where the brands are. Bold spans
# and headings are how every one of these answers introduces a vendor:
# "#### **A. ScrapingBee**", "| **Bright Data** |", "* **Octoparse:**". This is
# the source that finds the single-word, single-capital names -- Apify, Scrapy,
# Zyte, Firecrawl, Octoparse -- that no Title-Case or acronym pattern can reach.
_EMPHASIS_RE = re.compile(r"\*\*(.+?)\*\*|^#{1,6}[ \t]+(.+?)[ \t]*$", re.MULTILINE)

# "Brand.com" written in prose without a scheme.
_DOTTED_RE = re.compile(
    r"\b([A-Z][A-Za-z0-9\-]{2,})\.(?:com|io|net|org|ai|co|dev|app|cloud|sh)\b"
)

# Two- and three-word Title Case phrases. THIS is what finds "Bright Data".
_TITLECASE_RE = re.compile(r"\b([A-Z][a-z]{2,}(?: [A-Z][A-Za-z0-9]{2,}){1,2})\b")

# Single tokens carrying an internal capital: ScrapingBee, ScraperAPI,
# DataForSEO, ZenRows, ValueSERP, CapSolver. A lowercase letter is REQUIRED
# before the second capital, or an all-caps plural satisfies it -- "CAPTCHAs"
# and "LLMs" both parse as camel case without that guard, and both shipped as
# detected brands until it was added.
_CAMEL_RE = re.compile(r"\b([A-Z][a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*)\b")

# Trailing TLDs to shed so "SearchApi.io" from a heading and "searchapi" from a
# linked host are one brand rather than two rows.
_TLD_SUFFIX_RE = re.compile(
    r"\.(?:com|io|net|org|ai|co|dev|app|cloud|sh|tech|xyz)$", re.IGNORECASE
)

# Bare acronyms: AWS, GCP, IBM.
_ACRONYM_RE = re.compile(r"\b([A-Z]{2,6})\b")

# A comma-separated run of proper nouns: "Bright Data, Oxylabs, Smartproxy, or
# Webshare". Only admitted when a run already contains a name found by another
# source, so it expands a known list rather than inventing one -- this is the
# only way a single-word rival named once, in plain prose, with no emphasis, can
# ever be seen.
_LIST_MEMBER = r"[A-Z][A-Za-z0-9][A-Za-z0-9&.\-]*(?:[ ][A-Z][A-Za-z0-9&.\-]+)?"
_LIST_RUN_RE = re.compile(
    r"%(m)s(?:[ \t]*,[ \t]*%(m)s)+(?:[ \t]*,?[ \t]*(?:or|and)[ \t]+%(m)s)?"
    % {"m": _LIST_MEMBER}
)
_LIST_SPLIT_RE = re.compile(r"[ \t]*,[ \t]*|[ \t]+(?:or|and)[ \t]+")

# Splitting one emphasis span into the names inside it: "**Scrapy / Selenium**",
# "**ScrapingBee / ZenRows (Best Simple APIs)**", "(Cloudflare, Akamai)".
_SPLIT_RE = re.compile(r"[ \t]*(?:/|&|,|\bvs\.?\b|\band\b|\bor\b)[ \t]*")
_PAREN_RE = re.compile(r"[ \t]*\([^)]*\)?")
_ENUMERATOR_RE = re.compile(r"^(?:\d{1,2}|[A-Za-z])[ \t]*[.):][ \t]+")
_DECORATION = " \t*_-–—:;.,!?\"'“”‘’()[]{}|"

# Long enough that a phrase this size is a sentence fragment, not a name.
_MAX_WORDS = 3
_MAX_CHARS = 40


def _is_generic_word(word):
    """A word that carries no brand: filler prose, or acronym vocabulary.

    The trailing "s" comes off before the acronym check, or "CAPTCHAs", "SPAs"
    and "URLs" read as brands while their singulars are correctly rejected.
    """
    bare = word.strip(_DECORATION)
    if not bare:
        return True
    if bare.lower() in _GENERIC_WORDS:
        return True
    upper = bare.upper()
    if upper in _ACRONYM_STOPWORDS:
        return True
    return upper.endswith("S") and upper[:-1] in _ACRONYM_STOPWORDS


def _clean_candidate(raw):
    """Normalise one raw span into a brand name, or ``None`` to reject it.

    Order matters: markdown decoration comes off before the list enumerator is
    looked for, because the raw span for a heading is ``**A. ScrapingBee**`` and
    an enumerator pattern anchored at the start sees the asterisks first.
    """
    if not raw:
        return None
    name = raw.strip().strip(_DECORATION)
    name = _ENUMERATOR_RE.sub("", name)
    name = _PAREN_RE.sub("", name)
    name = name.strip(_DECORATION)
    # "SearchApi.io" in a heading and "searchapi" from a linked host are the
    # same rival; carrying the TLD would track it twice.
    name = _TLD_SUFFIX_RE.sub("", name)
    if not name or len(name) > _MAX_CHARS or len(name) < 3:
        return None
    # "Anti-bots", "Pay-as-you-go", "SQL-like": a hyphen into lowercase is a
    # compound adjective. "Anti-Captcha" and "Crawl4AI" survive it.
    if re.search(r"-[a-z]", name):
        return None
    words = name.split()
    if not words or len(words) > _MAX_WORDS:
        return None
    for word in words:
        if not (word[0].isupper() or word[0].isdigit()):
            return None
    if words[0] in _PHRASE_STOPWORDS:
        return None
    if all(_is_generic_word(word) for word in words):
        return None
    if name.lower() in _NON_BRAND_TERMS:
        return None
    if name.upper() == name and name.upper() in _ACRONYM_STOPWORDS:
        return None
    return name


def _name_patterns(name, url=""):
    """Every way one competitor can be written, as regex source strings.

    Boundaries are ``(?<![\\w-])`` / ``(?![\\w-])`` rather than ``\\b`` so a
    hyphen cannot be read as a word edge: ``Apify`` must not match inside
    ``Apify-style``, and ``Zyte`` must not match inside ``Zyte-API``.
    """
    patterns = []
    if url:
        from llmtracker.views import get_domain_from_url

        domain = get_domain_from_url(url)
        if domain:
            patterns.append(
                r"(?:https?://)?(?:www\.)?%s(?![\w-])" % re.escape(domain)
            )
    tokens = [re.escape(token) for token in (name or "").split()]
    if tokens:
        patterns.append(r"(?<![\w-])%s(?![\w-])" % r"\s+".join(tokens))
    return patterns


def count_name_mentions(text, name, url=""):
    """How many times ``text`` names this competitor, occurrences merged.

    Delegates to the same counter the account's own brand uses, so "a mention"
    means one thing across the whole feature.
    """
    from llmtracker.views import count_merged_matches

    return count_merged_matches(text, _name_patterns(name, url))


def first_name_index(text, name, url=""):
    """Character offset of the first time ``text`` names it; -1 when it never does."""
    if not text:
        return -1
    starts = []
    for pattern in _name_patterns(name, url):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            starts.append(match.start())
    return min(starts) if starts else -1


def _cited_host_candidates(prose, own_domain):
    """Registrable hosts the answer actually linked, as brand labels.

    Empty on every answer this project has stored -- ungrounded models link
    nothing -- and the reason the old citation list was not a rival list. Kept
    because it is the source that becomes the good one the moment provider
    grounding is switched on.
    """
    from llmtracker.views import extract_domains

    labels = set()
    for domain in extract_domains(prose):
        if domain == own_domain or domain in _NON_BRAND_HOSTS:
            continue
        label = domain.split(".")[0]
        if len(label) < 3 or label.lower() in _NON_BRAND_TERMS:
            continue
        labels.add(label[0].upper() + label[1:])
    return labels


def _drop_shadowed(found):
    """Collapse a name and a longer name containing it into the one that leads.

    "Zyte" (12) and "Zyte API" (2) are one vendor written two ways, as are
    "Microsoft" and "Microsoft Azure". Keep whichever is named more often, and
    the longer one on a tie -- a phrase that always appears in full is the
    vendor's actual name, while a bare word appearing far more often is.
    """
    kept = dict(found)
    for name in sorted(found, key=lambda item: -len(item)):
        words = name.split()
        for other in list(kept):
            if other == name or other not in kept or name not in kept:
                continue
            other_words = other.split()
            if len(other_words) <= len(words):
                continue
            if not all(word in other_words for word in words):
                continue
            # `name` is contained in the longer `other`.
            if kept[name]["mentions"] > kept[other]["mentions"]:
                kept.pop(other, None)
            else:
                kept.pop(name, None)
    return kept


def _merge_casings(entries):
    """One row per brand, keeping the casing the model actually wrote.

    ``SearchApi`` from a heading and ``Searchapi`` from a linked host are the
    same rival. The variant with more capitals wins: a vendor's own casing
    carries them and a title-cased host label does not.
    """
    merged = {}
    for name in sorted(entries, key=lambda item: (-sum(c.isupper() for c in item), item)):
        key = name.lower()
        entry = entries[name]
        if key in merged:
            merged[key]["presented"] = merged[key]["presented"] or entry["presented"]
            continue
        merged[key] = {"name": name, "presented": entry["presented"]}
    return {item["name"]: {"presented": item["presented"]} for item in merged.values()}


def extract_brand_candidates(text, own_domain=""):
    """Brand names this one answer appears to mention.

    Returns ``{name: {"mentions": int, "presented": bool}}``.

    A CANDIDATE GENERATOR, NOT A MEASUREMENT. Seven sources are unioned, then
    each surviving name is counted exactly with the span-merging counter. Recall
    on ungrounded prose is partial by construction: a rival named once, mid
    sentence, with no emphasis and no dot in its name leaves no typographic
    trace to find. Present the output as "we spotted these -- track them?".

    ``presented`` marks the names the model set out AS A NAME rather than
    fragments recovered from a sentence: a whole bold span, a linked host, a
    ``Brand.tld``, or a token with an internal capital. Nothing but typography
    separates "Bright Data" from "Simple API" in a Title Case scan, and this is
    the signal that does -- see ``SEED_MIN_ANSWERS`` for what it gates.
    """
    from llmtracker.views import _strip_code

    if not text:
        return {}
    prose = _strip_code(text)
    own_domain = (own_domain or "").lower()
    # name -> was it ever set out as a name in its own right
    found = {}

    def note(raw, presented):
        cleaned = _clean_candidate(raw)
        if not cleaned:
            return
        entry = found.setdefault(cleaned, {"presented": False})
        entry["presented"] = entry["presented"] or presented

    # 1. hosts the answer linked
    for label in _cited_host_candidates(prose, own_domain):
        note(label, True)

    # 2. Brand.tld written in prose
    for label in _DOTTED_RE.findall(prose):
        note(label, True)

    # 3. emphasis heads. A WHOLE bold span is a name being introduced
    #    ("**Octoparse:**", "| **Bright Data** |"); a fragment split out of a
    #    longer span or a "###" section title is not.
    for bold, heading in _EMPHASIS_RE.findall(prose):
        span = bold or heading
        parts = _SPLIT_RE.split(span)
        whole = bool(bold) and len(parts) == 1
        for part in parts:
            note(part, whole)

    # 4. multi-word Title Case -- this is what finds "Bright Data"
    for phrase in _TITLECASE_RE.findall(prose):
        note(phrase, False)

    # 5. internal-capital single tokens: ScrapingBee, ZenRows, DataForSEO
    for token in _CAMEL_RE.findall(prose):
        note(token, True)

    # 6. acronyms
    for token in _ACRONYM_RE.findall(prose):
        if token in _ACRONYM_STOPWORDS:
            continue
        note(token, False)

    # 7. expansion of proper-noun runs that already contain a known name
    lowered = {name.lower() for name in found}
    for run in _LIST_RUN_RE.findall(prose):
        members = [_clean_candidate(part) for part in _LIST_SPLIT_RE.split(run)]
        members = [member for member in members if member]
        if len(members) < 2:
            continue
        if not any(member.lower() in lowered for member in members):
            continue
        for member in members:
            note(member, False)

    if own_domain:
        # Drop the account's own brand however it is written -- bare, as its
        # domain, and inside a longer phrase. "Datablue Scraper" is the model
        # describing the customer, not a rival, and listing the customer among
        # the brands beating them is worse than listing nobody.
        own_label = own_domain.split(".")[0].lower()
        found = {
            name: entry for name, entry in found.items()
            if name.lower() != own_domain
            and own_label not in {word.lower() for word in name.split()}
        }

    found = _merge_casings(found)
    counted = {}
    for name, entry in found.items():
        occurrences = count_name_mentions(text, name)
        if occurrences > 0:
            counted[name] = {
                "mentions": occurrences, "presented": entry["presented"],
            }
    return _drop_shadowed(counted)


# ---------------------------------------------------------------------------
# Detection and seeding across a group's stored answers
# ---------------------------------------------------------------------------

# WHAT EARNS A PLACE IN THE TRACKED SET
# -------------------------------------
# Detection is deliberately permissive, because a name it never proposes is a
# name the user has to think of unaided. Seeding is not: these rows are what
# `answers_lost_to` is computed from, and a heading mistaken for a vendor there
# is a false claim about who is beating the customer.
#
# Two gates, both required.
#
# 1. FREQUENCY. Named in two separate answers, or three times in one. The
#    second half is not redundant: "SerpApi" is named five times in the single
#    SERP-API answer and nowhere else, and it is unquestionably a rival.
# 2. PRESENTATION. Set out as a name at least once -- a whole bold span, a
#    linked host, a `Brand.tld`, or an internal capital. This is the gate that
#    separates "Bright Data", which the answers print as `**Bright Data**` in a
#    comparison table, from "Simple API" and "Web Unlocker", which are
#    Title Case fragments of sentences and pass every frequency test.
#
# The cost is real and is the right trade: a rival that only ever appears in
# unemphasised prose is not seeded, so the user adds it by hand -- and the
# moment they do, every stored answer is scored for it retroactively. Missing
# from the list is recoverable; wrong on the dashboard is not.
SEED_MIN_ANSWERS = 2
SEED_MIN_MENTIONS = 3
SEED_REQUIRE_PRESENTED = True
# A suggestion nobody can read is not one. Cap what gets written so a noisy
# answer cannot bury the real names.
SEED_MAX_COMPETITORS = 25


def _done_rows(group):
    """The group's completed analytics rows, newest first, answers included."""
    from llmtracker.models import LLMPromptAnalytics

    return list(
        LLMPromptAnalytics.objects.filter(
            fk_prompt__fk_group=group, track_status="DONE"
        ).select_related("fk_prompt")
    )


def detect_group_brands(group, rows=None):
    """Every brand candidate across a group's stored answers, with its evidence.

    Returns ``{name: {"answers", "mentions", "lost_answers", "presented"}}``
    where ``answers`` counts distinct answers naming it, ``mentions`` counts
    occurrences, ``lost_answers`` counts answers that named it and did NOT name
    the account's brand, and ``presented`` is true when at least one answer set
    it out as a name rather than as a fragment of a sentence. No provider call:
    this is a re-read of ``response_text``.
    """
    from llmtracker.views import get_domain_from_url

    rows = _done_rows(group) if rows is None else rows
    own_domain = get_domain_from_url(group.domain_name or "")
    found = {}
    for row in rows:
        text = row.response_text or ""
        if not text:
            continue
        for name, hit in extract_brand_candidates(text, own_domain).items():
            entry = found.setdefault(
                name,
                {"answers": 0, "mentions": 0, "lost_answers": 0, "presented": False},
            )
            entry["answers"] += 1
            entry["mentions"] += hit["mentions"]
            entry["presented"] = entry["presented"] or hit["presented"]
            if not row.is_mention:
                entry["lost_answers"] += 1
    return found


def seed_group_competitors(group, rows=None):
    """Create tracked competitors from what detection found. Returns a summary.

    Only ever adds. A name the user deleted or untracked is not resurrected on
    the next detection run, and a competitor the user added by hand is never
    downgraded to ``detected`` -- curation has to survive a re-scan or it is not
    curation.
    """
    from llmtracker.models import LLMCompetitor

    detected = detect_group_brands(group, rows=rows)
    qualifying = [
        (name, evidence) for name, evidence in detected.items()
        if (evidence["presented"] or not SEED_REQUIRE_PRESENTED)
        and (evidence["answers"] >= SEED_MIN_ANSWERS
             or evidence["mentions"] >= SEED_MIN_MENTIONS)
    ]
    qualifying.sort(
        key=lambda item: (-item[1]["answers"], -item[1]["mentions"], item[0])
    )
    qualifying = qualifying[:SEED_MAX_COMPETITORS]

    existing = {
        competitor.name.lower(): competitor
        for competitor in LLMCompetitor.objects.filter(fk_group=group)
    }
    created = 0
    for name, evidence in qualifying:
        current = existing.get(name.lower())
        if current is None:
            LLMCompetitor.objects.create(
                fk_group=group,
                name=name,
                source="detected",
                detected_answers=evidence["answers"],
                detected_mentions=evidence["mentions"],
            )
            created += 1
            continue
        if current.source != "detected":
            continue
        if (current.detected_answers, current.detected_mentions) == (
            evidence["answers"], evidence["mentions"]
        ):
            continue
        current.detected_answers = evidence["answers"]
        current.detected_mentions = evidence["mentions"]
        current.save(update_fields=["detected_answers", "detected_mentions"])

    return {
        "candidates": len(detected),
        "qualifying": len(qualifying),
        "created": created,
        "tracked": LLMCompetitor.objects.filter(fk_group=group).count(),
    }


# ---------------------------------------------------------------------------
# Scoring the tracked set against stored answers
# ---------------------------------------------------------------------------


def score_group_competitors(group, rows=None):
    """Re-read every stored answer and score every tracked competitor against it.

    COSTS NOTHING. The answers are already in the database; adding a competitor
    re-scores all of history for it retroactively. One
    ``LLMCompetitorAnalytics`` row per (competitor, answer), upserted, and rows
    for competitors or answers that no longer exist are removed so the table
    cannot outlive what it describes.
    """
    from llmtracker.models import LLMCompetitor, LLMCompetitorAnalytics

    rows = _done_rows(group) if rows is None else rows
    # `is_tracked` is filtered in Python, not in the query: djongo renders a
    # boolean field test as a bare column name and its SQL parser rejects it
    # (SQLDecodeError). The same reason geo_summary counts `is_mention` in a
    # comprehension rather than a filter.
    competitors = [
        competitor
        for competitor in LLMCompetitor.objects.filter(fk_group=group)
        if competitor.is_tracked
    ]
    row_by_id = {row.analytics_id: row for row in rows}

    existing = {}
    stale = []
    competitor_ids = {competitor.competitor_id for competitor in competitors}
    for record in LLMCompetitorAnalytics.objects.filter(
        fk_competitor__fk_group=group
    ):
        key = (record.fk_competitor_id, record.fk_analytics_id)
        if record.fk_competitor_id not in competitor_ids or key[1] not in row_by_id:
            stale.append(record)
            continue
        existing[key] = record
    for record in stale:
        record.delete()

    written = 0
    for competitor in competitors:
        for row in rows:
            text = row.response_text or ""
            occurrences = count_name_mentions(text, competitor.name, competitor.url)
            first = first_name_index(text, competitor.name, competitor.url)
            prominence = (
                round(max(0.0, 1.0 - (first / max(len(text), 1))), 3)
                if first >= 0 else 0.0
            )
            record = existing.get((competitor.competitor_id, row.analytics_id))
            if record is None:
                LLMCompetitorAnalytics.objects.create(
                    fk_competitor=competitor,
                    fk_analytics=row,
                    is_mentioned=occurrences > 0,
                    mention_count=occurrences,
                    first_index=first,
                    position_score=prominence,
                )
                written += 1
                continue
            before = (
                record.is_mentioned, record.mention_count,
                record.first_index, record.position_score,
            )
            after = (occurrences > 0, occurrences, first, prominence)
            if before == after:
                continue
            (record.is_mentioned, record.mention_count,
             record.first_index, record.position_score) = after
            record.save(update_fields=[
                "is_mentioned", "mention_count", "first_index", "position_score",
            ])
            written += 1

    return {
        "competitors": len(competitors),
        "answers": len(rows),
        "rows_written": written,
        "rows_removed": len(stale),
    }


def refresh_group_competitors(group):
    """Detect, seed and score in one pass. The whole back-fill, no provider call."""
    rows = _done_rows(group)
    seeded = seed_group_competitors(group, rows=rows)
    scored = score_group_competitors(group, rows=rows)
    return {"seed": seeded, "score": scored}


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def group_competitor_summary(group):
    """Who was named in this group's answers, and who was named in the lost ones.

    Empty lists and zeroes for a group with no Geo data -- a valid state, not an
    error. Every count travels with the denominator it was measured against.
    """
    from llmtracker.models import LLMCompetitor, LLMCompetitorAnalytics

    rows = _done_rows(group)
    answers_total = len(rows)
    lost_ids = {row.analytics_id for row in rows if not row.is_mention}
    answers_lost_total = len(lost_ids)

    competitors = {
        competitor.competitor_id: competitor
        for competitor in LLMCompetitor.objects.filter(fk_group=group)
    }
    tallies = {}
    for record in LLMCompetitorAnalytics.objects.filter(
        fk_competitor__fk_group=group
    ):
        competitor = competitors.get(record.fk_competitor_id)
        if competitor is None or not record.is_mentioned:
            continue
        entry = tallies.setdefault(
            competitor.competitor_id,
            {"answers": 0, "mentions": 0, "lost_answers": 0},
        )
        entry["answers"] += 1
        entry["mentions"] += int(record.mention_count or 0)
        if record.fk_analytics_id in lost_ids:
            entry["lost_answers"] += 1

    listed = []
    for competitor_id, competitor in competitors.items():
        entry = tallies.get(
            competitor_id, {"answers": 0, "mentions": 0, "lost_answers": 0}
        )
        listed.append({
            "competitor_id": str(competitor_id),
            "name": competitor.name,
            "url": competitor.url or "",
            "source": competitor.source,
            "is_tracked": bool(competitor.is_tracked),
            "answers": entry["answers"],
            "mentions": entry["mentions"],
            "lost_answers": entry["lost_answers"],
        })
    listed.sort(key=lambda item: (-item["answers"], -item["mentions"], item["name"]))

    # THE HONEST REPLACEMENT FOR `cited_instead`. Not "who is cited", which no
    # ungrounded answer reveals, but who is NAMED in the answers that did not
    # name you -- ranked by how many of those answers each appears in, with the
    # denominator beside it. This is not a share of voice and must not be
    # rendered as a percentage of anything.
    lost_to = [
        {
            "name": item["name"],
            "answers": item["lost_answers"],
            "mentions": item["mentions"],
            "source": item["source"],
        }
        for item in listed
        if item["is_tracked"] and item["lost_answers"] > 0
    ]
    lost_to.sort(key=lambda item: (-item["answers"], -item["mentions"], item["name"]))

    return {
        "competitors": listed,
        "competitors_tracked": sum(1 for item in listed if item["is_tracked"]),
        "answers_total": answers_total,
        "answers_lost_total": answers_lost_total,
        "answers_lost_to": lost_to[:15],
    }


def suggest_group_competitors(group, limit=25):
    """Brands detected in stored answers that are not tracked yet.

    Feeds a "we spotted these -- track them?" prompt. Never a measured number:
    see the module docstring on why detection and scoring are separate.
    """
    from llmtracker.models import LLMCompetitor

    tracked = {
        competitor.name.lower()
        for competitor in LLMCompetitor.objects.filter(fk_group=group)
    }
    detected = detect_group_brands(group)
    suggestions = [
        {
            "name": name,
            "answers": evidence["answers"],
            "mentions": evidence["mentions"],
            "lost_answers": evidence["lost_answers"],
            # True when some answer set this out AS a name -- a bold span, a
            # linked host, a Brand.tld, an internal capital. The rest are Title
            # Case fragments of sentences, kept because a real rival named once
            # in plain prose looks identical to one, and ranked below.
            "presented": evidence["presented"],
        }
        for name, evidence in detected.items()
        if name.lower() not in tracked
    ]
    # Ranked by evidence, not by presentation: "Cloudflare" is named across four
    # answers and never in bold, and burying it under a dozen one-off bold spans
    # would be ranking typography above frequency. `presented` rides along so
    # the UI can mark which suggestions are firmer than others.
    suggestions.sort(
        key=lambda item: (-item["answers"], -item["mentions"], item["name"])
    )
    return suggestions[:limit]


# ---------------------------------------------------------------------------
# CLI -- the back-fill over answers already stored
# ---------------------------------------------------------------------------


def main():
    """Back-fill competitor detection and scoring. Spends nothing.

    Run:  docker compose exec backend python -m llmtracker.brands
          docker compose exec backend python -m llmtracker.brands --group 4
          docker compose exec backend python -m llmtracker.brands --dry-run
    """
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(description="Back-fill Geo competitor brands.")
    parser.add_argument("--group", default=None, help="limit to one project id")
    parser.add_argument(
        "--dry-run", action="store_true", help="report detection, write nothing"
    )
    args = parser.parse_args()

    import django

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tracker.settings")
    django.setup()

    from serp.models import Groups

    groups = Groups.objects.all()
    if args.group:
        groups = groups.filter(id=args.group)

    for group in groups:
        rows = _done_rows(group)
        if not rows:
            continue
        print("project %s (%s): %d stored answers" % (
            group.id, group.domain_name, len(rows)))
        if args.dry_run:
            for name, evidence in sorted(
                detect_group_brands(group, rows=rows).items(),
                key=lambda item: (-item[1]["answers"], -item[1]["mentions"], item[0]),
            ):
                print("    %-28s answers=%d mentions=%d lost=%d %s" % (
                    name, evidence["answers"], evidence["mentions"],
                    evidence["lost_answers"],
                    "SEED" if (
                        evidence["presented"]
                        and (evidence["answers"] >= SEED_MIN_ANSWERS
                             or evidence["mentions"] >= SEED_MIN_MENTIONS)
                    ) else ""))
            continue
        summary = refresh_group_competitors(group)
        print("    seeded %d new, %d tracked; %d competitor rows written"
              % (summary["seed"]["created"], summary["seed"]["tracked"],
                 summary["score"]["rows_written"]))


if __name__ == "__main__":
    main()
