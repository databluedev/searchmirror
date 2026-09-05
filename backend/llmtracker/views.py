import os
import json
import re
import uuid
import openai
import anthropic
from django.http import JsonResponse
from django.conf import settings
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from llmtracker.models import LLMPrompt, LLMPromptAnalytics, LLMMetricSnapshot
from account.models import Account
from serp.models import Groups, Settings
from django.db.models import Q
from textblob import TextBlob
from django.db import transaction
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from urllib.parse import urlparse
from rest_framework.permissions import IsAuthenticated
from account.cron_auth import cron_only
from account.aikeys import resolve_key
from account.completions import (
    AICompletionFailed,
    NoAIProviderConfigured,
    describe_provider_failure,
    generate_text,
)

logger = logging.getLogger(__name__)


def get_domain_from_url(value: str) -> str:
    """Return bare domain from a URL or domain string (strip scheme, www, port)."""
    try:
        if not value:
            return ""
        parsed = urlparse(value if "://" in value else f"http://{value}")
        host = parsed.netloc or parsed.path
        domain = host.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if ":" in domain:
            domain = domain.split(":", 1)[0]
        return domain
    except Exception:
        v = str(value).lower()
        return v[4:] if v.startswith("www.") else v


# A model's answer is prose with code samples in it, and `label.label` is the
# shape of a Python attribute as much as it is the shape of a domain. Reading
# the code as prose is what put `requests.get`, `response.status` and
# `navigator.webdriver` in the citation list. Remove fenced blocks and inline
# spans before looking for anything.
_CODE_FENCE = re.compile(r"```.*?```", re.DOTALL)
_UNCLOSED_FENCE = re.compile(r"```.*\Z", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`\n]*`")

# Generic TLDs actually seen in citations. Every two-letter label is accepted as
# a country code, which covers ~250 of them without listing any. Everything else
# is rejected: a blocklist can never close this hole, because ".webdriver" and
# ".sleep" are not file extensions and both shipped as citations. gTLDs that
# collide with everyday attribute names (.status, .name, .data) are left out on
# purpose -- a missed citation is recoverable, an invented one is not.
_GENERIC_TLDS = frozenset({
    "com", "net", "org", "edu", "gov", "mil", "int", "info", "biz", "pro",
    "mobi", "asia", "jobs", "tel", "travel", "museum", "aero", "coop", "cat",
    "xyz", "app", "dev", "cloud", "tech", "online", "site", "website", "store",
    "shop", "blog", "news", "media", "agency", "studio", "design", "digital",
    "software", "solutions", "systems", "services", "consulting", "group",
    "company", "ventures", "partners", "capital", "finance", "bank",
    "insurance", "legal", "law", "health", "care", "clinic", "academy",
    "school", "college", "university", "institute", "press", "review",
    "reviews", "guide", "tools", "analytics", "marketing", "seo", "social",
    "network", "host", "hosting", "space", "world", "life", "live", "today",
    "global", "top", "club", "fun", "wiki", "works", "team", "page", "email",
    "center", "directory", "expert", "exchange", "market", "money", "zone",
    "rocks", "ninja", "codes", "computer", "engineering", "technology",
    "support", "tips", "training", "video", "photo", "photography", "music",
    "art", "gallery",
})

# Two-letter country codes that are also file extensions. ".py", ".js" and
# ".sh" are real ccTLDs, so the country-code rule above would otherwise read
# "views.py" or "build.sh" in prose as a site.
_NON_TLD = frozenset({
    "txt", "md", "rst", "js", "jsx", "ts", "tsx", "mjs", "cjs", "py", "rb",
    "go", "rs", "php", "java", "kt", "swift", "c", "h", "cpp", "cs", "json",
    "html", "htm", "css", "scss", "sass", "less", "xml", "yml", "yaml", "toml",
    "ini", "cfg", "conf", "env", "lock", "csv", "tsv", "sql", "db", "sqlite",
    "png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "bmp", "pdf", "doc",
    "docx", "xls", "xlsx", "ppt", "pptx", "zip", "tar", "gz", "rar", "7z",
    "sh", "bat", "ps1", "exe", "dll", "so", "dylib", "log", "bak", "tmp",
    "map", "min", "webmanifest",
})

_DOMAIN_RE = re.compile(
    # Either an explicit scheme, or a boundary that is not itself part of a
    # dotted identifier -- so the ".get" in "requests.get" cannot start a match.
    r"(?:https?://|(?<![\w.@/-]))(?:www\.)?"
    r"((?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+([a-zA-Z]{2,24}))"
    r"(?![\w-])",
    re.IGNORECASE,
)


def _strip_code(text: str) -> str:
    """Blank out fenced code blocks and inline code spans.

    A fenced block goes entirely: a URL inside one is a code sample, which is
    how "target-website.com" from `requests.get("https://target-website.com")`
    became a cited source. An inline span holding an explicit http(s) URL is
    kept, because writing `https://ahrefs.com` in backticks is still a citation
    -- it is the bare `navigator.webdriver` shape that is not.
    """
    if not text:
        return ""
    out = _CODE_FENCE.sub(" ", text)
    out = _UNCLOSED_FENCE.sub(" ", out)
    return _INLINE_CODE.sub(
        lambda m: m.group(0) if "://" in m.group(0) else " ", out
    )


def extract_domains(text: str) -> list:
    """Pull real site domains out of a model's answer, in first-seen order.

    A model naming "ahrefs.com" or linking https://moz.com/blog is citing a
    source; `requests.get`, "robots.txt" and "views.py" are not. Two filters do
    that: code is removed first, then the trailing label must be a real TLD --
    a two-letter country code or one of the generic TLDs above.
    """
    if not text:
        return []
    domains = []
    for full, tld in _DOMAIN_RE.findall(_strip_code(text)):
        tld = tld.lower()
        if tld in _NON_TLD:
            continue
        if len(tld) != 2 and tld not in _GENERIC_TLDS:
            continue
        domain = full.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if domain not in domains:
            domains.append(domain)
    return domains


def _analyse_llm_response(text: str, user_domain: str) -> dict:
    """Turn one model's answer into the analytics row we store.

    Provider-agnostic on purpose: what differs between ChatGPT, Claude,
    Perplexity and Gemini is how the text is fetched, not how it is read. This
    was copied verbatim in each provider function, which is how two of them
    drifted; adding two more would have made four copies.
    """
    domain_clean = get_domain_from_url(user_domain)
    sld = domain_clean.split(".")[0] if domain_clean else ""
    mention_count = _count_brand_mentions(text, domain_clean, sld)

    third_party = [d for d in extract_domains(text) if d != domain_clean]

    # Prominence: where the brand first appears in the answer. Being named in the
    # opening sentence is worth more than a passing mention at the end, so score
    # 1..0 by the first hit's position; 0 when not mentioned at all.
    position_score = _first_mention_prominence(text, domain_clean, sld)

    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        sentiment = "positive"
    elif polarity < -0.1:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "response_text": text,
        "is_mention": mention_count > 0,
        "mention_count": mention_count,
        "citations": third_party,
        "sentiment": sentiment,
        "sentiment_score": round(polarity, 3),
        "context_summary": text[:200] + "..." if len(text) > 200 else text,
        "position_score": position_score,
    }


