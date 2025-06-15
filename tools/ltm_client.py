from __future__ import annotations

import os
from typing import Dict, List, Optional

import requests


def _endpoint(endpoint: Optional[str]) -> str:
    return endpoint or os.getenv("LTM_SERVICE_ENDPOINT", "http://127.0.0.1:8081")


def consolidate_memory(
    record: Dict,
    *,
    memory_type: str = "episodic",
    endpoint: Optional[str] = None,
) -> str:
    url = f"{_endpoint(endpoint)}/consolidate"
    resp = requests.post(
        url, json={"memory_type": memory_type, "record": record}, timeout=10
    )
    resp.raise_for_status()
    return resp.json().get("id", "")


def retrieve_memory(
    query: Dict,
    *,
    memory_type: str = "episodic",
    limit: int = 5,
    endpoint: Optional[str] = None,
) -> List[Dict]:
    url = f"{_endpoint(endpoint)}/retrieve"
    resp = requests.get(
        url,
        params={"memory_type": memory_type, "limit": str(limit)},
        json={"query": query},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])
