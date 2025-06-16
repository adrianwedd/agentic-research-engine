from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.reputation.models import Base
from services.reputation.service import ReputationService


def setup_service():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return ReputationService(Session)


def test_reputation_aggregation():
    service = setup_service()
    agent_id = service.add_agent("WebResearcher")
    task_id = service.add_task("research", "Find info")
    assign_id = service.assign(task_id, agent_id)
    service.record_evaluation(assign_id, "Eval1", {"accuracy": 0.8})
    service.record_evaluation(assign_id, "Eval1", {"accuracy": 0.6})

    rep = service.get_reputation(agent_id, "research")
    assert rep == {"accuracy": 0.7}
