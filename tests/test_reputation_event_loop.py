from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.monitoring.events import EvaluationCompletedEvent
from services.reputation.models import Base
from services.reputation.service import ReputationService


def setup_service():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return ReputationService(Session)


def test_handle_evaluation_event_updates_rep():
    service = setup_service()
    base_vector = {
        "accuracy_score": 0.9,
        "completeness_score": 0.0,
        "coherence_score": 0.0,
        "citation_score": 0.0,
        "source_quality_score": 0.0,
        "token_cost": 0.0,
        "completion_time_sec": 0.0,
        "tool_success_rate": 1.0,
    }
    event1 = EvaluationCompletedEvent(
        task_id="t1",
        worker_agent_id="a1",
        evaluator_id="e1",
        performance_vector=base_vector,
        task_type="research",
    )
    service.handle_evaluation_event(event1)
    rep1 = service.get_reputation("a1", "research")
    assert rep1["accuracy_score"] == 0.9

    event2_vec = base_vector.copy()
    event2_vec["accuracy_score"] = 0.5
    event2 = EvaluationCompletedEvent(
        task_id="t1",
        worker_agent_id="a1",
        evaluator_id="e1",
        performance_vector=event2_vec,
        task_type="research",
        timestamp=event1.timestamp + timedelta(days=1),
    )
    service.handle_evaluation_event(event2)
    rep2 = service.get_reputation("a1", "research")
    assert rep2["accuracy_score"] < 0.9
    assert rep2["accuracy_score"] > 0.5
