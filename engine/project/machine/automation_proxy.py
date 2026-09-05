"""DataBlue SERP API backend for the SearchMirror engine.

Replaces the old Scrapingdog/proxy scraper entirely.  All HTTP is async
(httpx.AsyncClient) with asyncio.Semaphore concurrency, matching test_api.py
exactly.  Django/Celery compatibility is achieved by running the event loop
inside a ThreadPoolExecutor(max_workers=1) so asyncio.run() never conflicts
with an already-running loop.

Settings required in Django settings.py / settings.local.py:
    DATABLUE_API_KEY = "wh_..."          # DataBlue API key
    RESEARCH_PROXY_URL = "http://..."    # Optional; only for research scraping
"""
from django.conf import settings as _def_

import urllib.parse
import json
import asyncio
import os
import random

import httpx


# ---------------------------------------------------------------------------
# Legacy header helpers — used by domains.py and research modules.
# Kept for backward compatibility with non-SERP code paths.
# ---------------------------------------------------------------------------
def __automation_desktop_headers__():
	_list_ = getattr(_def_, 'LIST_OF_HEADERS', []) or []
	if _list_:
		_ua_ = _list_[random.randint(0, len(_list_) - 1)]
	else:
		_ua_ = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
	return {
		'accept':     '*/*',
		'origin':     'https://www.google.com',
		'referer':    'https://www.google.com/',
		'User-Agent': _ua_,
	}


def __automation_mobile_headers__():
	_list_ = getattr(_def_, 'LIST_OF_MOBILE_ALL', []) or []
	if _list_:
		_ua_ = _list_[random.randint(0, len(_list_) - 1)]
	else:
		_ua_ = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
	return {
		'accept':     '*/*',
		'origin':     'https://www.google.com',
		'referer':    'https://www.google.com/',
		'User-Agent': _ua_,
	}

from project.machine.models import (
    Keyword as _kw__record_,
    Mainsettings as _ms__record_,
    KeywordResearch as _kw__research_,
    BrandTracker as _bd__record_,
    Group as _gp__record_,
)

from project.machine import watchdog as _wd_, automation_common as _at__common_
from project.machine import parser_json as _at__parser__json_

# ---------------------------------------------------------------------------
# DataBlue configuration constants
# ---------------------------------------------------------------------------
_DATABLUE_API_URL_     = "https://api.datablue.dev/v1/data/google/serp"
_DATABLUE_TIMEOUT_     = 210        # seconds — matches test_api.py default
_DATABLUE_PAGES_       = 3         # serp param 'pages' — result pages to fetch (~10 organic/page)
_DATABLUE_ADVANCED_    = False     # serp param 'advanced' — fallback only; the per-project
                                   # Group.serp_advanced flag decides. False = Lite (organic +
                                   # ads/featured_snippet/people_also_ask/local_results/
                                   # knowledge_panel/videos). True = Advanced, which adds
                                   # ai_overview and COSTS MORE per request.
_DATABLUE_DOMAIN_      = "google.com"  # serp param 'domain' — Google TLD; per-keyword 'domain' overrides this
_DATABLUE_CONCURRENCY_ = 100        # semaphore width — matches test_api.py default
# How many items may be anywhere in the fetch->process pipeline, as a multiple
# of the fetch width.  Above 1 so the fetch stage stays saturated while earlier
# items are still being written; finite so responses cannot outrun the writer
# and accumulate for the whole run.
_PIPELINE_SLACK_       = 2


def _google_domain_(_region_, _location_):
	"""Return the Google TLD a keyword must be measured on.

	`region` is the account's chosen search-engine domain -- "google.co.in" --
	and it is what DataBlue's `domain` parameter takes.  Rows seeded from the
	region table hold the country name there instead ("India"), and those rows
	carry the domain in `location`'s "google.co.in (India)" form, so that is
	read next.  Anything that is not a Google host falls back to the module
	default rather than being sent as one: a country name in `domain` is not a
	search engine and the provider would reject the call.

	Country targeting is a separate parameter (`country`, from the keyword's
	isocode) and is applied independently -- the two describe different halves
	of the same choice, so setting both is not applying the region twice.
	"""
	for _candidate_ in (_region_, str(_location_ or "").split("(")[0]):
		_candidate_ = str(_candidate_ or "").strip().lower()
		if _candidate_.startswith("www."):
			_candidate_ = _candidate_[4:]
		if _candidate_.startswith("google."):
			return _candidate_

	return _DATABLUE_DOMAIN_


