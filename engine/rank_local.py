"""Rank the locally-seeded keywords through the engine's real DataBlue pipeline.

Uses automation_proxy.__automation_fetch_all__ -- the same function production
calls -- but scoped to this machine's seeded keywords so the credit spend is
bounded and predictable (1 request per keyword, DATABLUE_PAGES pages each).

Run: docker compose exec engine python rank_local.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

import django  # noqa: E402

django.setup()

from django.apps import apps  # noqa: E402
from django.utils import timezone  # noqa: E402
from project.machine import automation_proxy as proxy  # noqa: E402

def _account_prefs():
    """serp_depth / serp_key from the account, so a run bills what the UI shows."""
    try:
        AU = apps.get_model("machine", "DAccountUsage")
        row = AU.objects.first()
        return (int(getattr(row, "serp_depth", 0) or 0) or None,
                getattr(row, "serp_key", "") or "")  # ciphertext; decrypted below
    except Exception:
        return None, ""

DKeyword = apps.get_model("machine", "DKeyword")

rows = list(DKeyword.objects.all())
if not rows:
    sys.exit("no keywords found -- run the tracker seed first")

_depth, _acct_token = _account_prefs()
# serp_key is stored encrypted; the raw column is a 'v1:' token, not a key.
try:
    from shared.keycrypto import decrypt_key
    _acct_key = decrypt_key(_acct_token) if _acct_token else ""
except Exception:
    _acct_key = ""

items = {
    str(k.id): {
        "id": k.id,
        "keyword": k.keyword,
        "platform": k.platform,
        "language": k.language_code or "en",
        "isocode": k.isocode or "in",
        "domain": "google.co.in",
        "pages": _depth,
    }
    for k in rows
}

_pages = _depth or proxy._DATABLUE_PAGES_
print(f"ranking {len(items)} keywords via DataBlue "
      f"(pages={_pages}, ~{len(items) * _pages} page-credits)"
      f"{'' if _depth else '  [account depth unset -- using module default]'}")
print()

# _acct_key was read above and then dropped, so every local run billed the
# instance key. Pass it through like the automation paths now do.
results = proxy.__automation_fetch_all__(items, 5, _acct_key or None)   # concurrency 5, gentle

ok = 0
# __automation_fetch_all__ returns a list of result dicts, each carrying its
# own item id -- normalise to (id, payload) pairs.
if isinstance(results, dict):
    pairs = list(results.items())
else:
    pairs = [(str((r or {}).get("item_id") or (r or {}).get("id")), r) for r in (results or [])]

for item_id, payload in pairs:
    if item_id not in items:
        print(f"  <unmatched id {item_id}> keys={list((payload or {}).keys())[:6]}")
        continue
    kw = items[str(item_id)]["keyword"]
    data = (payload or {}).get("data") or {}
    organic = data.get("organic") or data.get("organic_results") or []
    if not organic:
        print(f"  {kw:32} no organic results ({(payload or {}).get('status')})")
        continue
    ok += 1
    k = DKeyword.objects.get(id=int(item_id))
    # match against the keyword's own target domain, not a hardcoded one
    target = (k.target or k.site_url or "").replace("www.", "").strip().lower()
    position = 0
    for o in organic:
        link = str(o.get("url") or o.get("link") or "").lower()
        if target and target in link:
            position = int(o.get("position") or o.get("rank") or 0)
            break
    history = list(k.rank or [])
    history.append(position)
    k.rank = history[-30:]
    k.ranknow = position
    k.top_rank = min([p for p in k.rank if p] or [0]) or 0
    k.lastranked_date = timezone.now()
    k.auto_call_status = "done"
    k.save()
    top = organic[0]
    print(f"  {kw:32} {len(organic):>2} results | {target} at #{position}" if position else f"  {kw:32} {len(organic):>2} results | {target} not in top {len(organic)}")
    print(f"     #1 {str(top.get('title'))[:56]}")

print()
print(f"done -- {ok}/{len(items)} keywords returned live SERP data")
