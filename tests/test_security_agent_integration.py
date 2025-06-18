from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.monitoring.events import EvaluationCompletedEvent
from services.reputation.models import Base
from services.security_agent.service import SecurityAgentService


def setup_service():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return SecurityAgentService(Session)


def test_credibility_updates_on_events():
    service = setup_service()
    agent_id = service._reputation.add_agent("worker")
    task_id = service._reputation.add_task("research")
    service._reputation.assign(task_id, agent_id)

    vec1 = {"accuracy_score": 0.9}
    event1 = EvaluationCompletedEvent(
        task_id=task_id,
        worker_agent_id=agent_id,
        evaluator_id="e1",
        performance_vector=vec1,
        task_type="research",
    )
    service.handle_evaluation_event(event1)
    score1 = service.get_score(agent_id)
    assert score1 == 0.9

    vec2 = {"accuracy_score": 0.3}
    event2 = EvaluationCompletedEvent(
        task_id=task_id,
        worker_agent_id=agent_id,
        evaluator_id="e1",
        performance_vector=vec2,
        task_type="research",
        timestamp=event1.timestamp + timedelta(days=1),
    )
    service.handle_evaluation_event(event2)
    score2 = service.get_score(agent_id)
    assert score2 != score1