def _account_serp_prefs_(_uid_):
	"""Return (api_key, pages) for one account, or (None, None) when unset.

	The account's key is stored encrypted -- `Accountusage.serp_key` holds a
	`shared.keycrypto` token, never the raw key -- so the engine has to decrypt
	it here. This is the only place the engine touches the ciphertext.

	Failures are swallowed deliberately and reported as "no key": an
	unreadable token (rotated SERP_KEY_SECRET) or a missing account must not
	take down a ranking run. The caller decides what an absent key means.
	"""
	if not _uid_:
		return None, None
	try:
		from project.machine.submodels.serpmodels import DAccountUsage
		# The account model's FK is `fb_user`, so the column is fb_user_id --
		# NOT fk_user_id, which is what the keyword/group models use. Filtering
		# on the wrong one matches nothing and silently falls back to the
		# instance key, which is the exact bug this function exists to fix.
		_row_ = DAccountUsage.objects.filter(fb_user_id=int(_uid_)).first()
	except Exception:
		return None, None
	if not _row_:
		return None, None

	_depth_ = int(getattr(_row_, "serp_depth", 0) or 0) or None
	_token_ = getattr(_row_, "serp_key", "") or ""
	if not _token_:
		return None, _depth_
	try:
		from shared.keycrypto import decrypt_key
		return (decrypt_key(_token_) or None), _depth_
	except Exception as _e_:
		print(f"[DATABLUE WARN] account {_uid_} serp_key unreadable >>> {_e_}")
		return None, _depth_


def _resolve_api_key_(_api_key_=None):
	"""Pick the key a fetch should bill against.

	A caller that passes the account's own decrypted key gets exactly that.
	Anything that passes nothing falls back to the instance-wide key -- and
	that fallback is what ALLOW_INSTANCE_FALLBACK governs.

	Why the flag exists: a single-operator self-host legitimately runs every
	project on one key from .env. A hosted instance must not, because a user
	whose key is missing or unreadable would silently spend the house key and
	nothing on screen would look wrong. Default is to allow it, so a
	self-hoster is not broken by an upgrade; hosted deployments set
	ALLOW_INSTANCE_FALLBACK=false and get no ranking instead of a surprise
	bill.
	"""
	if _api_key_:
		return _api_key_
	if str(getattr(_def_, "ALLOW_INSTANCE_FALLBACK", "false")).lower() in ("0", "false", "no"):
		return ""
	return getattr(_def_, "DATABLUE_API_KEY", "")


def _project_serp_advanced_(_gid_):
	"""Return the project's DataBlue depth flag, or None when it cannot be read.

	None is not False. It means "unknown", and the caller leaves the item alone
	so the module default applies -- rather than stamping Lite onto a project
	that may have chosen Advanced, or Advanced onto one that did not and would
	then be billed at the higher credit weight without asking.
	"""
	if not _gid_:
		return None
	try:
		_row_ = _gp__record_.objects.filter(__raw__={'id': int(_gid_)}).first()
	except Exception as _e_:
		print(f"[DATABLUE WARN] project {_gid_} serp_advanced unreadable >>> {_e_}")
		return None
	if not _row_:
		return None
	return bool(getattr(_row_, "serp_advanced", False))


def _apply_account_prefs_(_items_dict_):
	"""Resolve the owning account for a batch: return its key, stamp its depth.

	Every item in a batch belongs to one project and therefore one account, so
	the lookup happens once per batch rather than once per keyword.

	`pages` is written with setdefault, so an item that already carries an
	explicit depth keeps it. When the account has no depth set, nothing is
	written and the module default applies downstream.

	`advanced` is per-PROJECT, not per-account, and is resolved once per
	distinct group in the batch. Both settings are cost multipliers on the
	account's own key -- pages bills a request per page, advanced bills each
	request at a higher credit weight -- so neither is ever inferred, only read.
	"""
	if not _items_dict_:
		return None
	_uid_ = None
	for _item_ in _items_dict_.values():
		if isinstance(_item_, dict) and _item_.get("fk_user_id"):
			_uid_ = _item_["fk_user_id"]
			break
	_key_, _depth_ = _account_serp_prefs_(_uid_)
	if _depth_:
		for _item_ in _items_dict_.values():
			if isinstance(_item_, dict):
				_item_.setdefault("pages", _depth_)

	_advanced_by_group_ = {}
	for _item_ in _items_dict_.values():
		if not isinstance(_item_, dict):
			continue
		_gid_ = _item_.get("fk_group_id")
		if _gid_ not in _advanced_by_group_:
			_advanced_by_group_[_gid_] = _project_serp_advanced_(_gid_)
		if _advanced_by_group_[_gid_] is not None:
			_item_.setdefault("advanced", _advanced_by_group_[_gid_])

	return _key_


