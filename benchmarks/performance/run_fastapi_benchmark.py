from __future__ import annotations

import json
import sys
import threading
import time
import types
from pathlib import Path

import gevent
import psutil
import uvicorn
from locust import HttpUser, between, task
from locust.env import Environment

# flake8: noqa


sys.path.append(str(Path(__file__).resolve().parents[2]))

splitter_mod = types.ModuleType("langchain.text_splitter")
splitter_mod.RecursiveCharacterTextSplitter = lambda **_: types.SimpleNamespace(
    split_text=lambda text: [text]
)
langchain_mod = types.ModuleType("langchain")
sys.modules.setdefault("langchain", langchain_mod)
sys.modules.setdefault("langchain.text_splitter", splitter_mod)

langsmith_mod = types.ModuleType("langsmith")
sys.modules.setdefault("langsmith", langsmith_mod)
sys.modules.setdefault("langsmith.client", types.ModuleType("langsmith.client"))
sys.modules.setdefault("langsmith.env", types.ModuleType("langsmith.env"))
sys.modules.setdefault(
    "langsmith.env._runtime_env", types.ModuleType("langsmith.env._runtime_env")
)
sys.modules.setdefault("langsmith.utils", types.ModuleType("langsmith.utils"))
sys.modules.setdefault("langsmith.schemas", types.ModuleType("langsmith.schemas"))


from services.ltm_service import EpisodicMemoryService, InMemoryStorage, LTMService
from services.ltm_service.openapi_app import create_app


class APIUser(HttpUser):
    wait_time = between(0.01, 0.05)
    host = "http://127.0.0.1:8081"

    @task
    def consolidate_and_retrieve(self) -> None:
        record = {
            "task_context": {"query": "perf"},
            "execution_trace": {},
            "outcome": {"success": True},
        }
        headers = {"X-Role": "editor"}
        self.client.post("/memory", json={"record": record}, headers=headers)
        self.client.get(
            "/memory?limit=1",
            json={"query": {"query": "perf"}},
            headers={"X-Role": "viewer"},
        )


def run_load_test(duration: int = 10, users: int = 20) -> dict[str, float | int]:
    env = Environment(user_classes=[APIUser])
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
    baseline_path = Path("benchmarks/performance/performance_results.json")
    baseline = json.loads(baseline_path.read_text())
    baseline_rps = baseline.get("rps", 0.0)

    service = LTMService(EpisodicMemoryService(InMemoryStorage()))
    app = create_app(service)
    config = uvicorn.Config(app, host="127.0.0.1", port=8081, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(0.5)

    results: dict[str, dict[str, float | int]] = {}
    try:
        for users in [20, 40, 80, 160]:
            metrics = run_load_test(users=users)
            results[str(users)] = metrics
    finally:
        server.should_exit = True
        thread.join()

    results["baseline_rps"] = baseline_rps
    Path("benchmarks/performance/fastapi_benchmarks.json").write_text(
        json.dumps(results, indent=2)
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
