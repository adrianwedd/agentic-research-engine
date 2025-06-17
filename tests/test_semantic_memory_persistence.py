import os

import pytest

from services.ltm_service.semantic_memory import SemanticMemoryService


def test_semantic_memory_persists_between_instances():
    if not (
        os.getenv("NEO4J_URI")
        and os.getenv("NEO4J_USER")
        and os.getenv("NEO4J_PASSWORD")
    ):
        pytest.skip("neo4j not configured")

    service = SemanticMemoryService()
    rec_id = service.store_fact("A", "REL", "B")
    service.close()

    service = SemanticMemoryService()
    results = service.query_facts(subject="A", predicate="REL", object="B")
    service.forget_fact(rec_id, hard=True)
    service.close()

    assert any(r["id"] == rec_id for r in results)