# ---------------------------------------------------------------------------
# Internal: on-disk raw-response cache
# ---------------------------------------------------------------------------
def _open_for_write_(_path_):
	"""Open a raw-response file for writing, creating its directory first.

	project/files/{desktop,mobile,other,brand,research} are not in the image and
	nothing creates them at start-up, so writing a fetched SERP used to raise
	FileNotFoundError *after* the provider call had already been paid for -- the
	credit was spent and the result thrown away.
	"""
	os.makedirs(os.path.dirname(_path_), exist_ok=True)
	return open(_path_, 'w', encoding='utf-8')


# ---------------------------------------------------------------------------
# Internal: normalize DataBlue response → downstream parser shape
# ---------------------------------------------------------------------------
def _datablue_normalize_organic_(_organic_):
	"""Map DataBlue field names to the shape parser_json.py expects.

	DataBlue returns:  position, url, title, snippet
	Parsers expect:    rank,     link, title, snippet, displayed_link
	"""
	for _item_ in _organic_:
		if not isinstance(_item_, dict):
			continue

		# position → rank
		if "rank" not in _item_ and "position" in _item_:
			try:
				_item_["rank"] = int(_item_.get("position") or 0)
			except Exception:
				_item_["rank"] = 0

		# url → link
		if "link" not in _item_ and "url" in _item_:
			_item_["link"] = _item_.get("url", "")

		# synthesize displayed_link from link hostname + path
		if "displayed_link" not in _item_:
			try:
				_p_ = urllib.parse.urlparse(_item_.get("link", ""))
				_item_["displayed_link"] = (_p_.netloc + _p_.path).rstrip("/")
			except Exception:
				_item_["displayed_link"] = _item_.get("link", "")

		# default snippet if missing
		if "snippet" not in _item_:
			_item_["snippet"] = ""
   
		# default title if missing (DataBlue omits null fields — exclude_none=True)
		if "title" not in _item_:
			_item_["title"] = ""

	return _organic_


# ---------------------------------------------------------------------------
# Build keyword task dict (AUTOMATION STAGE 3 replacement)
# ---------------------------------------------------------------------------
def __automation_search_scrap_url__(_kw__data_):
	"""Return a plain dict with all fields the engine needs downstream.

	NOTE: This no longer builds or stores a Google URL — DataBlue handles
	the actual search.

	Keeps the ScrapingDog-era DB write semantics alive: crawlurl/geo_target/
	geo_target_uule are written back onto the Keyword record so downstream
	audit/reporting code that reads these fields doesn't break.  Under
	DataBlue, crawlurl has no Google URL to store (DataBlue builds it
	server-side) and UULE is not part of the provider's parameter contract
	(docs/DATABLUE-INTEGRATION.md 3a) -- geo targeting is `domain` plus
	`country` -- so those two stay blank.
	"""
	# Best-effort geo_target — fall back to empty string if the model
	# doesn't expose a region/location attribute.
	_loc_ = getattr(_kw__data_, 'location', '') or ''
	_reg_ = getattr(_kw__data_, 'region', '') or ''
	_geo_target_ = _loc_ if _loc_ else _reg_

	# MongoEngine: 'id' field doesn't exist on the Keyword model; only
	# __raw__ reaches the integer id field.  Do NOT switch to id=_kw__data_.id.
	try:
		_kw__record_.objects.filter(__raw__={'id': _kw__data_.id}).update(
			crawlurl="",
			geo_target=_geo_target_,
			geo_target_uule="",
		)
	except Exception as _e_:
		print(f"[DATABLUE WARN] geo_target DB write failed for ID:{_kw__data_.id} >>> {_e_}")

	# Per-keyword overrides. The key is emitted ONLY when the row carries an
	# explicit value: null means inherit, and _apply_account_prefs_ uses
	# setdefault, so an absent key is what lets the account/project default
	# apply. Emitting a default here would silently disable inheritance.
	_overrides_ = {}
	_kw__pages_ = getattr(_kw__data_, 'serp_pages', None)
	if _kw__pages_ is not None:
		_overrides_['pages'] = int(_kw__pages_)
	_kw__adv_ = getattr(_kw__data_, 'serp_advanced', None)
	if _kw__adv_ is not None:
		_overrides_['advanced'] = bool(_kw__adv_)

	return {
		**_overrides_,
		'exactdomain': _kw__data_.exactdomain,
		'id':          _kw__data_.id,
		'fk_group_id': _kw__data_.fk_group_id,
		'language':    _kw__data_.language_code,
		'isocode':     _kw__data_.isocode,
		'platform':    _kw__data_.platform,
		'fk_user_id':  _kw__data_.fk_user_id,
		'page_uid':    getattr(_kw__data_, 'page_uuid', ''),
		'target':      _kw__data_.target,
		'se_name':     _kw__data_.region,
		# The fetcher reads 'domain'.  Writing the region only under 'se_name'
		# is why every rank was measured on google.com no matter which Google
		# the account picked -- the fetcher never found the key and fell
		# through to its constant.
		'domain':      _google_domain_(_reg_, _loc_),
		'keyword':     _kw__data_.keyword,
		'url':         '',
	}


