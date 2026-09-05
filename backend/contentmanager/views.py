from django.http import JsonResponse
from rest_framework.decorators import api_view
from contentmanager.models import ContentPlanner
from contentmanager.sanitizer import sanitize_article_html
from account.models import *
from account.completions import (
    AICompletionFailed,
    NoAIProviderConfigured,
    generate_text,
)
from serp.models import Groups
import json, os, threading
from datetime import timedelta
from django.utils import timezone
from pathlib import Path
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated


def format_custom_date(date_input):

    # Convert datetime to string if needed
    if isinstance(date_input, datetime):
        dt = date_input
    elif isinstance(date_input, str):
        dt = datetime.strptime(date_input, "%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        raise ValueError("Unsupported date format. Provide a string or datetime object.")

    # Get the day and determine the correct suffix
    day = dt.day
    suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    # Format the date as 'Mar17th 2025'
    return dt.strftime(f"%b{day}{suffix} %Y")


def _article_file(content_id):
    """The one place that knows where a plan's article HTML lives on disk."""
    return Path(os.getcwd()) / "files" / "contentplanner" / ("cnt_plan_%s.html" % content_id)


def _clamped_score(value):
    """Whole 0-100 score. The editor sends a float; the table renders it raw."""
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = 0
    return str(max(0, min(score, 100)))


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def create_content(request):
    try:
        required_fields = ["userid", "grpid", "primary_keyword", "secondary_keywords", "region_name", "region_code", "country_name"]
        validation_required = all(field in request.data for field in required_fields)

        if not validation_required:
            return JsonResponse({"status": "false", "message": "Invalid Params"})

        userid = request.data["userid"].strip()
        grpid = str(request.data["grpid"]).strip()
        primary_keyword = request.data["primary_keyword"].strip()
        region_name = request.data["region_name"].strip()
        region_code = request.data["region_code"].strip()
        country_name = request.data["country_name"].strip()

        secondary_keywords = request.data.get("secondary_keywords", "")
        # secondary_keywords = [keyword.strip() for keyword in secondary_keywords.split(",") if keyword.strip()]

        user_instance = Account.objects.get(id=userid)
        group_instance = Groups.objects.filter(id=grpid, fk_user_id=userid).first()
        if not group_instance:
            return JsonResponse({"status": "false", "message": "Project not found"}, status=404)

        if ContentPlanner.objects.filter(
            fk_user_id=userid,
            fk_group_id=grpid,
            primary_keyword=primary_keyword.lower(),
        ).exists():
            return JsonResponse({"status": "false", "message": "Primary Keyword has been already created"})

        # Create New Content
        newContent = ContentPlanner()
        newContent.fk_user = user_instance
        newContent.fk_group = group_instance
        newContent.primary_keyword = primary_keyword.lower()
        newContent.secondary_keywords = [each_keyword.lower() for each_keyword in secondary_keywords if each_keyword]
        newContent.region_name = region_name
        newContent.region_code = region_code
        newContent.country_name = country_name
        newContent.save()

        return JsonResponse({"status": "true", "message": "New content has been created successfully"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def list_content(request):
    try:
        required_fields = ["userid", "grpid"]
        validation_required = all(field in request.data for field in required_fields)

        if not validation_required:
            return JsonResponse({"status": "false", "message": "Invalid Params"})

        userid = request.data["userid"].strip()
        grpid = str(request.data["grpid"]).strip()

        user_content_plans = ContentPlanner.objects.filter(fk_user_id=userid, fk_group_id=grpid).values("content_id", "primary_keyword", "secondary_keywords", "score", "country_name", "track_status", "created_date", "modified_date")

        user_content_plans = [{**item, "modified_date": format_custom_date(item["modified_date"])} for item in user_content_plans if item.get("modified_date")]

        return JsonResponse({"status": "true", "data": user_content_plans})

    except Exception as e:
        print(e)
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def delete_content(request):
    try:

        required_fields = ["userid", "grpid", "content_ids"]
        validation_required = all(field in request.data for field in required_fields)

        if not validation_required:
            return JsonResponse({"status": "false", "message": "Invalid Params"})

        userid = request.data["userid"].strip()
        grpid = str(request.data["grpid"]).strip()
        content_ids = request.data["content_ids"]

        deletable_ids = list(ContentPlanner.objects.filter(fk_user_id=userid, fk_group_id=grpid, content_id__in=content_ids).values_list("content_id", flat=True))

        if not deletable_ids:
            return JsonResponse({"status": "false", "message": "Something went wrong"})

        ContentPlanner.objects.filter(fk_user_id=userid, fk_group_id=grpid, content_id__in=content_ids).delete()

        # The article body lives on disk, so dropping only the row leaks the file.
        for each_id in deletable_ids:
            _article_file(each_id).unlink(missing_ok=True)

        return JsonResponse({"status": "true", "message": "Content has been deleted successfully"})

    except Exception as e:
        print(e)
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def plan_details(request):
    try:
        required_fields = ["userid", "grpid", "content_id"]
        validation_required = all(field in request.data for field in required_fields)

        if not validation_required:
            return JsonResponse({"status": "false", "message": "Invalid Params"})

        userid = request.data["userid"].strip()
        grpid = str(request.data["grpid"]).strip()
        content_id = request.data["content_id"].strip()

        user_content_plans = ContentPlanner.objects.filter(fk_user_id=userid, fk_group_id=grpid, content_id=content_id).values("content_id", "file_name", "primary_keyword", "secondary_keywords", "country_name", "file_name", "nlp_stats", "track_status", "created_date", "modified_date").first()

        if not user_content_plans:
            return JsonResponse({"status": "false", "message": "Content does not exist or may have been deleted"})

        for key, value in user_content_plans.items():
            if key == "modified_date":
                user_content_plans[key] = format_custom_date(value)

        content_html_file = _article_file(content_id)
        content_html_data = ""
        if content_html_file.exists():
            content_html_data = content_html_file.read_text(encoding="utf-8")

        user_content_plans["content_html_data"] = content_html_data
        return JsonResponse({"status": "true", "data": user_content_plans})

    except Exception as e:
        print(e)
        return JsonResponse({"status": "false", "message": "Something went wrong"})


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def update_content(request):
    try:
        required_fields = ["userid", "grpid", "content_id", "content_html_data", "content_score"]
        validation_required = all(field in request.data for field in required_fields)

        if not validation_required:
            return JsonResponse({"status": "false", "message": "Invalid Params"})

        userid = request.data["userid"].strip()
        grpid = str(request.data["grpid"]).strip()
        content_id = request.data["content_id"].strip()
        content_html_data = request.data["content_html_data"]
        content_score = request.data["content_score"]
        user_content_plan = ContentPlanner.objects.filter(fk_user_id=userid, fk_group_id=grpid, content_id=content_id).first()

        if not user_content_plan:
            return JsonResponse({"status": "false", "message": "Content does not exist or may have been deleted"})

        parsed_content_html_data = json.loads(content_html_data)
        content_html_file = _article_file(content_id)
        content_dir = content_html_file.parent
        content_dir.mkdir(parents=True, exist_ok=True)
        with content_html_file.open("w", encoding="utf-8") as f:
            f.write(parsed_content_html_data)

        user_content_plan.file_name = content_html_file.name
        user_content_plan.score = _clamped_score(content_score)
        user_content_plan.track_status = "DONE"
        user_content_plan.save()

        return JsonResponse({"status": "true", "message": "Content has been updated succesfully"})

    except Exception as e:
        print(e)
        return JsonResponse({"status": "false", "message": "Something went wrong"})


# A provider call runs 30-60s. Awaited inside the request it held a worker for
# the whole of it, so three people generating at once made the product
# unavailable to everyone. The work now runs on a daemon thread and the browser
# polls, the same shape serp/engine_trigger.py already uses for rank runs.
_GEN_STALE_AFTER = timedelta(minutes=10)


def _generation_prompt(plan):
    system = (
        "You are an SEO content editor. Return only article HTML using h1, h2, h3, "
        "h4, p, ul, ol, li, strong, b, em, and br tags. Never return markdown fences, "
        "scripts, styles, forms, embeds, document wrappers, or tag attributes."
    )
    secondary = ", ".join(plan.secondary_keywords or [])
    prompt = (
        "Create a useful, SEO-optimized article about %s for readers in %s. "
        "Naturally include these secondary keywords: %s. Use one h1, at least three "
        "substantial sections, and at least five substantial paragraphs."
        % (plan.primary_keyword, plan.country_name or "the target market", secondary or "none")
    )
    return system, prompt


def _run_generation(userid, content_id):
    """Provider call, off the request. Writes an answer or a reason, never neither."""
    try:
        plan = ContentPlanner.objects.filter(content_id=content_id).first()
        if plan is None:
            return
        system, prompt = _generation_prompt(plan)
        ContentPlanner.objects.filter(content_id=content_id).update(gen_status="RUNNING")
        generated = generate_text(userid, system, prompt, max_tokens=1800, temperature=0.7)
        content = sanitize_article_html(generated)
        if not content:
            raise AICompletionFailed("AI provider returned no usable article HTML")
        ContentPlanner.objects.filter(content_id=content_id).update(
            gen_status="DONE", gen_content=content, gen_message="", gen_claim_date=None
        )
    except (NoAIProviderConfigured, AICompletionFailed) as exc:
        ContentPlanner.objects.filter(content_id=content_id).update(
            gen_status="FAIL", gen_message=str(exc), gen_content="", gen_claim_date=None
        )
    except Exception as exc:
        # A thread that dies silently would leave the plan RUNNING forever, and
        # the staleness cutoff would not report it for ten minutes. Record it.
        ContentPlanner.objects.filter(content_id=content_id).update(
            gen_status="FAIL",
            gen_message="Generation failed: %s" % (str(exc)[:200] or exc.__class__.__name__),
            gen_content="",
            gen_claim_date=None,
        )


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def generate_ai_content(request):
    required_fields = ["userid", "grpid", "content_id"]
    validation_required = all(field in request.data for field in required_fields)

    if not validation_required:
        return JsonResponse({"status": "false", "message": "Invalid Params"})

    try:
        userid = request.data["userid"].strip()
        grpid = str(request.data["grpid"]).strip()
        content_id = request.data["content_id"].strip()
        owned = ContentPlanner.objects.filter(
            fk_user_id=userid, fk_group_id=grpid, content_id=content_id
        )
        if not owned.exists():
            return JsonResponse(
                {"status": "false", "message": "Content does not exist or may have been deleted"},
                status=404,
            )

        # Claim conditionally: whichever request wins the update starts the
        # thread, and the loser is told a job is already running rather than
        # billing the account a second time for the same article.
        cutoff = timezone.now() - _GEN_STALE_AFTER
        claimed = owned.exclude(
            gen_status__in=("QUEUED", "RUNNING"), gen_claim_date__gt=cutoff
        ).update(
            gen_status="QUEUED", gen_claim_date=timezone.now(), gen_message="", gen_content=""
        )
        if not claimed:
            return JsonResponse(
                {"status": "true", "data": {"content_id": content_id, "gen_status": "RUNNING"},
                 "message": "Generation is already running for this plan."}
            )

        threading.Thread(target=_run_generation, args=(userid, content_id), daemon=True).start()
        return JsonResponse(
            {"status": "true", "data": {"content_id": content_id, "gen_status": "QUEUED"},
             "message": "Generation started."}
        )

    except Exception:
        return JsonResponse({"status": "false", "message": "Something went wrong"}, status=500)


@api_view(["POST"])
@permission_classes((IsAuthenticated,))
def generate_ai_status(request):
    """Where one plan's generation has got to.

    Never reports RUNNING for a job nobody is running: a claim older than
    _GEN_STALE_AFTER belonged to a process that no longer exists -- a restart,
    a killed container -- and is reported as interrupted so the user can start
    it again instead of watching a spinner that will never stop.
    """
    required_fields = ["userid", "grpid", "content_id"]
    if not all(field in request.data for field in required_fields):
        return JsonResponse({"status": "false", "message": "Invalid Params"})

    try:
        userid = request.data["userid"].strip()
        grpid = str(request.data["grpid"]).strip()
        content_id = request.data["content_id"].strip()
        plan = ContentPlanner.objects.filter(
            fk_user_id=userid, fk_group_id=grpid, content_id=content_id
        ).first()
        if plan is None:
            return JsonResponse(
                {"status": "false", "message": "Content does not exist or may have been deleted"},
                status=404,
            )

        state = (plan.gen_status or "").upper()
        payload = {"gen_status": state or "NONE", "content": "", "message": plan.gen_message or ""}

        if state in ("QUEUED", "RUNNING"):
            claim = plan.gen_claim_date
            if claim is None or claim < timezone.now() - _GEN_STALE_AFTER:
                ContentPlanner.objects.filter(content_id=content_id).update(
                    gen_status="FAIL",
                    gen_message="Generation was interrupted before it finished. You can start it again.",
                    gen_claim_date=None,
                )
                payload["gen_status"] = "FAIL"
                payload["message"] = "Generation was interrupted before it finished. You can start it again."
        elif state == "DONE":
            payload["content"] = plan.gen_content or ""
            if not payload["content"]:
                # DONE with nothing to show is not done. Say so rather than
                # handing the editor an empty article as a success.
                payload["gen_status"] = "FAIL"
                payload["message"] = "Generation finished without producing an article. Try again."

        return JsonResponse({"status": "true", "data": payload})

    except Exception:
        return JsonResponse({"status": "false", "message": "Something went wrong"}, status=500)
