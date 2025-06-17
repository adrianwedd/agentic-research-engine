from __future__ import annotations

import os
import time
from typing import Dict, List, Optional

import requests


def _endpoint(endpoint: Optional[str]) -> str:
    return endpoint or os.getenv("LTM_SERVICE_ENDPOINT", "http://127.0.0.1:8081")


def consolidate_memory(
    record: Dict,
    *,
    memory_type: str = "episodic",
    endpoint: Optional[str] = None,
    retries: int = 2,
    backoff: float = 1.0,
) -> str:
    url = f"{_endpoint(endpoint)}/memory"
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                url,
                json={"memory_type": memory_type, "record": record},
                headers={"X-Role": "editor"},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("id", "")
        except requests.RequestException as exc:
            if attempt >= retries:
                raise ValueError(f"Memory consolidation failed: {exc}") from exc
            time.sleep(backoff * 2**attempt)


def retrieve_memory(
    query: Dict,
    *,
    memory_type: str = "episodic",
    limit: int = 5,
    endpoint: Optional[str] = None,
    retries: int = 2,
    backoff: float = 1.0,
) -> List[Dict]:
    url = f"{_endpoint(endpoint)}/memory"
    for attempt in range(retries + 1):
        try:
            resp = requests.get(
                url,
                params={"memory_type": memory_type, "limit": str(limit)},
                json={"query": query},
                headers={"X-Role": "viewer"},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("results", [])
        except requests.RequestException as exc:
            if attempt >= retries:
                raise ValueError(f"Memory retrieval failed: {exc}") from exc
            time.sleep(backoff * 2**attempt)


def semantic_consolidate(
    payload: Dict | str,
    *,
    fmt: str = "jsonld",
    endpoint: Optional[str] = None,
    retries: int = 2,
    backoff: float = 1.0,
) -> List:
    url = f"{_endpoint(endpoint)}/semantic_consolidate"
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                url,
                json={"payload": payload, "format": fmt},
                headers={"X-Role": "editor"},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("result", [])
        except requests.RequestException as exc:
            if attempt >= retries:
                raise ValueError(f"Semantic consolidation failed: {exc}") from exc
            time.sleep(backoff * 2**attempt)


def propagate_subgraph(
    subgraph: Dict,
    *,
    endpoint: Optional[str] = None,
    retries: int = 2,
    backoff: float = 1.0,
) -> List[str]:
    """Send a subgraph consisting of entities and relations to the LTM service."""
    url = f"{_endpoint(endpoint)}/propagate_subgraph"
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                url,
                json=subgraph,
                headers={"X-Role": "editor"},
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json().get("ids", [])
        except requests.RequestException as exc:
            if attempt >= retries:
                raise ValueError(f"Subgraph propagation failed: {exc}") from exc
            time.sleep(backoff * 2**attempt)
