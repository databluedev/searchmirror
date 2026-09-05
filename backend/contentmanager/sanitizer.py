"""Sanitize model output before the content editor renders it as HTML."""

import re

from bs4 import BeautifulSoup


_ALLOWED_TAGS = {
    "h1", "h2", "h3", "h4", "p", "ul", "ol", "li", "strong", "b", "em", "br"
}
_DANGEROUS_TAGS = {"script", "style", "iframe", "object", "embed", "form"}


def sanitize_article_html(value):
    """Return a small, attribute-free subset of article HTML."""
    text = str(value or "").strip()
    text = re.sub(r"^```(?:html)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text).strip()
    soup = BeautifulSoup(text, "html.parser")

    for tag in list(soup.find_all(_DANGEROUS_TAGS)):
        tag.decompose()
    for tag in list(soup.find_all(True)):
        if tag.name not in _ALLOWED_TAGS:
            tag.unwrap()
        else:
            tag.attrs = {}

    return "".join(str(node) for node in soup.contents).strip()
