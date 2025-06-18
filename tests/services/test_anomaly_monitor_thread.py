# flake8: noqa: E402
import sys
import time
import types

sys.modules.setdefault(
    "services.monitoring.system_monitor", types.SimpleNamespace(SystemMonitor=object)
)

from services.ltm_service.episodic_memory import EpisodicMemoryService, InMemoryStorage


def test_anomaly_monitor_background_job(weaviate_vector_store):
    storage = InMemoryStorage()
    vector_store = weaviate_vector_store
    service = EpisodicMemoryService(storage, vector_store=vector_store)

    embeds = [[0.1 * i, 0.1 * i] for i in range(5)] + [[10.0, 10.0]]
    idx = 0

    def _fake_embed(_texts, *, attempts=3):
        nonlocal idx
        if idx < len(embeds):
            vec = embeds[idx]
            idx += 1
        else:
            vec = embeds[-1]
        return [vec]

    service._embed_with_retry = _fake_embed

    orig_cluster = service._cluster_and_detect

    def _patched_cluster():
        orig_cluster(n_clusters=1, z_thresh=1.0)

    service._cluster_and_detect = _patched_cluster

    for i in range(5):
        rid = storage.save({"task_context": {"i": i}})
        vector_store.add(
            [0.1 * i, 0.1 * i],
            {"id": rid, "chunk_index": 0, "text": "", "categories": []},
        )

    outlier_id = storage.save({"task_context": {"i": "out"}})
    vector_store.add(
        [10.0, 10.0], {"id": outlier_id, "chunk_index": 0, "text": "", "categories": []}
    )

    service.start_anomaly_monitor(0.1)
    time.sleep(0.3)
    service.stop_anomaly_monitor()

    flagged = service.review_anomalies()
    assert outlier_id in flagged