# ---------------------------------------------------------------------------
# Build brand task dict (AUTOMATION BRAND STAGE 3 replacement)
# ---------------------------------------------------------------------------
def __automation_brand_scrap_url__(_bd__data_, _gp__data_):
	"""Return a plain dict with all fields the brand engine needs downstream."""
	return {
		'id':          _bd__data_.id,
		'fk_group_id': _bd__data_.fb_group_id,
		'fk_user_id':  _bd__data_.fb_user_id,
		'target':      _gp__data_.domain_name,
		'exactdomain': False,
		'keyword':     _at__common_.trim(_bd__data_.brand_name),
		'platform':    'desktop',
		'url_list':    _bd__data_.conquestor_url_list,
	}



# ---------------------------------------------------------------------------
# PURE ASYNC LAYER — no Django DB calls inside
# ---------------------------------------------------------------------------
async def _fetch_one_(_client_, _sem_, _item_id_, _item_data_, _api_key_):
	"""Single DataBlue request, concurrency-limited by semaphore.

	Pattern mirrors test_api.py search() exactly:
	    async with sem:
	        r = await client.get(...)
	"""
	_kw_          = _item_data_['keyword']
	_item_id_str_ = str(_item_data_['id'])

	# Build query params for the /serp endpoint — sent as a GET querystring,
	# mirroring the documented `curl -G` request.  `advanced` is a module
	# constant; the geo params (domain, language, country, mobile) are derived
	# per-keyword so the account's chosen Google and country are what gets
	# measured.  Engine/manual pass all of them (via
	# __automation_search_scrap_url__); brand omits them (domain-scoped, not
	# keyword-geo).  httpx serializes bools to lowercase 'true'/'false'.
	_params_ = {
		"query":    _kw_[:256],
		# Pages is per-account (Accountusage.serp_depth), not global: each page is
		# billed separately by DataBlue, so a hardcoded 3 silently triples the cost
		# of every keyword regardless of what the user chose.
		"pages":    int(_item_data_.get("pages") or _DATABLUE_PAGES_),
		# Per-project (Group.serp_advanced), stamped by _apply_account_prefs_.
		# The module constant is only the fallback for a project whose flag
		# could not be read -- and the fallback is Lite, the cheaper of the two.
		"advanced": bool(_item_data_.get("advanced", _DATABLUE_ADVANCED_)),
		"mobile":   str(_item_data_.get("platform", "")).lower() == "mobile",
		"domain":   _item_data_.get("domain") or _DATABLUE_DOMAIN_,
	}
	_lang_ = _item_data_.get("language")
	_iso_  = _item_data_.get("isocode")
	if _lang_:
		_params_["language"] = _lang_
	if _iso_:
		_params_["country"] = str(_iso_).lower()

	async with _sem_:
		print(f"[DATABLUE REQ] ID:{_item_id_str_} KW:{_kw_[:60]} SE:{_params_['domain']} GEO:{_params_.get('country','-')}/{_params_.get('language','-')} MOBILE:{_params_['mobile']} PAGES:{_params_['pages']} ADV:{_params_['advanced']}")
		try:
			_r_ = await _client_.get(
				_DATABLUE_API_URL_,
				headers={"Authorization": f"Bearer {_api_key_}"},
				params=_params_,
				timeout=_DATABLUE_TIMEOUT_,
			)
			print(
				f"[DATABLUE RES] ID:{_item_id_str_} "
				f"STATUS:{_r_.status_code} "
				f"SIZE:{len(_r_.text or '')}bytes"
			)

			if _r_.status_code == 200:
				try:
					_raw_     = _r_.json()
					_organic_ = _raw_.get("organic_results", []) or []
					_raw_["organic_results"] = _datablue_normalize_organic_(_organic_)
					return {
						"item_id": _item_id_,
						"status":  _r_.status_code,
						"data":    _raw_,
						"success": len(_organic_) > 0,
					}
				except Exception as _je_:
					print(f"[DATABLUE ERR] ID:{_item_id_str_} JSON_PARSE_FAILED: {_je_}")
					return {"item_id": _item_id_, "status": _r_.status_code, "data": None, "success": False}

			return {"item_id": _item_id_, "status": _r_.status_code, "data": None, "success": False}

		except httpx.TimeoutException:
			print(f"[DATABLUE ERR] ID:{_item_id_str_} TIMEOUT after {_DATABLUE_TIMEOUT_}s")
			return {"item_id": _item_id_, "status": "timeout", "data": None, "success": False}
		except Exception as _e_:
			print(f"[DATABLUE ERR] ID:{_item_id_str_} EXCEPTION:{_e_}")
			return {"item_id": _item_id_, "status": "error", "data": None, "success": False}


