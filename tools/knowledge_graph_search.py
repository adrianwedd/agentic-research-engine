from __future__ import annotations

"""Tool for querying semantic knowledge graph via LTM service."""

from typing import Any, Dict, List, Optional

from .ltm_client import retrieve_memory


def knowledge_graph_search(
    query: Dict[str, Any],
    *,
    limit: int = 5,
    endpoint: Optional[str] = None,
    retries: int = 2,
    backoff: float = 1.0,
) -> List[Dict[str, Any]]:
    """Return facts matching ``query`` from semantic memory."""
    if not isinstance(query, dict):
        raise ValueError("query must be a dictionary")
    return retrieve_memory(
        query,
        memory_type="semantic",
        limit=limit,
        endpoint=endpoint,
        retries=retries,
        backoff=backoff,
    )
