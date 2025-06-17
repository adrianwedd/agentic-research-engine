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
    event1 = EvaluationCompletedEvent(
        task_id="t1",
        worker_agent_id="a1",
        evaluator_id="e1",
        performance_vector={"accuracy": 0.9},
        task_type="research",
    )
    service.handle_evaluation_event(event1)
    rep1 = service.get_reputation("a1", "research")
    assert rep1 == {"accuracy": 0.9}

    event2 = EvaluationCompletedEvent(
        task_id="t1",
        worker_agent_id="a1",
        evaluator_id="e1",
        performance_vector={"accuracy": 0.5},
        task_type="research",
        timestamp=event1.timestamp + timedelta(days=1),
    )
    service.handle_evaluation_event(event2)
    rep2 = service.get_reputation("a1", "research")
    assert rep2["accuracy"] < 0.9
    assert rep2["accuracy"] > 0.5
