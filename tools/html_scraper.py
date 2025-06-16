from __future__ import annotations

"""Simplistic HTML scraper returning main article text."""

import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup
from readability import Document

from .validation import validate_path_or_url


def _extract_main_text(html: str) -> str:
    """Extract article text from raw HTML using readability with trafilatura fallback."""
    doc = Document(html)
    article_html = doc.summary(html_partial=True)
    soup = BeautifulSoup(article_html, "html.parser")
    for tag in soup(
        ["script", "style", "noscript", "header", "footer", "nav", "aside"]
    ):
        tag.decompose()

    article = soup.find("article") or soup.find("main") or soup
    paragraphs = [p.get_text(strip=True) for p in article.find_all("p")]
    text = "\n".join(paragraphs).strip()
    if text:
        return text

    # Fallback to trafilatura if readability extraction fails
    text = trafilatura.extract(html, include_comments=False, include_tables=False) or ""
    return text.strip()


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

    text = _extract_main_text(html_text)
    if not text:
        # look for trivial inline script assigning to document.body.innerHTML
        match = re.search(
            r"document\.body\.innerHTML\s*=\s*(['\"])(.*?)\1",
            html_text,
            re.DOTALL,
        )
        if match:
            text = _extract_main_text(match.group(2))

    if not text:
        # Attempt JS-rendered snapshot via remote service
        try:
            resp = requests.get(f"https://r.jina.ai/{validated}", timeout=timeout)
            resp.raise_for_status()
            rendered = resp.text
            md_index = rendered.find("Markdown Content:")
            if md_index != -1:
                rendered = rendered[md_index + len("Markdown Content:") :]
            text = rendered.strip()
        except requests.RequestException:
            text = ""

    if not text:
        raise ValueError("No extractable text found in HTML")

    return text
