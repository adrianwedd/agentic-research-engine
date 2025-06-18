from services.ltm_service.embedding_client import (
    CachedEmbeddingClient,
    SimpleEmbeddingClient,
)


class CountingEmbeddingClient(SimpleEmbeddingClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        return super().embed(texts)


def test_cached_embedding_client_hits():
    base = CountingEmbeddingClient()
    client = CachedEmbeddingClient(base, cache_size=4)
    for _ in range(20):
        assert client.embed(["hello"])[0] == client.embed(["hello"])[0]
    assert base.calls == 1


def test_service_cache_integration(monkeypatch, weaviate_vector_store):
    from services.ltm_service.episodic_memory import (
        EpisodicMemoryService,
        InMemoryStorage,
    )

    monkeypatch.setenv("EMBED_CACHE_SIZE", "4")
    base = CountingEmbeddingClient()
    service = EpisodicMemoryService(
        InMemoryStorage(), embedding_client=base, vector_store=weaviate_vector_store
    )
    ctx = {"description": "cached"}
    service.store_experience(ctx, {}, {"success": True})
    for _ in range(10):
        service.retrieve_similar_experiences(ctx)
    # 1 call during store_experience + 1 during first retrieval
    assert base.calls <= 2
