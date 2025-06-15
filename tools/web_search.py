from __future__ import annotations

"""Wrapper for an external web search API."""

import os
from typing import Dict, List, Optional

import requests


def web_search(
    query: str, *, api_key: Optional[str] = None, top_k: int = 5
) -> List[Dict[str, str]]:
    """Perform a web search via a commercial API.

    Parameters
    ----------
    query: str
        Query string to search for.
    api_key: str | None
        API key for the external search service. Defaults to the ``SEARCH_API_KEY``
        environment variable.
    top_k: int
        Maximum number of results to return.

    Returns
    -------
    List[Dict[str, str]]
        List of search results with ``url``, ``title``, and ``snippet`` fields.
    """
    api_key = api_key or os.getenv("SEARCH_API_KEY")
    if not api_key:
        raise ValueError("Missing API key for web search")

    endpoint = os.getenv("SEARCH_API_ENDPOINT", "https://api.serper.dev/search")
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": top_k}
    response = requests.post(endpoint, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("organic", []):
        url = item.get("link") or item.get("url")
        title = item.get("title")
        snippet = item.get("snippet") or item.get("snippetText")
        if url and title:
            results.append({"url": url, "title": title, "snippet": snippet or ""})
    return results
