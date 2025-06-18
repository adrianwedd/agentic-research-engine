import sys
import time
import types

# flake8: noqa: E402

# provide minimal stub for langchain dependency
splitter_mod = types.ModuleType("langchain.text_splitter")  # noqa: E402
splitter_mod.RecursiveCharacterTextSplitter = lambda **_: types.SimpleNamespace(
    split_text=lambda text: [text]
)  # noqa: E402
langchain_mod = types.ModuleType("langchain")  # noqa: E402
sys.modules.setdefault("langchain", langchain_mod)  # noqa: E402
sys.modules.setdefault("langchain.text_splitter", splitter_mod)  # noqa: E402

# minimal fastapi stub to satisfy imports
fastapi_mod = types.ModuleType("fastapi")  # noqa: E402
fastapi_mod.FastAPI = object
fastapi_mod.Body = object
fastapi_mod.Header = object
fastapi_mod.HTTPException = Exception
fastapi_mod.Query = object
responses_mod = types.ModuleType("fastapi.responses")  # noqa: E402
responses_mod.RedirectResponse = object
sys.modules.setdefault("fastapi.responses", responses_mod)  # noqa: E402
sys.modules.setdefault("fastapi", fastapi_mod)  # noqa: E402

pydantic_mod = types.ModuleType("pydantic")  # noqa: E402
pydantic_mod.BaseModel = type(
    "BaseModel", (), {"model_rebuild": classmethod(lambda cls: None)}
)
pydantic_mod.Field = lambda *args, **kwargs: None
sys.modules.setdefault("pydantic", pydantic_mod)  # noqa: E402

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)

from services.ltm_service.episodic_memory import EpisodicMemoryService, InMemoryStorage
from services.ltm_service.vector_store import MilvusVectorStore


class InMemorySpanExporter(SpanExporter):
    def __init__(self) -> None:
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:  # pragma: no cover - not needed
        pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool:  # pragma: no cover
        return True


def test_prune_stale_memories(milvus_vector_store):
    storage = InMemoryStorage()
    service = EpisodicMemoryService(storage, vector_store=milvus_vector_store)

    old_ts = time.time() - 31 * 24 * 3600
    recent_ts = time.time() - 5 * 24 * 3600

    id_old = storage.save(
        {
            "task_context": {},
            "execution_trace": {},
            "outcome": {},
            "last_accessed": old_ts,
        }
    )
    vector_store.add([0.0], {"id": id_old})
    id_new = storage.save(
        {
            "task_context": {},
            "execution_trace": {},
            "outcome": {},
            "last_accessed": recent_ts,
        }
    )
    vector_store.add([0.0], {"id": id_new})

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    pruned = service.prune_stale_memories(30 * 24 * 3600)
    assert pruned == 1
    assert id_old not in dict(storage.all())
    assert id_new in dict(storage.all())
    assert exporter.spans


def test_decay_relevance_soft_delete(milvus_vector_store):
    storage = InMemoryStorage()
    service = EpisodicMemoryService(storage, vector_store=milvus_vector_store)

    rec_id = service.store_experience({}, {}, {})
    storage.update(
        rec_id,
        {
            "last_accessed_timestamp": time.time() - 31 * 24 * 3600,
            "relevance_score": 0.05,
        },
    )

    pruned = service.decay_relevance_scores(decay_rate=0.9, threshold=0.1)
    assert pruned == 1
    assert storage._data[rec_id].get("deleted_at")
