import asyncio
import sys
import time
import types
from threading import Thread

import pytest
import requests


@pytest.mark.asyncio
async def test_concurrent_retrieves_under_latency(monkeypatch):
    # minimal stubs for optional deps imported by ltm_service
    splitter_mod = types.ModuleType("langchain.text_splitter")
    splitter_mod.RecursiveCharacterTextSplitter = lambda **_: types.SimpleNamespace(
        split_text=lambda text: [text]
    )
    langchain_mod = types.ModuleType("langchain")
    monkeypatch.setitem(sys.modules, "langchain", langchain_mod)
    monkeypatch.setitem(sys.modules, "langchain.text_splitter", splitter_mod)

    fastapi_mod = types.ModuleType("fastapi")
    fastapi_mod.FastAPI = object
    fastapi_mod.Body = object
    fastapi_mod.Header = object
    fastapi_mod.HTTPException = Exception
    fastapi_mod.Query = object
    responses_mod = types.ModuleType("fastapi.responses")
    responses_mod.RedirectResponse = object
    monkeypatch.setitem(sys.modules, "fastapi", fastapi_mod)
    monkeypatch.setitem(sys.modules, "fastapi.responses", responses_mod)

    pydantic_mod = types.ModuleType("pydantic")
    pydantic_mod.BaseModel = type(
        "BaseModel",
        (),
        {"model_rebuild": classmethod(lambda cls: None)},
    )
    pydantic_mod.Field = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "pydantic", pydantic_mod)

    otel_mod = types.ModuleType("opentelemetry")
    trace_mod = types.ModuleType("opentelemetry.trace")
    trace_mod.get_tracer = lambda *_, **__: types.SimpleNamespace(
        start_as_current_span=lambda *a, **k: types.SimpleNamespace(
            __enter__=lambda *a2, **k2: None, __exit__=lambda *a2, **k2: None
        )
    )
    otel_mod.trace = trace_mod
    monkeypatch.setitem(sys.modules, "opentelemetry", otel_mod)
    monkeypatch.setitem(sys.modules, "opentelemetry.trace", trace_mod)

    from services.ltm_service import EpisodicMemoryService, InMemoryStorage
    from services.ltm_service.api import LTMService, LTMServiceServer

    storage = InMemoryStorage()
    service = LTMService(EpisodicMemoryService(storage))
    server = LTMServiceServer(service, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.httpd.server_port}"

    record = {
        "task_context": {"query": "perf"},
        "execution_trace": {},
        "outcome": {"success": True},
    }
    requests.post(
        f"{endpoint}/memory", json={"record": record}, headers={"X-Role": "editor"}
    )

    async def fetch():
        start = time.perf_counter()
        resp = await asyncio.to_thread(
            requests.get,
            f"{endpoint}/retrieve?limit=1",
            json={"query": {"query": "perf"}},
            headers={"X-Role": "viewer"},
            timeout=5,
        )
        duration = time.perf_counter() - start
        assert resp.status_code == 200
        return duration

    durations = await asyncio.gather(*(fetch() for _ in range(50)))
    assert len(durations) == 50
    assert sum(durations) / len(durations) <= 0.5
    server.httpd.shutdown()
