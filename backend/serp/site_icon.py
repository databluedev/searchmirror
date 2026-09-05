"""Serve a site's favicon from the server, so the browser never fetches it.

`site_mark.js` used to render `<img src="https://<competitor>/favicon.ico">`.
On /competitors that is one request per row straight from the user's browser to
a third-party SEO vendor -- 47 of them in one page load, leaving 8 tracking
cookies in the profile of someone who was looking at a table, not visiting
those sites. Every one of those requests also carried the user's IP and, on the
older browsers, a Referer naming this instance.

This endpoint puts the server in between: it fetches the icon once, caches it on
disk, and serves the bytes. The browser talks only to this instance.

FAILURE IS 204, NOT 404
-----------------------
Most domains have no usable icon, and half of the rest answer with an HTML
error page at /favicon.ico. Every one of those is a normal outcome, not an
error: the frontend falls back to its letter tile. A 404 would fill the console
with red and a 500 would look like this instance was broken, so anything short
of real image bytes is 204 No Content.

THREAT MODEL
------------
This is a view that fetches a URL a caller supplies, which is the classic SSRF
shape. The guards, in the order they apply:

1. **Authentication.** DRF's default IsAuthenticated. An unauthenticated
   fetch-any-URL endpoint is a gift to anyone scanning for one.
2. **An allowlist of the caller's own domains.** The host must already appear in
   this account's projects, competitors, competitor analysis or Geo citations --
   the only places the UI ever renders an icon. This is the guard that matters
   most, because it removes the primitive entirely rather than filtering it: an
   authenticated user cannot point the server at a host of their choosing, so
   the instance cannot be used to probe, to launder requests, or to reach
   anything an attacker picked. See `_allowed_host`.
3. **The resolved IP, not the string.** Names are resolved here and every
   returned address must be globally routable. `internal.example.com` resolving
   to 10.0.0.5 is refused even though the string looks public.
4. **The address actually connected to.** Checked again on the live socket after
   the connection is up, which is what closes DNS rebinding: a name that passed
   step 3 and re-resolved to 127.0.0.1 before connect is caught here, before a
   single byte of the response is used.
5. **https only, redirects capped and re-validated**, a hard timeout, a hard
   size cap, and a content check by both header and magic bytes -- because a
   domain can serve anything it likes at /favicon.ico, including HTML.

SVG is refused despite being an image. It is a script-bearing document, and an
`image/svg+xml` response served from this origin executes in the context of
this origin if it is ever opened directly.
"""

import hashlib
import ipaddress
import json
import os
import socket
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view


# Long enough that a project's icons are fetched once a fortnight, short enough
# that a rebrand is picked up without an operator clearing anything.
HIT_TTL = 14 * 24 * 60 * 60
# Negative results are cached too, and for a day -- otherwise a domain with no
# icon costs a 3-second timeout on every page view, for every user, forever.
MISS_TTL = 24 * 60 * 60

# Per-connection budget: (connect, read). An icon is decoration; no page should
# wait on it.
TIMEOUT = (2, 3)

# Total wall-clock budget for everything this view does on a cache miss --
# resolution, both candidate hosts, every redirect hop and the streamed read.
# `requests`' read timeout is per socket read, not per request, so a host that
# dribbles one byte at a time stays inside TIMEOUT forever; only a deadline
# bounds the whole thing.
#
# 4.5s is not arbitrary. The frontend aborts at 6000ms, and the rest of this
# request -- allowlist queries, cache write, response -- was measured at up to
# ~0.45s, so the fetch must finish inside roughly 5s or a legitimate icon is
# abandoned client-side after we already paid for it. If this number moves, the
# client's 6000ms has to move with it.
FETCH_BUDGET = 4.5
# Icons are small. 100KB is generous for a .ico and still a hard ceiling on what
# a hostile host can make this process hold in memory.
MAX_BYTES = 100 * 1024
MAX_REDIRECTS = 2

# What the browser may cache, on a hit AND on a 204 alike -- the client's
# in-memory dedupe map dies on every hard navigation, so the HTTP cache is what
# makes the second page load free, and a dead domain not being re-requested
# matters as much as a live one being reused. Shorter than HIT_TTL on purpose:
# the disk cache is what protects the remote host, this only saves a round trip.
#
# `private`, not `public`: the response is served on an authenticated request, so
# no shared proxy has any business holding a copy of it.
BROWSER_MAX_AGE = 24 * 60 * 60
BROWSER_CACHE_CONTROL = "private, max-age=%d" % BROWSER_MAX_AGE