async def _fetch_all_async_(_items_dict_, _concurrency_, _api_key_):
	"""Run all keyword requests concurrently.

	Matches test_api.py main() pattern exactly:
	    sem = asyncio.Semaphore(args.concurrency)
	    async with httpx.AsyncClient() as client:
	        tasks = [search(client, sem, kw, ...) for ...]
	        for coro in asyncio.as_completed(tasks):
	            r = await coro
	"""
	_sem_     = asyncio.Semaphore(_concurrency_)
	_results_ = []

	_limits_ = httpx.Limits(
		max_connections=_concurrency_ + 5,
		max_keepalive_connections=_concurrency_,
	)
	async with httpx.AsyncClient(limits=_limits_) as _client_:
		# create_task schedules all coroutines immediately — guaranteed
		# concurrent on every Python version (3.7+), not just 3.10+.
		_tasks_ = [
			asyncio.create_task(
				_fetch_one_(_client_, _sem_, _item_id_, _item_data_, _api_key_)
			)
			for _item_id_, _item_data_ in _items_dict_.items()
		]
		for _coro_ in asyncio.as_completed(_tasks_):
			_results_.append(await _coro_)

	return _results_


def __automation_fetch_all__(_items_dict_, _concurrency_=_DATABLUE_CONCURRENCY_, _api_key_=None):
	"""Synchronous entry point for Django/Celery callers.

	Runs the async event loop inside a dedicated thread so asyncio.run()
	never raises "This event loop is already running." (Celery, gevent,
	ASGI, and pytest-asyncio are all safe.)

	Usage:
	    results = __automation_fetch_all__(kw_collections)
	    # or with custom concurrency:
	    results = __automation_fetch_all__(kw_collections, concurrency=10)
	    # or with a per-account BYOK key:
	    results = __automation_fetch_all__(kw_collections, _api_key_=account_key)
	"""
	import concurrent.futures as _cf_

	_api_key_ = _resolve_api_key_(_api_key_)
	with _cf_.ThreadPoolExecutor(max_workers=1) as _pool_:
		return _pool_.submit(
			asyncio.run,
			_fetch_all_async_(_items_dict_, _concurrency_, _api_key_),
		).result()