def _brand_patterns(domain_clean, sld):
    """Every way the brand can appear: its domain, and its bare name.

    One list, used by both the mention count and the prominence score, so the
    two can never disagree about what counts as an appearance.
    """
    patterns = []
    if domain_clean:
        patterns.append(rf"(?:https?://)?(?:www\.)?{re.escape(domain_clean)}(?![\w-])")
    # A model naming "Ahrefs" without linking ahrefs.com is still a mention.
    if sld and len(sld) >= 4 and sld != "www":
        terms = {sld}
        if sld.endswith("s") and len(sld) > 4:
            terms.add(sld[:-1])
        for term in sorted(terms):
            patterns.append(rf"\b{re.escape(term)}\b")
    return patterns


def count_merged_matches(text, patterns):
    """How many stretches of ``text`` any of ``patterns`` covers, counted once.

    The patterns handed to this overlap by design: "datablue.dev" satisfies the
    domain pattern and contains the bare brand name. Counting each pattern
    separately and adding the totals scored that one occurrence twice, which is
    why a five-mention answer reported ten. Merge the match spans instead, so
    one stretch of text is one mention however many patterns hit it.

    Public because the competitor scorer in ``llmtracker.brands`` counts rival
    names the same way. A second implementation of "how many times is this name
    in this answer" is how the brand's count and a competitor's count would come
    to disagree about what an occurrence is -- and a share-of-answers number
    built on two different definitions of a mention is not a comparison.
    """
    if not text or not patterns:
        return 0
    spans = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            spans.append((match.start(), match.end()))
    spans.sort()
    count = 0
    covered_to = -1
    for start, end in spans:
        if start >= covered_to:
            count += 1
            covered_to = end
        else:
            covered_to = max(covered_to, end)
    return count


def _count_brand_mentions(text, domain_clean, sld):
    """How many times the answer names the brand -- once per occurrence."""
    return count_merged_matches(text, _brand_patterns(domain_clean, sld))


def _first_mention_prominence(text, domain_clean, sld):
    """Score 1..0 by how early the brand first appears; 0 if it never does.

    A pure-Python heuristic over the answer we already have -- no extra API
    call. The earliest of the domain hit or the bare-brand-word hit wins.
    """
    if not text:
        return 0.0
    idxs = []
    for pattern in _brand_patterns(domain_clean, sld):
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            idxs.append(match.start())
    if not idxs:
        return 0.0
    first = min(idxs)
    return round(max(0.0, 1.0 - (first / max(len(text), 1))), 3)


