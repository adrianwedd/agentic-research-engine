from __future__ import annotations

"""Client for publishing reputation events to the Reputation Service."""

import os
import time
from typing import Any, Dict, Optional

import requests


def _endpoint(url: Optional[str]) -> str:
    return url or os.getenv(
        "REPUTATION_API_URL", "http://localhost:8000/api/v1/evaluations"
    )


def _token(tok: Optional[str]) -> str | None:
    return tok or os.getenv("REPUTATION_API_TOKEN")


def publish_reputation_event(
    payload: Dict[str, Any],
    *,
    url: Optional[str] = None,
    token: Optional[str] = None,
    retries: int = 2,
    backoff: float = 1.0,
) -> str:
    """Send a reputation feedback event to the service."""

    endpoint = _endpoint(url)
    headers = {}
    tok = _token(token)
    if tok:
        headers["Authorization"] = f"Bearer {tok}"

    for attempt in range(retries + 1):
        try:
            resp = requests.post(endpoint, json=payload, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return data.get("evaluation_id", "")
        except requests.RequestException as exc:
            if attempt >= retries:
                raise ValueError(f"Failed to publish reputation event: {exc}") from exc
            time.sleep(backoff * 2**attempt)
