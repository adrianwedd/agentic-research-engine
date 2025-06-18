import os
import time
from typing import List

import requests
from opentelemetry import trace

from services.monitoring.system_monitor import SystemMonitor

TTL_DAYS = float(os.getenv("LTM_TTL_DAYS", "30"))
TTL_SECONDS = TTL_DAYS * 24 * 3600
LTM_BASE_URL = os.getenv("LTM_BASE_URL", "http://agent-services")
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")


def main() -> None:
    monitor = SystemMonitor.from_otlp(OTEL_ENDPOINT)
    tracer = trace.get_tracer(__name__)

    try:
        resp = requests.get(
            f"{LTM_BASE_URL}/memory",
            params={"memory_type": "episodic", "limit": 10000},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:  # pragma: no cover - network error
        print(f"failed to fetch memories: {exc}")
        return
    records: List[dict] = resp.json().get("results", [])
    cutoff = time.time() - TTL_SECONDS
    pruned = 0
    for rec in records:
        last = rec.get("last_accessed") or rec.get("last_accessed_timestamp", 0)
        if last < cutoff and rec.get("id"):
            try:
                r = requests.delete(
                    f"{LTM_BASE_URL}/forget/{rec['id']}",
                    params={"memory_type": "episodic"},
                    json={"hard": True},
                    timeout=10,
                )
                if r.status_code == 200:
                    pruned += 1
            except requests.RequestException:
                continue  # best effort

    monitor.record_ltm_deletions(pruned)
    with tracer.start_as_current_span(
        "forget_job", attributes={"pruned": pruned, "ttl_days": TTL_DAYS}
    ):
        pass
    print(f"Pruned {pruned} stale memories older than {TTL_DAYS} days")


if __name__ == "__main__":
    main()
