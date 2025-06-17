from services.ltm_service.semantic_memory import (
    SemanticMemoryService,
    SpatioTemporalMemoryService,
)


def test_versioned_inserts_and_queries():
    service = SpatioTemporalMemoryService()
    fid = service.store_fact(
        "S",
        "P",
        "O",
        properties={"value": "v1", "valid_from": 0, "valid_to": 50, "tx_time": 10},
    )
    service.add_version(
        fid,
        value="v2",
        valid_from=50,
        valid_to=None,
        tx_time=20,
    )

    snap1 = service.get_snapshot(valid_at=25, tx_at=15)
    assert snap1 and snap1[0]["value"] == "v1"
    snap2 = service.get_snapshot(valid_at=75, tx_at=25)
    assert snap2 and snap2[0]["value"] == "v2"


def test_migration_from_semantic_memory():
    legacy = SemanticMemoryService()
    fid = legacy.store_fact("A", "REL", "B", properties={"value": "old"})
    new_service = SpatioTemporalMemoryService()
    new_service._facts = legacy._facts
    new_service._migrate()
    assert new_service._facts[0]["id"] == fid
    assert "history" in new_service._facts[0]