# ---------------------------------------------------------------------------
# PIPELINED FETCH + PROCESS — dispatches DB work as each fetch lands
# ---------------------------------------------------------------------------
def __automation_fetch_and_process__(_items_dict_, _concurrency_, _process_cb_, _api_key_=None):
	"""Sync entry point.  Fires all fetches concurrently.  As each response
	arrives, dispatches _process_cb_(fetch_result) to a thread pool in
	parallel — so DB writes begin while other fetches are still in flight.

	Returns one compact entry per item: {"item_id", "status", "success", "cb"}.
	The response body is NOT returned — see the window note below.

	Pipeline shape (mirrors test_api.py as_completed pattern):
	    fetch_1 ──┐
	    fetch_2 ──┤→ asyncio.as_completed ─→ run_in_executor(pool, cb)
	    fetch_N ──┘                                   │
	                                                  └→ DB writes (parallel)

	Event-loop safety matches __automation_fetch_all__ — the async body
	runs inside a ThreadPoolExecutor(max_workers=1) so asyncio.run() never
	collides with a Django/Celery/gevent loop.
	"""
	import concurrent.futures as _cf_

	_api_key_ = _resolve_api_key_(_api_key_)
	_pipe__width_ = max(1, _concurrency_ * _PIPELINE_SLACK_)

	async def _fetch_and_dispatch_(_client_, _sem_, _pipe_, _item_id_, _item_data_, _db_pool_, _loop_):
		"""Fetch one item, then immediately hand its result to the DB pool."""
		# _pipe_ is held across BOTH stages, _sem_ only across the fetch.  The
		# fetch semaphore alone bounds requests in flight, not responses in
		# memory: it is released the moment a response arrives, so when the DB
		# callback is slower than the provider — which it is, being parse plus
		# several Mongo writes plus a file write — responses pile up in the
		# executor's unbounded queue.  Measured on a 2,000-keyword run with a
		# callback 10x the fetch: 1,112 responses fetched, billed and resident
		# at once.  A crash there loses every one of them, already paid for.
		async with _pipe_:
			_fetch_result_ = await _fetch_one_(_client_, _sem_, _item_id_, _item_data_, _api_key_)
			try:
				_cb_result_ = await _loop_.run_in_executor(_db_pool_, _process_cb_, _fetch_result_)
			except Exception as _cbe_:
				print(f"[DATABLUE CB_ERR] ID:{_item_id_} >>> {_cbe_}")
				_cb_result_ = None

		# Summary only.  The callback has already consumed the body, and every
		# caller discards this list -- keeping it held every response for the
		# whole run: 6,000 keywords measured at +206 MB of nothing but garbage.
		return {
			"item_id": _fetch_result_.get("item_id"),
			"status":  _fetch_result_.get("status"),
			"success": _fetch_result_.get("success"),
			"cb":      _cb_result_,
		}

	async def _pipeline_():
		_sem_     = asyncio.Semaphore(_concurrency_)
		_pipe_    = asyncio.Semaphore(_pipe__width_)
		_results_ = []

		_limits_ = httpx.Limits(
			max_connections=_concurrency_ + 5,
			max_keepalive_connections=_concurrency_,
		)

		# Thread pool sized to _concurrency_ so DB callbacks can run in
		# parallel with in-flight HTTP fetches.  max_workers clamps the DB
		# side even when the semaphore lets more fetches loose.
		_loop_ = asyncio.get_event_loop()
		with _cf_.ThreadPoolExecutor(max_workers=_concurrency_) as _db_pool_:
			async with httpx.AsyncClient(limits=_limits_) as _client_:
				_tasks_ = [
					asyncio.create_task(
						_fetch_and_dispatch_(
							_client_, _sem_, _pipe_, _item_id_, _item_data_, _db_pool_, _loop_
						)
					)
					for _item_id_, _item_data_ in _items_dict_.items()
				]
				# as_completed — iterate as each (fetch + cb) pair lands,
				# NOT gather — we want results streaming back as they finish.
				for _coro_ in asyncio.as_completed(_tasks_):
					_results_.append(await _coro_)

		return _results_

	# Same event-loop-safety pattern as __automation_fetch_all__.
	with _cf_.ThreadPoolExecutor(max_workers=1) as _outer_pool_:
		return _outer_pool_.submit(asyncio.run, _pipeline_()).result()



# ---------------------------------------------------------------------------
# AUTOMATION STAGE 4+5 — process result and write file (keyword)
# ---------------------------------------------------------------------------
def __automation_process_result__(_mode_, _kw_id_, _kw_collections_, _comp__list_, _result_):
	"""Process a single fetch result for a rank-tracking keyword.

	Returns a 3-tuple: (kw_collection_entry | False, competitor_list | False, outcome)
	    outcome: "ok"   — 200 + organic results found, file written
	             "429"  — rate-limited by DataBlue
	             "fail" — any other failure (timeout, HTTP error, empty results)

	DB counter updates (auto_refresh_count, daily_automation_count, proxy_*)
	are intentionally NOT done here — the calling pool aggregates them in bulk.
	"""
	_kwc__id_       = _kw_collections_[_kw_id_]['id']
	_kwc__platform_ = _kw_collections_[_kw_id_]['platform']

	_status_   = _result_.get("status")
	_raw_data_ = _result_.get("data")

	if _status_ == 429:
		_wd_.coreLog(
			f" > {_mode_} - {_kwc__platform_} - RATE LIMITED (429) >> KW_ID:{_kwc__id_}",
			"PROXY",
		)
		return False, False, "429"

	if _status_ != 200 or not _raw_data_:
		_wd_.coreLog(
			f" > {_mode_} - {_kwc__platform_} - FAILED ({_status_}) >> KW_ID:{_kwc__id_}",
			"PROXY",
		)
		return False, False, "fail"

	_organic_ = _raw_data_.get("organic_results", [])
	if not _organic_:
		_wd_.coreLog(
			f" > {_mode_} - {_kwc__platform_} - NO RESULTS >> KW_ID:{_kwc__id_}",
			"PROXY",
		)
		return False, False, "fail"

	# Determine file path by platform
	_search__file_ = (
		os.getcwd() + "/project/files/other/searchFile__" + str(_kw_id_) + ".json"
	)
	if _kwc__platform_.lower() == "desktop":
		_search__file_ = (
			os.getcwd() + "/project/files/desktop/searchFile__" + str(_kw_id_) + ".json"
		)
	elif _kwc__platform_.lower() == "mobile":
		_search__file_ = (
			os.getcwd() + "/project/files/mobile/searchFile__" + str(_kw_id_) + ".json"
		)

	with _open_for_write_(_search__file_) as _f_:
		json.dump(_raw_data_, _f_, ensure_ascii=False)

	_kw_collections_[_kw_id_]['status']   = "200"
	_kw_collections_[_kw_id_]['response'] = _raw_data_

	# Competitor presence check — use str(_raw_data_), NOT parser.cleanMe(json_dict)
	_c__list_ = list()
	if _comp__list_:
		_c__list_ = [
			_at__common_.__c_remove__(x)
			for x in _comp__list_
			if x in str(_raw_data_)
		]

	return _kw_collections_[_kw_id_], _c__list_, "ok"


