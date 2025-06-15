from __future__ import annotations

"""Simplistic HTML scraper returning main article text."""

import requests
from bs4 import BeautifulSoup


def html_scraper(url: str, *, timeout: int = 10) -> str:
    """Return main body text extracted from a web page URL."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network errors
        raise ValueError(f"Failed to fetch HTML: {exc}") from exc

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(
        ["script", "style", "noscript", "header", "footer", "nav", "aside"]
    ):
        tag.decompose()

    article = soup.find("article") or soup.find("main")
    if article:
        text = article.get_text(separator="\n", strip=True)
    else:
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
        text = "\n".join(paragraphs)

    if not text.strip():
        raise ValueError("No extractable text found in HTML")
    return text
