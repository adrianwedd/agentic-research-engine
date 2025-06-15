from __future__ import annotations

"""Simplistic HTML scraper returning main article text."""

import requests
from bs4 import BeautifulSoup
from readability import Document


def html_scraper(url: str, *, timeout: int = 10) -> str:
    """Return main body text extracted from a web page URL.

    This uses ``readability-lxml`` to isolate the main article content and
    strips common boilerplate tags. If no meaningful text is found, an error is
    raised.
    """
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise ValueError(f"Failed to fetch HTML: {exc}") from exc

    # Use readability to isolate the article HTML, falling back to full page
    doc = Document(resp.text)
    article_html = doc.summary(html_partial=True)
    soup = BeautifulSoup(article_html, "html.parser")
    for tag in soup(
        ["script", "style", "noscript", "header", "footer", "nav", "aside"]
    ):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup
    paragraphs = [p.get_text(strip=True) for p in article.find_all("p")]
    text = "\n".join(paragraphs)
    if not paragraphs:
        raise ValueError("Page appears to require JavaScript rendering")

    if not text.strip():
        raise ValueError("No extractable text found in HTML")
    return text