# ---------------------------------------------------------------------------
# BRAND RESULT PROCESSOR
# ---------------------------------------------------------------------------
def __automation_brand_process_result__(_bd_id_, _bd_collections_, _result_):
	"""Process a single fetch result for a brand-tracking keyword.

	Returns the updated _bd_collections_ entry on success, False on failure.
	Refresh counter updates are batched by the pool caller — not here.
	"""
	_bdc__id_ = _bd_collections_[_bd_id_]['id']

	_status_   = _result_.get("status")
	_raw_data_ = _result_.get("data")

	if _status_ == 429:
		_wd_.coreLog(
			f" > BRAND - RATE LIMITED (429) >> BD_ID:{_bdc__id_}",
			"PROXY",
		)
		return False

	if _status_ != 200 or not _raw_data_:
		_wd_.coreLog(
			f" > BRAND - FAILED ({_status_}) >> BD_ID:{_bdc__id_}",
			"PROXY",
		)
		return False

	_organic_ = _raw_data_.get("organic_results", [])
	if not _organic_:
		_wd_.coreLog(
			f" > BRAND - NO RESULTS >> BD_ID:{_bdc__id_}",
			"PROXY",
		)
		return False

	_search__file_ = (
		os.getcwd() + "/project/files/brand/brandSearchFile__" + str(_bd_id_) + ".json"
	)
	with _open_for_write_(_search__file_) as _f_:
		json.dump(_raw_data_, _f_, ensure_ascii=False)

	_bd_collections_[_bd_id_]['status']   = "200"
	_bd_collections_[_bd_id_]['response'] = _raw_data_

	return _bd_collections_[_bd_id_]


# ---------------------------------------------------------------------------
# AUTOMATION STAGE 5 — parse rank keyword JSON (unchanged logic)
# ---------------------------------------------------------------------------
def __automation_collective_parser__(_mode_, _index_, _kw__data_):
	"""Parse the stored JSON response and persist the rank to the database."""
	if _index_ in _kw__data_:
		_engine__parse__result_ = ""

		# No "read" transition: the keyword was claimed as 'busy' before the
		# fetch and stays claimed until it reaches a real outcome.  A separate
		# in-flight status for the parse step is the same state under a second
		# name, and a second name is a second way for a claim to be missed
		# (docs/ORCHESTRATION.md 2).
		_kw__soup_                      = _kw__data_[_index_]['response']
		_kw__data_[_index_]['response'] = ""
		_kw__data_[_index_]['status']   = ""

		_platform_ = _kw__data_[_index_]['platform'].lower()
		if _platform_ in ("desktop", "mobile"):
			_engine__parse__result_ = _at__parser__json_.engineParseData(
				_mode_, _kw__soup_, _kw__data_[_index_]
			)
		else:
			_wd_.coreLog(
				" !!! PLATFORM NOT AVAILABLE ON KEYWORD ID " + str(_kw__data_[_index_]['id']),
				_mode_,
			)

		if _engine__parse__result_ == 1:
			if _mode_ == "ENGINE":
				_at__common_.__change_keyword_call_status__(
					int(_kw__data_[_index_]['id']), "done", "_"
				)
				return True
			elif _mode_ == "MANUAL":
				_at__common_.__change_keyword_manual_call_status__(
					int(_kw__data_[_index_]['id']), "done"
				)
				return True
		else:
			# A response that would not parse is a failed attempt like any
			# other: counted, backed off, and terminal only once the budget is
			# spent.  It is not a measurement and must not be written as one.
			_at__common_.__record_keyword_failure__(
				int(_kw__data_[_index_]['id']), _mode_, "parse"
			)

	return False


