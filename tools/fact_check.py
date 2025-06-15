from __future__ import annotations

"""Wrapper for a fact-checking API."""

import os
import time
from typing import Dict, List, Optional

import requests


def fact_check_claim(
    claim: str,
    *,
    api_key: Optional[str] = None,
    language: str = "en",
    retries: int = 2,
    backoff: float = 1.0,
) -> Dict[str, object]:
    """Validate a claim using a third-party fact-checking API.

    Parameters
    ----------
    claim: str
        Text of the claim to verify.
    api_key: str | None
        API key for the external service. Defaults to the ``FACT_CHECK_API_KEY``
        environment variable.
    language: str
        Language code for the claim review results. Defaults to ``"en"``.
    retries: int
        Number of retry attempts on failure. Defaults to ``2``.
    backoff: float
        Base seconds to wait between retries. Each retry waits ``backoff`` * 2**attempt.

    Returns
    -------
    Dict[str, object]
        ``{"claim": claim, "rating": str, "source_links": List[str]}``.
    """
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("Claim text cannot be empty")

    api_key = api_key or os.getenv("FACT_CHECK_API_KEY")
    if not api_key:
        raise ValueError("Missing API key for fact checking")

    endpoint = os.getenv(
        "FACT_CHECK_API_ENDPOINT",
        "https://factchecktools.googleapis.com/v1alpha1/claims:search",
    )
    params = {"query": claim, "languageCode": language, "key": api_key}

    data: Dict[str, object] | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(endpoint, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            break
        except requests.RequestException as exc:  # pragma: no cover - network errors
            if attempt >= retries:
                raise ValueError(f"Fact check API request failed: {exc}") from exc
            time.sleep(backoff * 2**attempt)

    claims = data.get("claims", []) if isinstance(data, dict) else []
    rating = "unverified"
    links: List[str] = []
    if claims:
        review = None
        if isinstance(claims[0], dict):
            reviews = claims[0].get("claimReview", [])
            if reviews and isinstance(reviews[0], dict):
                review = reviews[0]
        if review:
            rating = (
                review.get("text")
                or (review.get("reviewRating", {}) or {}).get("text")
                or rating
            )
            url = review.get("url")
            if url:
                links.append(url)

    return {"claim": claim, "rating": rating, "source_links": links}
