from __future__ import annotations

"""Wrapper for an external web search API."""

import os
import time
from typing import Dict, List, Optional

import requests


def web_search(
    query: str,
    *,
    api_key: Optional[str] = None,
    top_k: int = 5,
    retries: int = 2,
    backoff: float = 1.0,
) -> List[Dict[str, str]]:
    """Perform a web search via a commercial API with simple retry logic.

    Parameters
    ----------
    query: str
        Query string to search for.
    api_key: str | None
        API key for the external search service. Defaults to the ``SEARCH_API_KEY``
        environment variable.
    top_k: int
        Maximum number of results to return.

    retries: int
        Number of retry attempts on failure. Defaults to ``2``.
    backoff: float
        Base seconds to wait between retries. Each retry waits ``backoff`` * 2
        ** attempt. Defaults to ``1.0``.

    Returns
    -------
    List[Dict[str, str]]
        List of search results with ``url``, ``title``, and ``snippet`` fields.
    """
    api_key = api_key or os.getenv("SEARCH_API_KEY")
    if not api_key:
        raise ValueError("Missing API key for web search")
    if not query.strip():
        raise ValueError("Query string cannot be empty")

    endpoint = os.getenv("SEARCH_API_ENDPOINT", "https://api.serper.dev/search")
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": top_k}

    for attempt in range(retries + 1):
        try:
            response = requests.post(
                endpoint, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()
            data = response.json()
            break
        except requests.RequestException as exc:  # pragma: no cover - network errors
            if attempt >= retries:
                raise ValueError(f"Web search failed: {exc}") from exc
            time.sleep(backoff * 2**attempt)

    results = []
    for item in data.get("organic", []):
        url = item.get("link") or item.get("url")
        title = item.get("title")
        snippet = item.get("snippet") or item.get("snippetText")
        if url and title:
            results.append({"url": url, "title": title, "snippet": snippet or ""})
    return results
