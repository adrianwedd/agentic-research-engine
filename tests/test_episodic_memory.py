from services.ltm_service.episodic_memory import EpisodicMemoryService, InMemoryStorage


def test_store_and_retrieve():
    storage = InMemoryStorage()
    service = EpisodicMemoryService(storage)

    ctx1 = {"description": "Write a blog post", "category": "writing"}
    service.store_experience(ctx1, {"steps": []}, {"success": True})

    ctx2 = {"description": "Write unit tests", "category": "coding"}
    service.store_experience(ctx2, {"steps": []}, {"success": True})

    results = service.retrieve_similar_experiences(
        {"description": "Write code"}, limit=1
    )
    assert results
    assert results[0]["task_context"]["description"] == "Write unit tests"
