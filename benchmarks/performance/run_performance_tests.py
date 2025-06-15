from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import gevent
import psutil
from locust import HttpUser, between, task
from locust.env import Environment


class LTMUser(HttpUser):
    wait_time = between(0.01, 0.05)
    host = "http://127.0.0.1:8081"

    @task
    def consolidate_and_retrieve(self):
        record = {
            "task_context": {"query": "perf"},
            "execution_trace": {},
            "outcome": {"success": True},
        }
        self.client.post("/consolidate", json={"record": record})
        self.client.get("/retrieve?limit=1", json={"query": {"query": "perf"}})


def run_load_test(duration: int = 10, users: int = 20) -> dict[str, float | int]:
    env = Environment(user_classes=[LTMUser])
    env.create_local_runner()

    stop_evt = threading.Event()
    cpu_usage: list[float] = []
    mem_usage: list[float] = []

    proc = psutil.Process()

    def monitor() -> None:
        while not stop_evt.is_set():
            cpu_usage.append(psutil.cpu_percent(interval=1))
            mem_usage.append(proc.memory_info().rss / 1_048_576)

    monitor_t = threading.Thread(target=monitor)
    monitor_t.start()

    env.runner.start(users, spawn_rate=users)
    gevent.spawn_later(duration, lambda: env.runner.quit())
    env.runner.greenlet.join()

    stop_evt.set()
    monitor_t.join()

    stats = env.runner.stats.total
    cpu_avg = sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0.0
    mem_peak = max(mem_usage) if mem_usage else 0.0

    return {
        "requests": stats.num_requests,
        "failures": stats.num_failures,
        "rps": stats.total_rps,
        "p50": stats.get_current_response_time_percentile(0.50),
        "p95": stats.get_current_response_time_percentile(0.95),
        "cpu_avg": cpu_avg,
        "mem_peak": mem_peak,
    }


def main() -> None:
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from services.ltm_service.api import LTMService, LTMServiceServer
    from services.ltm_service.episodic_memory import (
        EpisodicMemoryService,
        InMemoryStorage,
    )

    service = LTMService(EpisodicMemoryService(InMemoryStorage()))
    server = LTMServiceServer(service, host="127.0.0.1", port=8081)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.5)

    try:
        results = run_load_test()
    finally:
        pass

    with open("benchmarks/performance/performance_results.json", "w") as fh:
        json.dump(results, fh, indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
