"""No credential ships in this repository.

Added 2026-09-05, after GitHub's secret scanning found a hardcoded **Telegram
bot token** in `engine/project/machine/watchbot/automation_bot.py` minutes after
the first public push. The token belonged to the commercial predecessor's
operational alerting and posted engine status into a Telegram group this
project does not own.

It survived a pre-publication scan because that scan looked for the shapes I
thought of -- OpenAI, Google, GitHub, AWS, Slack, private keys -- and a Telegram
token is `digits:base64ish`, which matched none of them. A scan is only as good
as its pattern list, so the list lives here where it can be extended, and runs
on every commit rather than once by hand.

The whole `watchbot` package was removed rather than parameterised: it reported
to somebody else's channel, and operators already have EMERGENCY_MAIL.
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]

# (name, pattern). Add to this list; never narrow it to make a test pass.
PATTERNS = [
    ("Telegram bot token",    r"\b\d{8,10}:[A-Za-z0-9_-]{30,}\b"),
    ("Slack token",           r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    ("Slack/Discord webhook", r"https://(hooks\.slack\.com|discord(app)?\.com/api/webhooks)/[A-Za-z0-9/_-]+"),
    ("AWS access key id",     r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("Google API key",        r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    ("OpenAI key",            r"\bsk-(proj-)?[A-Za-z0-9]{20,}\b"),
    ("Anthropic key",         r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b"),
    ("Perplexity key",        r"\bpplx-[A-Za-z0-9]{20,}\b"),
    ("GitHub token",          r"\b(ghp|gho|ghs|ghu|ghr)_[A-Za-z0-9]{30,}\b"),
    ("GitHub fine-grained",   r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    ("Stripe live key",       r"\b(sk|rk|pk)_live_[A-Za-z0-9]{10,}\b"),
    ("SendGrid key",          r"\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}\b"),
    ("Twilio SID or key",     r"\b(AC|SK)[0-9a-fA-F]{32}\b"),
    ("Mailgun key",           r"\bkey-[0-9a-f]{32}\b"),
    ("Private key block",     r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("JSON Web Token",        r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ("Credentials in a URL",  r"[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s:@]+@[A-Za-z0-9.-]+"),
    ("Hardcoded assignment",
     r"(?i)\b(password|passwd|secret|api_?key|auth_?token|access_?token|client_?secret|bot_?token)\b"
     r"\s*[:=]\s*[\"'][^\"'\s]{12,}[\"']"),
]

# A line saying "put your key here" is not a key.
PLACEHOLDER = re.compile(
    r"(?i)(example|placeholder|change-me|your-|dummy|xxxx|<[a-z_]+>|sample|"
    r"local-dev-only|redacted|user:pass)"
)

# Deliberate, documented, and safe: `.env.example` ships a local MongoDB URI
# whose password is public on purpose. docker-compose.yml publishes that port on
# 127.0.0.1 only and the production overlay does not publish it at all.
ALLOWED = {
    (".env.example", "Credentials in a URL"),
}

# The generic "password = '...'" heuristic, and ONLY that one, is not applied
# inside tests/. Fixtures legitimately hold literal passwords for the seeded and
# probe accounts, and rewriting them to satisfy a regex would make the suite
# harder to read for no security gain. Every provider-specific pattern above
# still applies here -- a real key pasted into a test is still caught.
GENERIC = "Hardcoded assignment"

SKIP = re.compile(
    r"(node_modules|package-lock|pnpm-lock|"
    r"\.(png|jpg|jpeg|gif|ico|svg|ttf|otf|woff2?|eot|pdf|zip)$)"
)


def _tracked_files():
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, timeout=120
    ).stdout
    return [f.strip() for f in out.split("\n") if f.strip() and not SKIP.search(f)]


def test_no_credential_is_committed():
    findings = []
    for relative in _tracked_files():
        path = ROOT / relative
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            if len(line) > 2000:
                continue
            for name, pattern in PATTERNS:
                if not re.search(pattern, line):
                    continue
                if PLACEHOLDER.search(line) or (relative, name) in ALLOWED:
                    break
                if name == GENERIC and relative.startswith("tests/"):
                    break
                findings.append("%s\n        %s:%d\n        %s"
                                % (name, relative, number, line.strip()[:120]))
                break

    assert not findings, (
        "%d possible credential(s) are committed:\n\n    %s\n\n"
        "If it is real: remove it, ROTATE IT AT THE PROVIDER (it is public the "
        "moment it is pushed), and read it from the environment instead. If it "
        "is a placeholder, make that obvious in the text rather than widening "
        "the pattern." % (len(findings), "\n\n    ".join(findings))
    )


def test_the_telegram_alerting_stays_removed():
    """It reported to a channel this project does not own, over a token that
    was published. EMERGENCY_MAIL is the supported watchdog path."""
    assert not (ROOT / "engine/project/machine/watchbot").exists(), (
        "the watchbot package is back"
    )
    urls = (ROOT / "engine/project/machine/urls.py").read_text(encoding="utf-8")
    assert "watchbot" not in urls and "engine/bot" not in urls
    for req in ("engine/requirements.txt", "engine/requirements-prod.txt"):
        assert "telegram" not in (ROOT / req).read_text(encoding="utf-8").lower()
