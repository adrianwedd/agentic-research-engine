import logging
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.monitoring.events import MessageMetadataEvent
from services.reputation.models import Base
from services.security_agent.service import SecurityAgentService


def setup_service():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return SecurityAgentService(Session)


def test_anomaly_detection_triggers_alert(caplog):
    service = setup_service()
    caplog.set_level(logging.WARNING)
    ts = datetime.now(UTC).timestamp()

    # Oversized message
    service.handle_message_event(
        MessageMetadataEvent(sender="A", size=2000, timestamp=ts)
    )
    assert any("Oversized" in r.message for r in caplog.records)

    caplog.clear()

    for _ in range(service.max_rate + 1):
        service.handle_message_event(
            MessageMetadataEvent(sender="B", size=10, timestamp=ts)
        )
    assert any("Traffic spike" in r.message for r in caplog.records)