def process_prompt_with_perplexity(prompt_text: str, user_domain: str, client, model: str = None) -> dict:
    """Ask Perplexity the prompt and read the answer.

    Perplexity serves an OpenAI-compatible API, so the same SDK drives it with
    a different base_url -- see get_perplexity_client. Its answers cite sources
    heavily, which is precisely what Geo Citations is looking for.
    """
    try:
        response = client.chat.completions.create(
            model=model or os.environ.get("PERPLEXITY_MODEL", "sonar"),
            messages=[
                {"role": "system", "content": "Answer the question directly and cite your sources."},
                {"role": "user", "content": prompt_text},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        text = response.choices[0].message.content
        return _analyse_llm_response(text, user_domain)
    except Exception as e:
        logger.error(f"Error processing prompt with Perplexity: {str(e)}")
        raise e


def process_prompt_with_gemini(prompt_text: str, user_domain: str, client, model: str = None) -> dict:
    """Ask Gemini the prompt and read the answer.

    `client` here is the configured google.generativeai module rather than a
    client object -- that library configures globally, unlike the other three.
    """
    try:
        model = client.GenerativeModel(model or os.environ.get("GEMINI_MODEL", "gemini-3.6-flash"))
        response = model.generate_content(prompt_text)
        text = getattr(response, "text", "") or ""
        if not text:
            raise ValueError("Gemini returned no text")
        return _analyse_llm_response(text, user_domain)
    except Exception as e:
        logger.error(f"Error processing prompt with Gemini: {str(e)}")
        raise e


def process_prompt_with_chatgpt(prompt_text: str, user_domain: str, client, model: str = None) -> dict:
    """
    Process a single prompt with ChatGPT and return structured analytics.
    """
    try:
        response = client.chat.completions.create(
            model=model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are ChatGPT, a helpful assistant."},
                {"role": "user", "content": prompt_text}
            ],
            temperature=0.7,
            top_p=1, 
            frequency_penalty=0,
            presence_penalty=0,
            max_tokens=1024
        )

        text = response.choices[0].message.content
        return _analyse_llm_response(text, user_domain)
    except Exception as e:
        logger.error(f"Error processing prompt with ChatGPT: {str(e)}")
        raise e


def process_prompt_with_claude(prompt_text: str, user_domain: str, client, model: str = None) -> dict:
    """
    Process a single prompt with Claude and return structured analytics similar to ChatGPT.
    """
    try:
        message = client.messages.create(
            model=model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
            max_tokens=300,
            messages=[
                {"role": "user", "content": prompt_text}
            ]
        )

        # Extract response text per Anthropic SDK structure
        text = ""
        try:
            text = message.content[0].text
        except Exception:
            text = str(message)

        return _analyse_llm_response(text, user_domain)
    except Exception as e:
        logger.error(f"Error processing prompt with Claude: {str(e)}")
        raise e


def process_llm_prompts_automatically(user_id=None, group_id=None, prompt=None):
    """Process one queued prompt, oldest first.

    One at a time, because a prompt in flight is marked SCHD and a second
    worker would pick it up again.

    `user_id` and `group_id` scope both the in-flight check and the pick. The
    cron passes neither and works the whole queue; the interactive Geo
    Citations run passes both so it never spends one project's keys while
    processing another project's prompts.
    """
    try:
        # Check if any prompt is currently being processed (SCHD status)
        scheduled_prompts = LLMPrompt.objects.filter(track_status="SCHD")
        if user_id:
            scheduled_prompts = scheduled_prompts.filter(fk_user_id=user_id)
        if group_id:
            scheduled_prompts = scheduled_prompts.filter(fk_group_id=group_id)
        if scheduled_prompts.exists():
            logger.info("A prompt is already being processed. Skipping automatic processing.")
            return {
                "status": "skipped",
                "message": "Another prompt is currently being processed"
            }

        # Interactive reruns pass one completed prompt as a readiness probe.
        # Scheduled work keeps using the ordinary INIT/FAIL queue.
        init_prompt = prompt
        if init_prompt is None:
            _queue_ = LLMPrompt.objects.filter(track_status__in=["INIT", "FAIL"])
            if user_id:
                _queue_ = _queue_.filter(fk_user_id=user_id)
            if group_id:
                _queue_ = _queue_.filter(fk_group_id=group_id)
            init_prompt = _queue_.order_by("created_date").first()
        if not init_prompt:
            logger.info("No prompts with INIT or FAIL status found.")
            return {
                "status": "no_prompts",
                "message": "No prompts to process"
            }

        # Mark the prompt as scheduled
        with transaction.atomic():
            init_prompt.track_status = "SCHD"
            init_prompt.track_message = "Processing started"
            init_prompt.save()

        # Keep the current result until at least one provider produces a new
        # result. A quota/auth outage must never erase previously useful data.
        current_analytics = LLMPromptAnalytics.objects.filter(fk_prompt=init_prompt)
        previous_analytics = list(current_analytics)

        logger.info(f"Processing prompt {init_prompt.prompt_id}: {init_prompt.prompt[:50]}...")

        try:
            # Get user domain from the group settings
            user_domain = init_prompt.fk_group.domain_name
            if not user_domain:
                user_domain = "example.com"  # Fallback if no domain is set

            # Bill each provider call to the account that owns the prompt.
            # Without _uid_ every account's Geo Citations run spent the
            # operator's instance key.
            _uid_ = getattr(init_prompt, "fk_user_id", None)

            # One table rather than a block per provider. ChatGPT used to be
            # mandatory -- its client was built outside the try and raised, so
            # an account holding only a Gemini key got no analysis at all and
            # the whole prompt was marked FAIL. Under BYOK an account
            # configures only the models it wants tracked, so every provider is
            # optional and a run succeeds if any one of them answers.
            _providers_ = (
                ("chatgpt", "ChatGPT", get_openai_client, process_prompt_with_chatgpt, "chatgpt_model"),
                ("claude", "Claude", get_anthropic_client, process_prompt_with_claude, "claude_model"),
                ("perplexity", "Perplexity", get_perplexity_client, process_prompt_with_perplexity, "perplexity_model"),
                ("gemini", "Gemini", get_gemini_client, process_prompt_with_gemini, "gemini_model"),
            )

            # The account's per-provider model override, if any. Blank falls back
            # to the provider's instance default inside each process_* function.
            from serp.models import Accountusage
            _acc_ = Accountusage.objects.filter(fb_user_id=_uid_).first() if _uid_ else None

            succeeded = 0
            pending_analytics = []
            provider_failures = []

            for _provider_, _name_, _make_client_, _run_, _model_attr_ in _providers_:
                if not resolve_key(_uid_, _provider_):
                    continue

                try:
                    _client_ = _make_client_(_uid_)
                    _model_ = (getattr(_acc_, _model_attr_, "") or "").strip() or None
                    _result_ = _run_(init_prompt.prompt, user_domain, _client_, model=_model_)
                    pending_analytics.append({
                        "fk_prompt": init_prompt,
                        "model": _name_,
                        "track_status": "DONE",
                        "position": 0,
                        "is_mention": _result_["is_mention"],
                        "mention_count": _result_["mention_count"],
                        "citations": _result_["citations"],
                        "sentiment": _result_["sentiment"],
                        "sentiment_score": _result_["sentiment_score"],
                        "context_summary": _result_["context_summary"],
                        "response_text": _result_.get("response_text", ""),
                        "position_score": _result_.get("position_score", 0.0),
                    })
                    succeeded += 1
                except Exception as _perr_:
                    _safe_error_ = describe_provider_failure(_provider_, _perr_)
                    provider_failures.append(_safe_error_)
                    pending_analytics.append({
                        "fk_prompt": init_prompt,
                        "model": _name_,
                        "track_status": "FAIL",
                        "position": 0,
                        "is_mention": False,
                        "mention_count": 0,
                        "citations": [],
                        "sentiment": "neutral",
                        "sentiment_score": 0.0,
                        "context_summary": "",
                        "track_message": _safe_error_,
                    })

            if not succeeded:
                failure_message = (
                    "; ".join(provider_failures)
                    if provider_failures
                    else "No AI provider key configured. Add one under Settings -> AI Keys."
                )
                retained = bool(previous_analytics)
                with transaction.atomic():
                    init_prompt.track_status = "DONE" if retained else "FAIL"
                    init_prompt.track_message = (
                        "Latest analysis failed; previous results retained. " + failure_message
                        if retained
                        else failure_message
                    )
                    init_prompt.save()

                return {
                    "status": "error",
                    "message": init_prompt.track_message,
                    "prompt_id": str(init_prompt.prompt_id),
                    "previous_results_retained": retained,
                }

            # Only a successful run may replace the current provider rows.
            first_analytics = None
            with transaction.atomic():
                current_analytics.delete()
                for analytics_data in pending_analytics:
                    _row_ = LLMPromptAnalytics.objects.create(**analytics_data)
                    if analytics_data["track_status"] == "DONE" and first_analytics is None:
                        first_analytics = _row_

            # Mark the prompt as completed after attempting every provider
            with transaction.atomic():
                init_prompt.track_status = "DONE"
                init_prompt.track_message = (
                    f"Processed by {succeeded} configured provider"
                    f"{'s' if succeeded != 1 else ''}"
                )
                init_prompt.save()

            # Record today's aggregate for this group so the page can chart the
            # mention rate/sentiment/prominence over time.
            try:
                _write_group_snapshot(init_prompt.fk_group_id)
            except Exception as _snap_err_:
                logger.error(f"snapshot write failed: {_snap_err_}")

            # Score the project's tracked rivals against the answer just stored.
            # Reads text, calls no provider, spends nothing. Failing here must
            # not fail a run that already succeeded, so it is caught like the
            # snapshot above.
            try:
                from llmtracker.brands import score_group_competitors

                score_group_competitors(init_prompt.fk_group)
            except Exception as _rival_err_:
                logger.error(f"competitor scoring failed: {_rival_err_}")

            logger.info(f"Successfully processed prompt {init_prompt.prompt_id}")

            return {
                "status": "success",
                "message": "Prompt processed successfully",
                "prompt_id": str(init_prompt.prompt_id),
                "analytics_id": str(first_analytics.analytics_id),
            }

        except Exception as e:
            # Unexpected failures still preserve any previous provider rows.
            retained = bool(previous_analytics)
            with transaction.atomic():
                init_prompt.track_status = "DONE" if retained else "FAIL"
                init_prompt.track_message = (
                    "Latest analysis failed; previous results retained."
                    if retained
                    else "Analysis failed unexpectedly. Try again."
                )
                init_prompt.save()

            logger.error(f"Failed to process prompt {init_prompt.prompt_id}: {str(e)}")
            
            return {
                "status": "error",
                "message": init_prompt.track_message,
                "prompt_id": str(init_prompt.prompt_id),
                "previous_results_retained": retained,
            }

    except Exception as e:
        logger.error(f"Error in automatic processing: {str(e)}")
        return {
            "status": "error",
            "message": f"System error: {str(e)}"
        }


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def add_prompt(request):
    """Add new prompts for all enabled LLM services from Settings with optional new fields"""
    try:
        required_fields = ["userid", "groupid", "prompts"]
        validation_required = all(field in request.data for field in required_fields)

        if not validation_required:
            return JsonResponse({"status": "false", "message": "Something went wrong"})

        userid = request.data["userid"].strip()
        groupid = request.data["groupid"].strip()
        prompts_input = request.data["prompts"]
        
        # Ensure prompts is always an array
        if isinstance(prompts_input, str):
            prompts = [prompts_input.strip()]
        elif isinstance(prompts_input, list):
            prompts = [str(p).strip() for p in prompts_input if p]
        else:
            return JsonResponse({"status": "false", "message": "Something went wrong"})
        
        if not prompts:
            return JsonResponse({"status": "false", "message": "Something went wrong"})

        # Validate user and group exist
        try:
            user_instance = Account.objects.get(id=userid)
            group_instance = Groups.objects.get(id=groupid, fk_user_id=userid)
        except Account.DoesNotExist:
            return JsonResponse({"status": "false", "message": "Invalid user"})
        except Groups.DoesNotExist:
            return JsonResponse({"status": "false", "message": "Invalid group"})

        created_prompts = []
        # Create prompts for each prompt text (one LLMPrompt per text)
        for prompt_text in prompts:
            # Create the main LLMPrompt record
            new_prompt = LLMPrompt()
            new_prompt.fk_user = user_instance
            new_prompt.fk_group = group_instance
            new_prompt.prompt = prompt_text
            new_prompt.track_status = "INIT"  # Set initial status
            new_prompt.save()
            
            # Only create the prompt record, analytics will be created during processing
            created_prompts.append({
                "promptId": str(new_prompt.prompt_id),
                "prompt": prompt_text,
                "track_status": new_prompt.track_status,
                "created_date": new_prompt.created_date.strftime("%Y-%m-%d %H:%M:%S")
            })

        return JsonResponse({
            "status": "true", 
            "message": "Saved successfully",
            "total_prompts": len(created_prompts)
        })

    except Exception as e:
        print(f"Error adding prompt: {str(e)}")
        return JsonResponse({"status": "false", "message": f"Error: {str(e)}"})


@api_view(["POST"])
def list_prompts(request):
    """List prompts with simple search filter"""
    try:
        required_fields = ["userid", "groupid"]
        validation_required = all(field in request.data for field in required_fields)

        if not validation_required:
            return JsonResponse({"status": "false", "message": "Invalid Params"})

        userid = request.data["userid"].strip()
        groupid = request.data["groupid"].strip()
        search_query = request.data.get("search", "").strip()

        # Validate user and group exist
        try:
            user_instance = Account.objects.get(id=userid)
            group_instance = Groups.objects.get(id=groupid, fk_user=user_instance)
        except Account.DoesNotExist:
            return JsonResponse({"status": "false", "message": "Invalid user"})
        except Groups.DoesNotExist:
            return JsonResponse({"status": "false", "message": "Invalid group"})

        # Build query for prompts
        query = Q(fk_user=user_instance, fk_group=group_instance)
        
        if search_query:
            query &= Q(prompt__icontains=search_query)

        
        # Get prompts with their analytics data
        prompts = LLMPrompt.objects.filter(query).prefetch_related('analytics').order_by('created_date')
        
        result_data = []
        for prompt in prompts:
            # Check if prompt is being processed
            is_processing = prompt.track_status in ["SCHD", "INIT"]
            
            if is_processing:
                # For processing prompts, show processing status
                result_data.append({
                    "prompt_id": str(prompt.prompt_id),
                    "prompt": prompt.prompt,
                    "is_mentioned_in_chatgpt": False,
                    "is_mentioned_in_claude": False,
                    "average_position": 0,
                    "tracked_at": "",
                    "track_status": prompt.track_status,
                    "track_message": prompt.track_message or "Processing",
                    "total_citations": 0,
                    "chatgpt_analytics_id": None,
                    "claude_analytics_id": None,
                    "chatgpt_citations_count": 0,
                    "claude_citations_count": 0
                })
            else:
                # For completed prompts, get analytics data
                analytics = prompt.analytics.all()
                
                # Get position from analytics (use the first non-zero position found)
                average_position = 0
                for a in analytics:
                    if a.position > 0:
                        average_position = a.position
                        break
                
                # Get the latest analytics record
                latest_analytics = None
                if analytics:
                    latest_analytics = max(analytics, key=lambda a: a.modified_date)
                latest_modified = latest_analytics.modified_date if latest_analytics else prompt.modified_date
                
                # Check ChatGPT and Claude mentions from analytics
                
                # Collect citations data
                all_citations = []
                # Per-model rollups, keyed by model name rather than a pair of
                # variables each. Two providers were hardcoded here; Perplexity
                # and Gemini would have needed a third and fourth of every line.
                _MODELS_ = ("ChatGPT", "Claude", "Perplexity", "Gemini")
                per_model = {m: {"mentioned": False, "citations": [], "latest": None}
                             for m in _MODELS_}

                for a in analytics:
                    bucket = per_model.get(a.model)
                    if bucket is None:
                        continue
                    if a.is_mention:
                        bucket["mentioned"] = True
                    if a.citations:
                        all_citations.extend(a.citations)
                        bucket["citations"].extend(a.citations)
                    if (bucket["latest"] is None) or (a.modified_date > bucket["latest"].modified_date):
                        bucket["latest"] = a

                unique_citations = list(set(all_citations))

                row = {
                    "prompt_id": str(prompt.prompt_id),
                    "prompt": prompt.prompt,
                    "average_position": average_position,
                    "tracked_at": latest_modified.strftime("%b %d, %Y"),
                    "track_status": prompt.track_status,
                    "track_message": prompt.track_message,
                    "total_citations": len(unique_citations),
                }
                for m in _MODELS_:
                    key = m.lower()
                    b = per_model[m]
                    row[f"is_mentioned_in_{key}"] = b["mentioned"]
                    # Whether this model actually ran for the prompt (has an
                    # analytics row). Without it the table can't tell "ran, not
                    # mentioned" (a real ✗) from "no key for this model, never
                    # ran" (should read as not-tracked, not a failure).
                    row[f"ran_{key}"] = b["latest"] is not None
                    row[f"{key}_analytics_id"] = str(b["latest"].analytics_id) if b["latest"] else None
                    row[f"{key}_citations_count"] = len(set(b["citations"]))

                # Aggregate signal for the list row, so mention/sentiment show
                # without opening the detail. mentioned_count / models_ran give
                # "N of M models"; overall_sentiment is brand-safety-first --
                # any negative among the models that mentioned you wins, so the
                # worst case is never hidden behind an average.
                row["mentioned_count"] = sum(1 for m in _MODELS_ if per_model[m]["mentioned"])
                row["models_ran"] = sum(1 for m in _MODELS_ if per_model[m]["latest"] is not None)
                _ment_sents = [
                    per_model[m]["latest"].sentiment
                    for m in _MODELS_
                    if per_model[m]["mentioned"] and per_model[m]["latest"] is not None
                ]
                if not _ment_sents:
                    row["overall_sentiment"] = "na"
                elif "negative" in _ment_sents:
                    row["overall_sentiment"] = "negative"
                elif "positive" in _ment_sents:
                    row["overall_sentiment"] = "positive"
                else:
                    row["overall_sentiment"] = "neutral"

                result_data.append(row)

        return JsonResponse({
            "status": "true", 
            "data": result_data
        })
    except Exception as e:
        print(f"Error listing prompts: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def delete_prompts(request):
    """Delete multiple prompts with prompt_ids"""
    try:
        required_fields = ["userid", "prompt_ids"]
        validation_required = all(field in request.data for field in required_fields)

        if not validation_required:
            return JsonResponse({"status": "false", "message": "Invalid Params - userid and prompt_ids are required"})

        userid = request.data["userid"].strip()
        prompt_ids = request.data["prompt_ids"]

        # Validate user exists
        try:
            user_instance = Account.objects.get(id=userid)
        except Account.DoesNotExist:
            return JsonResponse({"status": "false", "message": "Invalid user"})

        # Ensure prompt_ids is a list and not empty
        if not isinstance(prompt_ids, list):
            return JsonResponse({"status": "false", "message": "prompt_ids must be a list"})
        
        if not prompt_ids:
            return JsonResponse({"status": "false", "message": "prompt_ids list cannot be empty"})

        # Find and delete the prompts and their analytics
        deleted_count = 0
        
        for prompt_id in prompt_ids:
            try:
                # Convert string to UUID if needed
                if isinstance(prompt_id, str):
                    import uuid
                    try:
                        prompt_id = uuid.UUID(prompt_id)
                    except ValueError:
                        continue
                
                # Find the prompt
                prompt = LLMPrompt.objects.get(prompt_id=prompt_id, fk_user=user_instance)
                
                # Get all analytics for this prompt before deletion
                analytics_list = LLMPromptAnalytics.objects.filter(fk_prompt=prompt)
                
                # Delete all analytics first (CASCADE should handle this, but being explicit)
                analytics_list.delete()
                
                # Then delete the prompt
                prompt.delete()
                
                deleted_count += 1
                print(f"Successfully deleted prompt {prompt_id}")
                
            except LLMPrompt.DoesNotExist:
                print(f"Prompt {prompt_id} not found for user {userid}")
            except Exception as e:
                print(f"Error deleting prompt {prompt_id}: {e}")

        if deleted_count == 0:
            return JsonResponse({
                "status": "false", 
                "message": "No prompts were deleted"
            })

        return JsonResponse({
            "status": "true", 
            "message": "Deleted successfully"
        })

    except Exception as e:
        print(f"Error deleting prompts: {str(e)}")
        return JsonResponse({"status": "false", "message": f"Error: {str(e)}"})


def get_openai_client(user_id=None):
    """OpenAI client billed to `user_id`'s own key where one is stored.

    Passing no user_id keeps the old instance-key behaviour, which is what the
    management/debug entry points want. Every scheduled path passes one --
    without it, one account's analysis is charged to the operator.
    """
    from account.aikeys import resolve_key

    key = resolve_key(user_id, "chatgpt")
    if not key:
        raise Exception("No ChatGPT API key for this account")
    try:
        return openai.OpenAI(api_key=key)
    except Exception as e:
        raise Exception(f"Failed to initialize OpenAI client: {str(e)}")


def get_perplexity_client(user_id=None):
    """Perplexity client billed to `user_id`'s own key.

    Perplexity is OpenAI-compatible, so this is the openai SDK pointed at their
    host rather than a second library.
    """
    from account.aikeys import resolve_key

    key = resolve_key(user_id, "perplexity")
    if not key:
        raise Exception("No Perplexity API key for this account")
    try:
        return openai.OpenAI(api_key=key, base_url="https://api.perplexity.ai")
    except Exception as e:
        raise Exception(f"Failed to initialize Perplexity client: {str(e)}")


def get_gemini_client(user_id=None):
    """Configured google.generativeai module for `user_id`'s own key.

    Returns the MODULE, not a client: google-generativeai configures globally.
    That also makes it order-dependent -- configure immediately before use, so
    two accounts processed in sequence cannot inherit each other's key.
    """
    from account.aikeys import resolve_key

    key = resolve_key(user_id, "gemini")
    if not key:
        raise Exception("No Gemini API key for this account")
    try:
        import google.generativeai as genai

        genai.configure(api_key=key)
        return genai
    except Exception as e:
        raise Exception(f"Failed to initialize Gemini client: {str(e)}")


def get_anthropic_client(user_id=None):
    """Anthropic client billed to `user_id`'s own key where one is stored."""
    from account.aikeys import resolve_key

    key = resolve_key(user_id, "claude")
    if not key:
        raise Exception("No Claude API key for this account")
    try:
        return anthropic.Anthropic(api_key=key)
    except Exception as e:
        raise Exception(f"Failed to initialize Anthropic client: {str(e)}")


@api_view(["POST"])
def list_citations(request):
    """Return sorted, deduplicated citations and total count for a user's group.

    Body params:
    - userid (required)
    - groupid (required)
    - search (optional; filters prompts containing text)
    - model (optional; one of ChatGPT, Claude, Gemini, Perplexity, DeepSeek)
    - analytics_id (optional; limits citations to a single analytics record)
    """
    try:
        required_fields = ["userid", "groupid"]
        validation_required = all(field in request.data for field in required_fields)

        if not validation_required:
            return JsonResponse({"status": "false", "message": "Invalid Params"})

        userid = request.data["userid"].strip()
        groupid = request.data["groupid"].strip()
        search_query = request.data.get("search", "").strip()
        model_filter = request.data.get("model", "").strip()
        analytics_id_str = request.data.get("analytics_id", "").strip()

        # Validate user and group
        try:
            user_instance = Account.objects.get(id=userid)
            group_instance = Groups.objects.get(id=groupid, fk_user=user_instance)
        except Account.DoesNotExist:
            return JsonResponse({"status": "false", "message": "Invalid user"})
        except Groups.DoesNotExist:
            return JsonResponse({"status": "false", "message": "Invalid group"})

        # If analytics_id is provided, return citations only for that analytics record
        if analytics_id_str:
            try:
                import uuid
                analytics_uuid = uuid.UUID(analytics_id_str)
            except ValueError:
                return JsonResponse({"status": "false", "message": "Invalid analytics_id"})

            try:
                analytics = LLMPromptAnalytics.objects.get(
                    analytics_id=analytics_uuid,
                    fk_prompt__fk_user=user_instance,
                    fk_prompt__fk_group=group_instance,
                )
            except LLMPromptAnalytics.DoesNotExist:
                return JsonResponse({"status": "false", "message": "Analytics not found"})

            # DEPRECATED. `citations` matches domain-shaped substrings in prose,
            # not sources any model cited -- these answers contain no URLs at
            # all. It needs a dot and a valid TLD, so "Bright Data" can never
            # appear in it, and across this project's eight answers it holds one
            # value, scraped out of a markdown heading. Kept because other
            # callers may still read it; the detail page reads `brands_named`.
            citations = sorted(list(set(analytics.citations or [])))

            # The rival brands THIS answer actually named, from llmtracker/brands.py.
            #
            # Three fields, not one, because an empty `brands_named` means either
            # "no tracked rival was named here" or "this answer was never
            # scanned" -- and rendering those two identically is the defect this
            # codebase has repeated more than any other.
            from llmtracker.models import LLMCompetitor, LLMCompetitorAnalytics

            tracked = {
                competitor.competitor_id: competitor
                for competitor in LLMCompetitor.objects.filter(fk_group=group_instance)
                if competitor.is_tracked  # djongo cannot filter a bool in SQL
            }
            scored = list(LLMCompetitorAnalytics.objects.filter(fk_analytics=analytics))
            brands_named = sorted(
                (
                    {
                        "name": tracked[record.fk_competitor_id].name,
                        "mentions": int(record.mention_count or 0),
                    }
                    for record in scored
                    if record.is_mentioned and record.fk_competitor_id in tracked
                ),
                key=lambda item: (-item["mentions"], item["name"]),
            )

            data = {
                # `score_group_competitors` writes one row per (tracked
                # competitor, answer) whether or not the name matched -- 19
                # rivals x 8 answers = 152 rows for this group, verified. So a
                # single row is proof this answer was looked at, and no row is
                # proof of nothing: the scorer may never have run, or the group
                # may track no rivals for it to write about.
                #
                # Hence True or None, and never False. False would be a claim --
                # "we looked and there was nothing" -- that this expression
                # cannot support, and it would collapse into one state the two
                # the frontend has to tell apart. `brands_tracked` carries the
                # no-rivals-configured case on its own.
                #
                # A `last_scored_at` on the group would make this a fact rather
                # than an inference. Until it exists, unknown stays unknown.
                "brands_named": brands_named,
                "brands_scored": True if scored else None,
                "brands_tracked": len(tracked),
                "analytics_id": str(analytics.analytics_id),
                "model": analytics.model,
                "prompt": analytics.fk_prompt.prompt,
                "prompt_id": str(analytics.fk_prompt.prompt_id),
                "total_citations": len(citations),
                "citations": citations,
                # The point of Geo Citations is what the model SAID about you,
                # not just which URLs it cited. Carry the analysis through so
                # the detail view can show it.
                "is_mention": analytics.is_mention,
                "mention_count": analytics.mention_count,
                "sentiment": analytics.sentiment,
                "sentiment_score": analytics.sentiment_score,
                "context_summary": analytics.context_summary,
                "response_text": analytics.response_text or analytics.context_summary,
                "position_score": analytics.position_score,
            }
        else:
            # Filter prompts
            query = Q(fk_user=user_instance, fk_group=group_instance)
            if search_query:
                query &= Q(prompt__icontains=search_query)

            prompts = LLMPrompt.objects.filter(query).prefetch_related('analytics').order_by('created_date')

            # Aggregate citations
            all_citations = set()

            for prompt in prompts:
                for a in prompt.analytics.all():
                    if model_filter and a.model != model_filter:
                        continue
                    if a.citations:
                        for c in a.citations:
                            all_citations.add(c)

            data = {
                "analytics_id": None,
                "total_citations": len(all_citations),
                "citations": sorted(list(all_citations))
            }

        return JsonResponse({"status": "true", "data": data})

    except Exception as e:
        logger.error(f"Error listing citations: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})


def _write_group_snapshot(group_id):
    """Upsert today's LLMMetricSnapshot for a group from its DONE analytics.

    One row per group per day: re-running prompts through the day updates the
    same row rather than spawning many, so the trend chart shows one point per
    day. Averages are taken over mentioning answers only -- sentiment and
    prominence are meaningless where the brand was not named.
    """
    from django.utils import timezone
    today = timezone.now().date()
    rows = list(LLMPromptAnalytics.objects.filter(
        fk_prompt__fk_group_id=group_id, track_status="DONE"))
    measured = len(rows)
    if not measured:
        return
    mentions = [r for r in rows if r.is_mention]
    mention_rate = round(len(mentions) / measured, 3)
    avg_sentiment = round(sum(r.sentiment_score for r in mentions) / len(mentions), 3) if mentions else 0.0
    avg_position = round(sum((r.position_score or 0.0) for r in mentions) / len(mentions), 3) if mentions else 0.0
    total_citations = sum(len(r.citations or []) for r in rows)
    snap = LLMMetricSnapshot.objects.filter(fk_group_id=group_id, snapshot_date=today).first()
    if snap:
        snap.prompts_measured = measured
        snap.mention_rate = mention_rate
        snap.avg_sentiment = avg_sentiment
        snap.avg_position = avg_position
        snap.total_citations = total_citations
        snap.save()
    else:
        LLMMetricSnapshot.objects.create(
            fk_group_id=group_id, snapshot_date=today, prompts_measured=measured,
            mention_rate=mention_rate, avg_sentiment=avg_sentiment,
            avg_position=avg_position, total_citations=total_citations)


def _resolve_group(request):
    """Validate userid+groupid from the body; return (group, error_response)."""
    userid = request.data.get("userid", "").strip()
    groupid = request.data.get("groupid", "").strip()
    if not userid or not groupid:
        return None, JsonResponse({"status": "false", "message": "Invalid Params"})
    try:
        user = Account.objects.get(id=userid)
        group = Groups.objects.get(id=groupid, fk_user=user)
    except (Account.DoesNotExist, Groups.DoesNotExist):
        return None, JsonResponse({"status": "false", "message": "Invalid user or group"})
    return group, None


@api_view(["POST"])
def geo_trend(request):
    """Geo Citations metrics over time for a group (one point per day)."""
    try:
        group, err = _resolve_group(request)
        if err:
            return err
        snaps = LLMMetricSnapshot.objects.filter(fk_group_id=group.id).order_by("snapshot_date")
        series = [{
            "date": s.snapshot_date.isoformat(),
            "mention_rate": s.mention_rate,
            "avg_sentiment": s.avg_sentiment,
            "avg_position": s.avg_position,
            "total_citations": s.total_citations,
            "prompts_measured": s.prompts_measured,
        } for s in snaps]
        return JsonResponse({"status": "true", "data": {"series": series}})
    except Exception as e:
        logger.error(f"Error in geo_trend: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
def geo_competitors(request):
    """The rival brands tracked for a group, and who won the answers it lost.

    Read-only and cheap: it reports stored ``LLMCompetitorAnalytics`` scores and
    runs no extraction. Body params: userid, groupid, plus optional
    `suggest=true` to include brands detected in stored answers that are not
    tracked yet -- that flag DOES re-read every answer, so it is opt-in.

    A group with no Geo data answers with empty lists and zeroes, which is a
    valid state and not an error.
    """
    try:
        group, err = _resolve_group(request)
        if err:
            return err
        from llmtracker.brands import group_competitor_summary, suggest_group_competitors

        data = group_competitor_summary(group)
        wants_suggestions = str(request.data.get("suggest", "")).lower() in (
            "1", "true", "yes",
        )
        data["suggestions"] = (
            suggest_group_competitors(group) if wants_suggestions else []
        )
        data["suggestions_included"] = wants_suggestions
        return JsonResponse({"status": "true", "data": data})
    except Exception as e:
        logger.error(f"Error in geo_competitors: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def geo_competitor_manage(request):
    """Add, retire, restore or delete one tracked competitor, then re-score.

    SPENDS NOTHING. Scoring re-reads answers already stored, so adding a rival
    scores the whole of the project's history for it retroactively -- which is
    the point of keeping ``response_text``.

    Body params: userid, groupid, action in add|track|untrack|delete, plus
    `name` (for add) or `competitor_id` (for the rest), and optional `url`.
    A competitor added or restored here becomes `source="user"`, so a later
    detection pass cannot overwrite the decision.
    """
    try:
        group, err = _resolve_group(request)
        if err:
            return err
        from llmtracker.models import LLMCompetitor
        from llmtracker.brands import group_competitor_summary, score_group_competitors

        action = (request.data.get("action") or "").strip().lower()
        if action not in ("add", "track", "untrack", "delete"):
            return JsonResponse({"status": "false", "message": "Invalid action"})

        if action == "add":
            name = (request.data.get("name") or "").strip()
            if not name or len(name) > 120:
                return JsonResponse({"status": "false", "message": "Invalid name"})
            url = (request.data.get("url") or "").strip()[:255]
            existing = next(
                (row for row in LLMCompetitor.objects.filter(fk_group=group)
                 if row.name.lower() == name.lower()),
                None,
            )
            if existing:
                # Re-adding a name the user had retired is how they restore it.
                existing.is_tracked = True
                existing.source = "user"
                if url:
                    existing.url = url
                existing.save(update_fields=["is_tracked", "source", "url"])
            else:
                LLMCompetitor.objects.create(
                    fk_group=group, name=name, url=url, source="user",
                )
        else:
            competitor_id = (request.data.get("competitor_id") or "").strip()
            try:
                competitor = LLMCompetitor.objects.get(
                    competitor_id=uuid.UUID(competitor_id), fk_group=group,
                )
            except (ValueError, LLMCompetitor.DoesNotExist):
                return JsonResponse({"status": "false", "message": "Invalid competitor"})
            if action == "delete":
                competitor.delete()
            else:
                # Keeping or rejecting a suggestion is a decision, so the row
                # stops being "detected" either way -- otherwise the next scan
                # would propose a name the user has already turned down.
                competitor.is_tracked = action == "track"
                competitor.source = "user"
                competitor.save(update_fields=["is_tracked", "source"])

        score_group_competitors(group)
        return JsonResponse({"status": "true", "data": group_competitor_summary(group)})
    except Exception as e:
        logger.error(f"Error in geo_competitor_manage: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def geo_detect_competitors(request):
    """Re-read every stored answer, propose rival brands, and score them.

    SPENDS NOTHING -- no provider is called. This is the back-fill: the brands
    the models named have been sitting in ``response_text`` unread since the
    answers were paid for.
    """
    try:
        group, err = _resolve_group(request)
        if err:
            return err
        from llmtracker.brands import group_competitor_summary, refresh_group_competitors

        summary = refresh_group_competitors(group)
        data = group_competitor_summary(group)
        data["detected"] = summary["seed"]
        data["scored"] = summary["score"]
        return JsonResponse({"status": "true", "data": data})
    except Exception as e:
        logger.error(f"Error in geo_detect_competitors: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
def geo_share_of_voice(request):
    """Answer coverage + top cited sources across a group's answers.

    Reuses data already captured -- no extra LLM calls.

    The headline is **answer coverage**: of the model answers measured, the
    share that named the brand at all. It is the same quantity the trend chart
    plots as `mention_rate`, and it is countable from the two numbers shown
    beside it ("2 of 8 answers").

    This replaces a "share of voice" that divided the brand's mention count by
    that count plus the number of cited third-party domains. Those are not
    comparable quantities -- one counts occurrences inside answers, the other
    counts distinct domains across them -- so the percentage tracked nothing.
    It also moved the wrong way: cleaning bogus citations out of the denominator
    pushed the reported "share" *up*, from 76.2% to 91.7% on the same answers.
    A real share of voice needs a competitor set to divide against, which Geo
    Citations does not have; the cited-source list below carries that signal
    honestly instead, as counts rather than a ratio.
    """
    try:
        group, err = _resolve_group(request)
        if err:
            return err
        # Imported here, not at module level: geo_summary reads
        # get_domain_from_url out of this module, and a top-level import both
        # ways is a cycle. The mention summary is meaningful even when no model
        # cites sources (e.g. a Gemini-only account) -- how many answers named
        # the brand, across how many models, and the overall tone.
        from llmtracker.geo_summary import geo_answer_summary

        return JsonResponse({"status": "true", "data": geo_answer_summary(group)})
    except Exception as e:
        logger.error(f"Error in geo_share_of_voice: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
def generate_prompts(request):
    """Suggest realistic tracking prompts for a group's domain via one AI call.

    Uses whichever provider key the account already has (the same BYOK keys Geo
    Citations runs on), so it costs the account one short completion and no new
    dependency. Returns suggestions; the user chooses which to add.
    """
    try:
        group, err = _resolve_group(request)
        if err:
            return err
        topic = (request.data.get("topic", "") or "").strip()
        domain = get_domain_from_url(group.domain_name) or group.domain_name or ""
        uid = group.fk_user_id
        instruction = (
            "You generate short, natural search prompts a real person would type "
            "into an AI assistant. Given a brand/domain and an optional topic, "
            "return 8 diverse prompts that could surface that brand or its "
            "competitors. Do NOT name the brand in the prompts -- they must be "
            "generic queries the brand would want to appear in. Return ONLY a "
            "JSON array of strings, no prose."
        )
        ask = f"Domain: {domain}\nTopic: {topic or 'general'}\nReturn the JSON array."
        text = _one_shot_completion(uid, instruction, ask)
        suggestions = _parse_prompt_list(text)
        return JsonResponse({"status": "true", "data": {"suggestions": suggestions}})
    except (NoAIProviderConfigured, AICompletionFailed) as exc:
        return JsonResponse({"status": "false", "message": str(exc)})
    except Exception as e:
        logger.error(f"Error in generate_prompts: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})


def _one_shot_completion(uid, system_text, user_text):
    """Run one short completion through the shared account BYOK router."""
    return generate_text(
        uid, system_text, user_text, max_tokens=512, temperature=0.8
    )


def _parse_prompt_list(text):
    """Pull a list of prompt strings out of a model reply (JSON array or lines)."""
    if not text:
        return []
    try:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end != -1 and end > start:
            arr = json.loads(text[start:end + 1])
            out = [str(x).strip() for x in arr if str(x).strip()]
            if out:
                return out[:12]
    except Exception:
        pass
    # Fallback: split lines, strip bullets/numbering.
    lines = []
    for ln in text.splitlines():
        ln = re.sub(r"^\s*(?:[-*\d\.\)]+)\s*", "", ln).strip().strip('"')
        if len(ln) >= 8:
            lines.append(ln)
    return lines[:12]


@csrf_exempt
@cron_only
@api_view(["GET"])
@permission_classes((AllowAny,))
def manage_prompts(request):
    """Scheduler entry point. AllowAny is deliberate -- a cron has no session --
    but @cron_only above it demands the instance's CRON_TOKEN, so this is not a
    public URL. Without the token an anonymous GET here would pick up queued
    prompts and spend the account's OpenAI/Anthropic credits.
    """
    """Automatically process LLM prompts with INIT status using ChatGPT."""
    try:
        # Trigger automatic processing
        result = process_llm_prompts_automatically()
        
        if result["status"] == "success":
            return JsonResponse({
                "status": "true",
                "message": result["message"],
                "data": {
                    "prompt_id": result["prompt_id"],
                    "analytics_id": result["analytics_id"]
                }
            })
        elif result["status"] == "skipped":
            return JsonResponse({
                "status": "false",
                "message": result["message"]
            })
        elif result["status"] == "no_prompts":
            return JsonResponse({
                "status": "false",
                "message": result["message"]
            })
        else:  # error status
            return JsonResponse({
                "status": "false",
                "message": result["message"]
            })

    except Exception as e:
        logger.error(f"Error in manage_prompts: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def trigger_auto_processing(request):
    """Run the next prompt for the caller's active project.

    The first request in a manual run re-queues completed prompts for that
    project. The browser then calls this endpoint once per prompt, avoiding one
    long request while a single button click still runs the complete queue.
    """
    try:
        group_id = request.data.get("groupid")
        rerun = request.data.get("rerun", False)
        if not group_id:
            return JsonResponse({"status": "false", "message": "groupid is required"})

        try:
            group = Groups.objects.get(id=group_id, fk_user_id=request.user.id)
        except Groups.DoesNotExist:
            return JsonResponse(
                {"status": "false", "message": "Invalid group"}, status=403
            )

        project_prompts = LLMPrompt.objects.filter(
            fk_user_id=request.user.id,
            fk_group_id=group.id,
        )
        if not project_prompts.exists():
            result = {"status": "no_prompts", "message": "No prompts to process"}
            total_queued = 0
        elif rerun and project_prompts.filter(track_status="SCHD").exists():
            result = {
                "status": "skipped",
                "message": "Another prompt is currently being processed",
            }
            total_queued = project_prompts.filter(
                track_status__in=["INIT", "FAIL", "SCHD"]
            ).count()
        else:
            probe_prompt = None
            if rerun:
                probe_prompt = project_prompts.filter(
                    track_status__in=["INIT", "FAIL"]
                ).order_by("created_date").first()
                if probe_prompt is None:
                    probe_prompt = project_prompts.filter(
                        track_status="DONE"
                    ).order_by("created_date").first()
                total_queued = project_prompts.count()
            else:
                total_queued = project_prompts.filter(
                    track_status__in=["INIT", "FAIL"]
                ).count()

            result = process_llm_prompts_automatically(
                user_id=request.user.id,
                group_id=group.id,
                prompt=probe_prompt,
            )
            if rerun and result["status"] == "success":
                project_prompts.exclude(pk=probe_prompt.pk).filter(
                    track_status="DONE"
                ).update(
                    track_status="INIT",
                    track_message="Queued for re-analysis",
                )

        remaining = project_prompts.filter(
            track_status__in=["INIT", "FAIL"]
        ).count()
        result["total_queued"] = total_queued
        result["remaining"] = remaining

        return JsonResponse({
            "status": "true" if result["status"] in ["success", "skipped", "no_prompts"] else "false",
            "message": result["message"],
            "data": result
        })

    except Exception as e:
        logger.error(f"Error in trigger_auto_processing: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
def get_processing_status(request):
    """Get the current processing status of LLM prompts."""
    try:
        required_fields = ["userid"]
        validation_required = all(field in request.data for field in required_fields)

        if not validation_required:
            return JsonResponse({"status": "false", "message": "userid is required"})

        userid = request.data["userid"].strip()

        # Validate user exists
        try:
            user_instance = Account.objects.get(id=userid)
        except Account.DoesNotExist:
            return JsonResponse({"status": "false", "message": "Invalid user"})

        # Get status counts
        status_counts = {
            "INIT": LLMPrompt.objects.filter(fk_user=user_instance, track_status="INIT").count(),
            "SCHD": LLMPrompt.objects.filter(fk_user=user_instance, track_status="SCHD").count(),
            "DONE": LLMPrompt.objects.filter(fk_user=user_instance, track_status="DONE").count(),
            "FAIL": LLMPrompt.objects.filter(fk_user=user_instance, track_status="FAIL").count(),
        }

        # Get currently processing prompt (if any)
        current_processing = None
        scheduled_prompt = LLMPrompt.objects.filter(fk_user=user_instance, track_status="SCHD").first()
        if scheduled_prompt:
            current_processing = {
                "prompt_id": str(scheduled_prompt.prompt_id),
                "prompt": scheduled_prompt.prompt[:100] + "..." if len(scheduled_prompt.prompt) > 100 else scheduled_prompt.prompt,
                "track_message": scheduled_prompt.track_message,
                "started_at": scheduled_prompt.modified_date.strftime("%Y-%m-%d %H:%M:%S")
            }

        return JsonResponse({
            "status": "true",
            "data": {
                "status_counts": status_counts,
                "current_processing": current_processing,
                "total_prompts": sum(status_counts.values())
            }
        })

    except Exception as e:
        logger.error(f"Error in get_processing_status: {str(e)}")
        return JsonResponse({"status": "false", "message": "Something went wrong"})