# Magic bytes, checked against the payload rather than trusting Content-Type.
# The offset is where the signature starts; WEBP identifies itself 8 bytes in,
# after the RIFF chunk length.
_SIGNATURES = (
    (0, b"\x00\x00\x01\x00", "image/x-icon"),
    (0, b"\x89PNG\r\n\x1a\n", "image/png"),
    (0, b"GIF87a", "image/gif"),
    (0, b"GIF89a", "image/gif"),
    (0, b"\xff\xd8\xff", "image/jpeg"),
    (0, b"BM", "image/bmp"),
    (8, b"WEBP", "image/webp"),
)

_LABEL_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-")

# RFC 6052's well-known NAT64 prefix. Docker's own resolver hands these back for
# every public name in some environments, so this is not a theoretical shape --
# and the low 32 bits are a literal IPv4 address, which makes `64:ff9b::7f00:1`
# a spelling of 127.0.0.1 that walks past every v4 range check.
_NAT64_WELL_KNOWN = ipaddress.ip_network("64:ff9b::/96")


def _cache_dir():
    path = Path(settings.BASE_DIR) / "files" / "siteicons"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _normalise_host(value):
    """A bare lowercase hostname, or "" if this is not one.

    Deliberately strict, and deliberately refuses IP literals: nothing the UI
    renders an icon for is an address, and "the caller may not name an address"
    is a much easier rule to verify than "these address ranges are forbidden".
    The range check still runs on whatever the name resolves to -- this only
    removes the shortest path to it.
    """
    host = str(value or "").strip().lower()
    if "//" in host:
        host = host.split("//", 1)[1]
    for separator in ("/", "?", "#"):
        host = host.split(separator, 1)[0]
    if "@" in host:
        return ""
    if ":" in host:
        # A port, or an IPv6 literal. Neither is acceptable here.
        return ""
    host = host.strip(".")
    if not host or len(host) > 253 or "." not in host:
        return ""
    try:
        ipaddress.ip_address(host)
        return ""
    except ValueError:
        pass
    for label in host.split("."):
        if not label or len(label) > 63 or label[0] == "-" or label[-1] == "-":
            return ""
        if not set(label) <= _LABEL_CHARS:
            return ""
    return host[4:] if host.startswith("www.") else host


