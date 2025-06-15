from __future__ import annotations

"""Simplistic HTML scraper returning main article text."""

import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from readability import Document

from .validation import validate_path_or_url


def html_scraper(url: str, *, timeout: int = 10) -> str:
    """Return main body text extracted from a web page URL or file."""

    validated = validate_path_or_url(url)
    parsed = urlparse(url)

    if parsed.scheme in {"http", "https"}:
        try:
            resp = requests.get(validated, timeout=timeout)
            resp.raise_for_status()
            html_text = resp.text
        except requests.RequestException as exc:  # pragma: no cover - network errors
            raise ValueError(f"Failed to fetch HTML: {exc}") from exc
    else:
        if not os.path.exists(validated):
            raise FileNotFoundError(validated)
        html_text = Path(validated).read_text(encoding="utf-8", errors="ignore")

    # Use readability to isolate the article HTML, falling back to full page
    doc = Document(html_text)
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
