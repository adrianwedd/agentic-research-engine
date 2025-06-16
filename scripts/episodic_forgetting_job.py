import os

from opentelemetry import trace

from services.ltm_service import EpisodicMemoryService, InMemoryStorage

TTL_DAYS = float(os.getenv("LTM_TTL_DAYS", "30"))
TTL_SECONDS = TTL_DAYS * 24 * 3600


def main() -> None:
    storage = InMemoryStorage()
    service = EpisodicMemoryService(storage)
    pruned = service.prune_stale_memories(TTL_SECONDS)
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(
        "forget_job", attributes={"pruned": pruned, "ttl_days": TTL_DAYS}
    ):
        pass
    print(f"Pruned {pruned} stale memories older than {TTL_DAYS} days")


if __name__ == "__main__":
    main()