def _is_public_address(text):
    """True only for a globally routable unicast address.

    `is_global` already excludes 10/8, 172.16/12, 192.168/16, 127/8, 169.254/16,
    100.64/10, ::1 and fc00::/7. The explicit flags are kept beside it because
    they are the requirement, and a reader should not have to know what
    `is_global` covers to check that it covers them.
    """
    try:
        address = ipaddress.ip_address(text)
    except ValueError:
        return False
    # A v6 address can carry a v4 one, and each wrapper is a way to spell a
    # forbidden address in a form that passes an IPv4 range check:
    # ::ffff:127.0.0.1 is loopback in v6 clothing, 2002:7f00:1:: reaches it via
    # 6to4, 64:ff9b::7f00:1 via NAT64 and 2001:0::...:7f00:1 via Teredo. Unwrap
    # first, then apply the ranges to what is actually being addressed.
    if isinstance(address, ipaddress.IPv6Address):
        teredo = address.teredo
        mapped = (
            address.ipv4_mapped
            or address.sixtofour
            or (teredo[1] if teredo else None)
        )
        if mapped is None and address in _NAT64_WELL_KNOWN:
            mapped = ipaddress.IPv4Address(int(address) & 0xFFFFFFFF)
        if mapped is not None:
            address = mapped
    if (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        return False
    return address.is_global


def _resolves_publicly(host):
    """True when the host resolves, and EVERY address it resolves to is public.

    Every, not any: a name with one public and one loopback record would
    otherwise be reachable on whichever the connect happened to pick.
    """
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return False
    addresses = {info[4][0] for info in infos}
    return bool(addresses) and all(_is_public_address(a) for a in addresses)


def _peer_is_public(response):
    """Re-check the address the socket actually connected to.

    This is the anti-rebinding check. If the underlying socket cannot be
    reached -- a urllib3 internal, and not a contract -- we fall back to the
    pre-connect resolution rather than failing open silently; that is recorded
    here so the weaker case is visible rather than assumed away.
    """
    try:
        peer = response.raw._connection.sock.getpeername()[0]
    except Exception:
        return True
    return _is_public_address(peer)


def _sniff(payload, content_type):
    """The real content type of these bytes, or "" if they are not an image.

    Both checks must pass. Magic bytes alone would accept an icon served as
    `text/html` by a host that is confused rather than hostile; the header alone
    accepts an HTML error page a host merely *labelled* `image/x-icon`, which is
    what /favicon.ico returns on a large fraction of real sites.
    """
    declared = (content_type or "").split(";", 1)[0].strip().lower()
    if not declared.startswith("image/") or declared == "image/svg+xml":
        return ""
    for offset, signature, mime in _SIGNATURES:
        if payload[offset:offset + len(signature)] == signature:
            return mime
    return ""


def _remaining(deadline):
    return deadline - time.monotonic()


def _read_capped(response, deadline):
    """The body, or None if it runs past the cap or the deadline.

    Streamed and counted rather than `response.content`, which would read
    whatever the host decided to send before anyone could object -- and checked
    against the clock as well as the byte count, because a slow trickle is the
    other way to make a caller wait forever without ever tripping a read
    timeout.
    """
    payload = b""
    for chunk in response.iter_content(chunk_size=8192):
        payload += chunk
        if len(payload) > MAX_BYTES or _remaining(deadline) <= 0:
            return None
    return payload or None


def _fetch(host, deadline):
    """`(bytes, content_type)` for a host's icon, or `(None, "")`.

    Tries the bare host and then the www. form: plenty of sites serve the icon
    on only one of the two, and a letter tile for a site that has a perfectly
    good logo is the bug this endpoint exists to fix. Both attempts share one
    deadline, so two slow hosts cannot add up to twice the budget.
    """
    for candidate in (host, "www." + host):
        payload, content_type = _fetch_one(
            "https://%s/favicon.ico" % candidate, deadline
        )
        if payload:
            return payload, content_type
    return None, ""


def _fetch_one(url, deadline):
    session = requests.Session()
    try:
        for _ in range(MAX_REDIRECTS + 1):
            scheme, _, rest = url.partition("://")
            if scheme != "https":
                return None, ""
            host = rest.split("/", 1)[0].split(":", 1)[0]
            # Re-validated on every hop, not just the first: a redirect is a URL
            # the remote host chose, which is exactly the input this endpoint
            # does not trust.
            if not _normalise_host(host) or not _resolves_publicly(host):
                return None, ""

            remaining = _remaining(deadline)
            # Below this there is no point starting: a connect that lands with
            # nothing left to read the body just burns what budget is left.
            if remaining < 0.5:
                return None, ""

            connect_timeout, read_timeout = TIMEOUT
            response = session.get(
                url,
                timeout=(min(connect_timeout, remaining), min(read_timeout, remaining)),
                stream=True,
                allow_redirects=False,
                headers={"User-Agent": "SearchMirror-icon/1.0", "Accept": "image/*"},
            )
            try:
                if not _peer_is_public(response):
                    return None, ""
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location") or ""
                    if not location:
                        return None, ""
                    # Resolved against the current URL, because real hosts send
                    # every legal form: brightdata.com answers with the
                    # scheme-relative `//brightdata.com/favicon.ico?md5=...`,
                    # and plenty send a bare path. A raw string check would
                    # reject both and draw a letter tile for a site that has an
                    # icon. The https and address checks run on the result, so
                    # a redirect to http:// or to an internal name still stops
                    # at the top of the loop.
                    url = urljoin(url, location)
                    continue
                if response.status_code != 200:
                    return None, ""
                payload = _read_capped(response, deadline)
                if not payload:
                    return None, ""
                content_type = _sniff(payload, response.headers.get("Content-Type"))
                return (payload, content_type) if content_type else (None, "")
            finally:
                response.close()
    except Exception:
        # A DNS failure, a TLS failure, a timeout and a hostile host are the
        # same outcome to the caller: no icon. None of them is worth a 500.
        return None, ""
    finally:
        session.close()
    return None, ""


def _cache_paths(host):
    digest = hashlib.sha256(host.encode("utf-8")).hexdigest()[:32]
    directory = _cache_dir()
    return directory / (digest + ".meta"), directory / (digest + ".img")


def _cache_read(host):
    """`(payload, content_type)` on a hit, `(None, "")` on a cached miss, or None.

    None means "nothing cached, go and fetch"; a cached miss is a real answer
    and must be distinguishable from it, or a dead domain is retried on every
    page view -- which is the cost this cache exists to avoid.
    """
    meta_path, image_path = _cache_paths(host)
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    age = time.time() - float(meta.get("at") or 0)
    if age > (HIT_TTL if meta.get("ok") else MISS_TTL):
        return None
    if not meta.get("ok"):
        return None, ""
    try:
        return image_path.read_bytes(), meta.get("type") or "image/x-icon"
    except Exception:
        # Metadata says there is an image and there is not. Treat it as no
        # cache entry at all rather than as a miss, so the next request repairs
        # it instead of serving a blank for a day.
        return None


def _cache_write(host, payload, content_type):
    meta_path, image_path = _cache_paths(host)
    try:
        if payload:
            # Image first, metadata second: a reader that sees the metadata is
            # guaranteed the bytes are already there.
            tmp = image_path.with_suffix(".tmp")
            tmp.write_bytes(payload)
            os.replace(str(tmp), str(image_path))
        meta_path.write_text(
            json.dumps({"ok": bool(payload), "type": content_type, "at": time.time()}),
            encoding="utf-8",
        )
    except Exception:
        # An unwritable cache directory must not stop the icon being served.
        pass


def _allowed_host(userid, host):
    """True when this host is one this account already sees somewhere.

    Every icon the UI draws is for a domain that came out of this account's own
    data: its projects, the competitors it tracks, the competitor list its
    analysis produced, or the sources cited in its Geo Citations answers. So the
    endpoint serves exactly those and refuses everything else, which turns "an
    authenticated open proxy" into "a cache of icons the user was already
    looking at".

    Checked in cost order, cheapest first, and stopping at the first match --
    the common case is the project's own domain, one indexed query.
    """
    from competitor.models import CompProject
    from serp.models import Groups

    group_ids = list(
        Groups.objects.filter(fk_user_id=userid).values_list("id", flat=True)
    )

    domains = Groups.objects.filter(fk_user_id=userid).values_list(
        "domain_name", flat=True
    )
    if any(_normalise_host(domain) == host for domain in domains):
        return True

    domains = CompProject.objects.filter(fk_user_id=userid).values_list(
        "cp_domain_name", flat=True
    )
    if any(_normalise_host(domain) == host for domain in domains):
        return True

    # The competitor analysis writes its discovered domains to a file per group
    # rather than to the database (competitor/compfiles.py). Those are the rows
    # on /competitors, and they are exactly the 47 requests this endpoint
    # replaced, so they have to be in the allowlist.
    for group_id in group_ids:
        path = os.path.join(
            os.getcwd(), "competitor", "ai_files", "domains",
            "aiGroup__%s.json" % group_id,
        )
        try:
            with open(path) as handle:
                discovered = json.loads(handle.read())
        except Exception:
            continue
        if any(_normalise_host(domain) == host for domain in discovered):
            return True

    return _cited_by(userid, host)


def _cited_by(userid, host):
    """True when this host appears in the account's stored Geo citations."""
    from llmtracker.models import LLMPrompt, LLMPromptAnalytics

    prompt_ids = list(
        LLMPrompt.objects.filter(fk_user_id=userid).values_list("prompt_id", flat=True)
    )
    if not prompt_ids:
        return False
    for citations in LLMPromptAnalytics.objects.filter(
        fk_prompt_id__in=prompt_ids
    ).values_list("citations", flat=True):
        if any(_normalise_host(domain) == host for domain in (citations or [])):
            return True
    return False


def _no_content():
    response = HttpResponse(status=204)
    response["Cache-Control"] = BROWSER_CACHE_CONTROL
    # A 204 has no body, so the Content-Type Django puts on every HttpResponse
    # describes nothing. Left in place it says "text/html" to a consumer that
    # is deciding whether it received an image.
    del response["Content-Type"]
    return response


@api_view(["GET"])
def site_icon(request):
    """GET /site-icon?domain=<host> -> the site's icon bytes, or 204.

    The account comes from the token, via DRF's `request.user`, and NOT from a
    `userid` the caller supplies. That is deliberate and it is the opposite of
    what the rest of this API does: every ownership bug in `account/ownership.py`
    exists because a view believed a userid in the request instead of the one
    behind the credential. There is nothing to believe here -- the allowlist is
    the authenticated account's, full stop. An explicit `userid` may still be
    passed (the ownership middleware refuses it if it is not the caller's) but
    it is not read.

    A team member's token authenticates as the owning Account, so a member sees
    the owner's whole icon allowlist rather than only their assigned projects.
    That is a favicon for a domain the product displays publicly, not project
    data, and scoping it per project would mean a per-project allowlist query on
    every icon.

    NOTE FOR THE FRONTEND: this needs the `Authorization` header, and an
    `<img src>` cannot send one. Fetch it with `fetch()` and hand the blob to
    `URL.createObjectURL`, or fall back to the letter tile on any non-200.
    """
    userid = getattr(request.user, "id", None)
    host = _normalise_host(request.GET.get("domain"))
    if not userid or not host:
        return _no_content()

    if not _allowed_host(userid, host):
        return _no_content()

    cached = _cache_read(host)
    if cached is None:
        deadline = time.monotonic() + FETCH_BUDGET
        if not _resolves_publicly(host):
            # Cached as a miss: a host that resolves privately today is a
            # misconfiguration or an attempt, and either way re-resolving it on
            # every page view helps nobody.
            _cache_write(host, None, "")
            return _no_content()
        payload, content_type = _fetch(host, deadline)
        _cache_write(host, payload, content_type)
    else:
        payload, content_type = cached

    if not payload:
        return _no_content()

    response = HttpResponse(payload, content_type=content_type)
    response["Cache-Control"] = BROWSER_CACHE_CONTROL
    # Belt and braces on bytes fetched from a third party: never sniffed into
    # something executable, never able to load anything of its own.
    response["X-Content-Type-Options"] = "nosniff"
    response["Content-Security-Policy"] = "default-src 'none'; sandbox"
    return response
