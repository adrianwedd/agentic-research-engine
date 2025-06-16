from __future__ import annotations

"""GitHub Search API wrapper with basic rate limit handling."""

import os
import time
from typing import Dict, List, Optional

import requests


def _github_request(
    endpoint: str,
    params: Dict[str, str],
    *,
    token: str,
    retries: int,
    backoff: float,
) -> Dict[str, object]:
    """Perform a GET request to the GitHub API with exponential backoff."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com{endpoint}"
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            if resp.status_code == 403 and "rate limit" in resp.text.lower():
                reset = resp.headers.get("X-RateLimit-Reset")
                if reset and reset.isdigit():
                    wait = max(0, int(reset) - int(time.time()))
                else:
                    wait = backoff * 2**attempt
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:  # pragma: no cover - network errors
            if attempt >= retries:
                raise ValueError(f"GitHub API request failed: {exc}") from exc
            time.sleep(backoff * 2**attempt)
    raise ValueError("GitHub API request failed")


def github_search(
    query: str,
    *,
    search_type: str = "repositories",
    token: Optional[str] = None,
    top_k: int = 5,
    retries: int = 2,
    backoff: float = 1.0,
) -> List[Dict[str, str]]:
    """Search GitHub for repositories, code, or issues.

    Parameters
    ----------
    query: str
        Search query string.
    search_type: str
        One of ``"repositories"``, ``"code"``, or ``"issues"``.
    token: str | None
        Personal access token. Defaults to ``GITHUB_TOKEN`` environment variable.
    top_k: int
        Maximum number of results to return.
    retries: int
        Number of retry attempts on failure.
    backoff: float
        Base seconds to wait between retries.

    Returns
    -------
    List[Dict[str, str]]
        A list of results with fields depending on ``search_type``.
    """

    token = token or os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("Missing GitHub token")
    if not query.strip():
        raise ValueError("Query string cannot be empty")

    endpoint_map = {
        "repositories": "/search/repositories",
        "code": "/search/code",
        "issues": "/search/issues",
    }
    if search_type not in endpoint_map:
        raise ValueError(f"Invalid search_type: {search_type}")

    params = {"q": query, "per_page": str(top_k)}
    data = _github_request(
        endpoint_map[search_type],
        params,
        token=token,
        retries=retries,
        backoff=backoff,
    )

    items = data.get("items", [])
    results: List[Dict[str, str]] = []
    if search_type == "repositories":
        for item in items:
            results.append(
                {
                    "url": item.get("html_url", ""),
                    "name": item.get("full_name", ""),
                    "description": item.get("description") or "",
                }
            )
    elif search_type == "code":
        for item in items:
            repo = item.get("repository", {})
            results.append(
                {
                    "url": item.get("html_url", ""),
                    "path": item.get("path", ""),
                    "repository": repo.get("full_name", ""),
                }
            )
    else:  # issues
        for item in items:
            results.append(
                {
                    "url": item.get("html_url", ""),
                    "title": item.get("title", ""),
                    "state": item.get("state", ""),
                }
            )
    return results
