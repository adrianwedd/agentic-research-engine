import pytest

from services.ltm_service import (
    EpisodicMemoryService,
    InMemoryStorage,
    InMemoryVectorStore,
    SimpleEmbeddingClient,
    WeaviateVectorStore,
)


def test_store_and_retrieve():
    storage = InMemoryStorage()
    service = EpisodicMemoryService(storage)

    ctx1 = {"description": "Write a blog post", "category": "writing"}
    service.store_experience(ctx1, {"steps": []}, {"success": True})

    ctx2 = {"description": "Write unit tests", "category": "coding"}
    service.store_experience(ctx2, {"steps": []}, {"success": True})

    results = service.retrieve_similar_experiences(
        {"description": "Write code"}, limit=2
    )
    assert results
    assert len(results) == 2
    assert results[0]["similarity"] >= results[1]["similarity"]
    descriptions = {
        results[0]["task_context"]["description"],
        results[1]["task_context"]["description"],
    }
    assert descriptions == {"Write a blog post", "Write unit tests"}


def test_embedding_and_vector_storage():
    storage = InMemoryStorage()
    vector_store = InMemoryVectorStore()
    service = EpisodicMemoryService(
        storage, embedding_client=SimpleEmbeddingClient(), vector_store=vector_store
    )

    ctx = {"description": "Vector test", "category": "testing"}
    mem_id = service.store_experience(ctx, {}, {"success": True})
    assert mem_id

    results = service.retrieve_similar_experiences({"description": "Vector test"})
    assert results
    assert results[0]["id"] == mem_id


class FlakyEmbeddingClient(SimpleEmbeddingClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("transient")
        return super().embed(texts)


def test_embedding_retry():
    storage = InMemoryStorage()
    vector_store = InMemoryVectorStore()
    client = FlakyEmbeddingClient()
    service = EpisodicMemoryService(
        storage, embedding_client=client, vector_store=vector_store
    )

    ctx = {"description": "Retry test"}
    mem_id = service.store_experience(ctx, {}, {"success": True})
    assert mem_id
    assert client.calls >= 2


def test_weaviate_vector_store(tmp_path):
    try:
        store = WeaviateVectorStore(persistence_path=str(tmp_path))
    except Exception:
        pytest.skip("weaviate not available")

    ctx = {"description": "Weaviate", "category": "db"}
    service = EpisodicMemoryService(
        InMemoryStorage(), embedding_client=SimpleEmbeddingClient(), vector_store=store
    )
    rec_id = service.store_experience(ctx, {}, {"success": True})
    results = service.retrieve_similar_experiences({"description": "Weaviate"})
    assert results
    assert results[0]["id"] == rec_id
    store.close()


def test_retrieve_boosts_relevance():
    storage = InMemoryStorage()
    service = EpisodicMemoryService(storage)

    ctx = {"description": "Boost"}
    rec_id = service.store_experience(ctx, {}, {"success": True})
    before = storage._data[rec_id]["relevance_score"]
    service.retrieve_similar_experiences(ctx)
    after = storage._data[rec_id]["relevance_score"]
    assert after > before
