from __future__ import annotations

"""Simplistic HTML scraper returning main article text."""

import os
import re
import time
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


def html_scraper(
    url: str, *, timeout: int = 10, retries: int = 2, backoff: float = 1.0
) -> str:
    """Return main body text extracted from a web page URL or file."""

    validated = validate_path_or_url(url)
    parsed = urlparse(url)

    if parsed.scheme in {"http", "https"}:
        html_text = None
        for attempt in range(retries + 1):
            try:
                resp = requests.get(validated, timeout=timeout)
                resp.raise_for_status()
                html_text = resp.text
                break
            except (
                requests.RequestException
            ) as exc:  # pragma: no cover - network errors
                if attempt >= retries:
                    raise ValueError(f"Failed to fetch HTML: {exc}") from exc
                time.sleep(backoff * 2**attempt)
        if html_text is None:
            raise ValueError("Failed to fetch HTML")
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
        for attempt in range(retries + 1):
            try:
                resp = requests.get(f"https://r.jina.ai/{validated}", timeout=timeout)
                resp.raise_for_status()
                rendered = resp.text
                md_index = rendered.find("Markdown Content:")
                if md_index != -1:
                    rendered = rendered[md_index + len("Markdown Content:") :]
                text = rendered.strip()
                break
            except requests.RequestException:
                if attempt >= retries:
                    text = ""
                else:
                    time.sleep(backoff * 2**attempt)

    if not text:
        raise ValueError("No extractable text found in HTML")

    return text
