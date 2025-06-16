import os

from opentelemetry import trace

from services.ltm_service import EpisodicMemoryService, InMemoryStorage

DECAY_RATE = float(os.getenv("LTM_DECAY_RATE", "0.99"))
THRESHOLD = float(os.getenv("LTM_PRUNE_THRESHOLD", "0.1"))


def main() -> None:
    storage = InMemoryStorage()
    service = EpisodicMemoryService(storage)
    pruned = service.decay_relevance_scores(decay_rate=DECAY_RATE, threshold=THRESHOLD)
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(
        "hybrid_forget_job", attributes={"pruned": pruned}
    ):
        pass


if __name__ == "__main__":
    main()
