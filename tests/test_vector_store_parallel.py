import random
import sys
import types

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

from services.ltm_service.vector_store import InMemoryVectorStore


def test_parallel_matches_serial(monkeypatch):
    store = InMemoryVectorStore()
    for i in range(1000):
        vec = [random.random() for _ in range(5)]
        store.add(vec, {"id": str(i)})
    query = [random.random() for _ in range(5)]

    monkeypatch.setenv("VECTOR_SEARCH_WORKERS", "1")
    serial = store.query(query, limit=10)

    monkeypatch.setenv("VECTOR_SEARCH_WORKERS", "4")
    parallel = store.query(query, limit=10)

    assert parallel == serial