# ---------------------------------------------------------------------------
# BRAND PARSER STAGE
# ---------------------------------------------------------------------------
def __automation_brand_collective_parser__(_index_, _bd__data_):
	"""Parse the stored JSON brand response and persist data to the database."""
	if _index_ in _bd__data_:
		_bd__soup_                      = _bd__data_[_index_]['response']
		_bd__data_[_index_]['response'] = ""
		_bd__data_[_index_]['status']   = ""

		try:
			_engine__parse__result_ = _at__parser__json_.engineBrandParseData(
				"BRAND", _bd__soup_, _bd__data_[_index_]
			)
			if _engine__parse__result_ == 1:
				return True
		except Exception as _e_:
			_wd_.coreLog(
				f" !!! BRAND PARSE ERROR BD_ID:{_index_} >>> {_e_}",
				"BRAND",
			)

	return False


# ---------------------------------------------------------------------------
# RESEARCH — kept on direct Google scraping (DataBlue is SERP, not research)
# ---------------------------------------------------------------------------
def __automation_research_request__(_r_session_, _r_kws_):
	"""Stage 3 research request — still hits Google directly via proxy.

	Requires RESEARCH_PROXY_URL in Django settings.py:
	    RESEARCH_PROXY_URL = "http://user:pass@host:port"
	If unset, requests are sent without a proxy.
	"""
	_engine__mode_ = "RESEARCH"
	_kw__id_       = 0
	try:
		_r__delimiter_      = _def_.URL_DELIMITER
		_kw__data_          = _r_kws_.rsplit(_r__delimiter_, 1)
		_r__error__message_ = ""

		if len(_kw__data_) >= 2:
			_kw__url_ = _kw__data_[0].strip()
			_kw__id_  = _kw__data_[1].strip()

			if _kw__url_ and _kw__id_.isdigit():
				from bs4 import BeautifulSoup
				import random

				_head__index_ = random.randint(0, len(_def_.LIST_OF_HEADERS) - 1)
				_headers_ = {
					'accept':     '*/*',
					'origin':     'https://www.google.com',
					'referer':    'https://www.google.com/',
					'User-Agent': _def_.LIST_OF_HEADERS[_head__index_],
				}

				_proxy_url_ = getattr(_def_, "RESEARCH_PROXY_URL", None)
				_proxies_   = {"http": _proxy_url_, "https": _proxy_url_} if _proxy_url_ else None

				_automation__status_ = str('0')

				with _r_session_.get(
					_kw__url_,
					headers=_headers_,
					proxies=_proxies_,
					timeout=(10, 30),
				) as _resp_:
					if hasattr(_resp_, 'status_code'):
						_setting__records_  = _ms__record_.objects.filter(__raw__={'id': 1})
						_research__records_ = _kw__research_.objects.filter(__raw__={'id': int(_kw__id_)})

						_setting__records_.update(inc__daily_demand_count__0=1)
						_research__records_.update(inc__research_refresh_count=1)

						if _resp_.status_code == 200:
							_soup_ = BeautifulSoup(_resp_.text, "html.parser")
							_search__file_ = (
								os.getcwd()
								+ "/project/files/other/researchFile__"
								+ str(_kw__id_) + ".html"
							)

							_ele_           = "schema.org/SearchResultsPage"
							_content__html_ = _soup_.find("html")
							if _content__html_ and _content__html_.has_attr('itemtype'):
								if _content__html_['itemtype'].find(_ele_) > -1:
									_search__file_ = (
										os.getcwd()
										+ "/project/files/research/researchFile__"
										+ str(_kw__id_) + ".html"
									)
									_automation__status_ = str(_resp_.status_code)

							with _open_for_write_(_search__file_) as _f_:
								_f_.write(str(_soup_))

						elif _resp_.status_code == 429:
							_r__error__message_ = "PROXY TOO MANY REQUESTS ERROR"
						elif _resp_.status_code == 407:
							_r__error__message_ = "PROXY AUTHORIZATION ERROR"
						else:
							_r__error__message_ = "PROXY UNEXPECTED ERROR"

						if _automation__status_ == "200":
							return True, _kw__id_
						else:
							_wd_.coreLog(
								f" > RESEARCH - DESKTOP - {_r__error__message_}"
								f" >> KEYWORD ID: {_kw__id_}",
								"PROXY",
							)

	except Exception as _exp_:
		_wd_.coreLog(
			f" > RESEARCH - DESKTOP - PROXY REQUEST FUNCTION ERROR"
			f" >> KEYWORD ID: {_kw__id_} >>> ERROR MESSAGE: {_exp_}",
			"PROXY",
		)

	return False, _kw__id_
