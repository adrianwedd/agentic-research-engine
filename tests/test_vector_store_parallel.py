import random
import sys
import time
import types

import pytest

# flake8: noqa: E402

# minimal stubs for optional deps imported by ltm_service
splitter_mod = types.ModuleType("langchain.text_splitter")
splitter_mod.RecursiveCharacterTextSplitter = lambda **_: types.SimpleNamespace(
    split_text=lambda text: [text]
)
langchain_mod = types.ModuleType("langchain")
sys.modules.setdefault("langchain", langchain_mod)
sys.modules.setdefault("langchain.text_splitter", splitter_mod)

fastapi_mod = types.ModuleType("fastapi")
fastapi_mod.FastAPI = object
fastapi_mod.Body = object
fastapi_mod.Header = object
fastapi_mod.HTTPException = Exception
fastapi_mod.Query = object
responses_mod = types.ModuleType("fastapi.responses")
responses_mod.RedirectResponse = object
sys.modules.setdefault("fastapi.responses", responses_mod)
sys.modules.setdefault("fastapi", fastapi_mod)

otel_mod = types.ModuleType("opentelemetry")
trace_mod = types.ModuleType("opentelemetry.trace")
trace_mod.get_tracer = lambda *_, **__: types.SimpleNamespace(
    start_as_current_span=lambda *a, **k: types.SimpleNamespace(
        __enter__=lambda *a2, **k2: None, __exit__=lambda *a2, **k2: None
    )
)
otel_mod.trace = trace_mod
sys.modules.setdefault("opentelemetry", otel_mod)
sys.modules.setdefault("opentelemetry.trace", trace_mod)

pydantic_mod = types.ModuleType("pydantic")
pydantic_mod.BaseModel = type(
    "BaseModel", (), {"model_rebuild": classmethod(lambda cls: None)}
)
pydantic_mod.Field = lambda *args, **kwargs: None
sys.modules.setdefault("pydantic", pydantic_mod)


def test_query_many_faster(tmp_path):
    from services.ltm_service.vector_store import WeaviateVectorStore

    try:
        store = WeaviateVectorStore(persistence_path=str(tmp_path), workers=4)
    except Exception:
        pytest.skip("weaviate not available")

    for i in range(500):
        vec = [random.random() for _ in range(5)]
        store.add(vec, {"id": str(i)})

    queries = [[random.random() for _ in range(5)] for _ in range(50)]

    start = time.perf_counter()
    for q in queries:
        store.query(q, limit=5)
    serial = time.perf_counter() - start

    start = time.perf_counter()
    store.query_many(queries, limit=5)
    parallel = time.perf_counter() - start

    store.close()
    assert parallel <= serial
