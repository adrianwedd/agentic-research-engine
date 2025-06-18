# flake8: noqa: E402
import sys
import types

sys.modules.setdefault(
    "services.monitoring.system_monitor",
    types.SimpleNamespace(SystemMonitor=object),
)  # noqa: E402

from services.ltm_service.episodic_memory import EpisodicMemoryService, InMemoryStorage


def test_outlier_detection_flagged(weaviate_vector_store):
    storage = InMemoryStorage()
    vector_store = weaviate_vector_store
    service = EpisodicMemoryService(storage, vector_store=vector_store)

    embeds = [[0.1 * i, 0.1 * i] for i in range(5)] + [[10.0, 10.0]]

    def _fake_embed(_texts, *, attempts=3):
        return [embeds.pop(0)]

    service._embed_with_retry = _fake_embed

    for i in range(5):
        rec_id = storage.save({"task_context": {"i": i}})
        vector_store.add(
            [0.1 * i, 0.1 * i],
            {"id": rec_id, "chunk_index": 0, "text": "", "categories": []},
        )

    outlier_id = storage.save({"task_context": {"i": "out"}})
    vector_store.add(
        [10.0, 10.0], {"id": outlier_id, "chunk_index": 0, "text": "", "categories": []}
    )

    service._cluster_and_detect(n_clusters=1, z_thresh=1.0)
    flagged = service.review_anomalies()
    assert outlier_id in flagged
    metrics = service.get_anomaly_metrics()
    assert metrics["anomalies_detected"] >= 1
