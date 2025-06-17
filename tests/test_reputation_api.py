import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.reputation.models import Base
from services.reputation.service import ReputationService

pytestmark = pytest.mark.core


def setup_service():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return ReputationService(Session)


def test_query_reputation_sorting():
    service = setup_service()
    a1 = service.add_agent("worker")
    a2 = service.add_agent("worker")
    task = service.add_task("research")
    assign1 = service.assign(task, a1)
    assign2 = service.assign(task, a2)
    vec1 = {
        "accuracy_score": 0.5,
        "completeness_score": 0.0,
        "coherence_score": 0.0,
        "citation_score": 0.0,
        "source_quality_score": 0.0,
        "token_cost": 0.0,
        "completion_time_sec": 0.0,
        "tool_success_rate": 1.0,
    }
    vec2 = vec1.copy()
    vec2["accuracy_score"] = 0.9
    service.record_evaluation(assign1, "eval", vec1)
    service.record_evaluation(assign2, "eval", vec2)

    results = service.query_reputations("research", top_n=2, sort_by="accuracy_score")
    assert results[0]["agent_id"] == a2
    assert results[1]["agent_id"] == a1


def test_get_history_pagination():
    service = setup_service()
    agent = service.add_agent("worker")
    task = service.add_task("test")
    assign = service.assign(task, agent)
    vec = {
        "accuracy_score": 0.0,
        "completeness_score": 0.0,
        "coherence_score": 0.0,
        "citation_score": 0.0,
        "source_quality_score": 0.0,
        "token_cost": 0.0,
        "completion_time_sec": 0.0,
        "tool_success_rate": 1.0,
        "score": 0,
    }
    for i in range(5):
        vec["score"] = i
        service.record_evaluation(assign, "ev", dict(vec))
    hist = service.get_history(agent, offset=1, limit=2)
    assert len(hist) == 2
    assert hist[0]["performance_vector"]["score"] == 3
