from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from services.monitoring.events import EvaluationCompletedEvent, MessageMetadataEvent
from services.reputation.service import ReputationService

from .models import CredibilityScore


class SecurityAgentService:
    """Maintain per-agent credibility scores based on reputation."""

    def __init__(
        self, session_factory, *, reputation_service: ReputationService | None = None
    ) -> None:
        self._session_factory = session_factory
        self._reputation = reputation_service or ReputationService(session_factory)
        self._logger = logging.getLogger(__name__)
        self._msg_history: Dict[str, List[float]] = {}
        self.max_size = 1000
        self.window = timedelta(seconds=1)
        self.max_rate = 5

    def _calc_score(self, rep: Dict[str, Any] | None) -> float:
        if not rep:
            return 0.0
        values = [float(v) for v in rep.values() if isinstance(v, (int, float))]
        return sum(values) / len(values) if values else 0.0

    def update_score(self, agent_id: str) -> float:
        rep_vec = self._reputation.get_reputation(agent_id)
        score = self._calc_score(rep_vec)
        with self._session_factory() as session:
            record = session.get(CredibilityScore, agent_id)
            if record is None:
                record = CredibilityScore(agent_id=agent_id, score=score)
                session.add(record)
            else:
                record.score = score
                record.last_updated = datetime.utcnow()
            session.commit()
        return score

    def handle_evaluation_event(self, event: EvaluationCompletedEvent) -> None:
        self._reputation.handle_evaluation_event(event)
        self.update_score(event.worker_agent_id)

    def handle_message_event(self, event: MessageMetadataEvent) -> None:
        """Analyze message metadata for anomalies."""
        history = self._msg_history.setdefault(event.sender, [])
        now = datetime.fromtimestamp(event.timestamp)
        history.append(now.timestamp())
        # drop messages outside window
        cutoff = now - self.window
        self._msg_history[event.sender] = [
            t for t in history if t >= cutoff.timestamp()
        ]
        if len(self._msg_history[event.sender]) > self.max_rate:
            self._logger.warning("Traffic spike detected from %s", event.sender)
        if event.size > self.max_size:
            self._logger.warning(
                "Oversized message from %s (%d bytes)", event.sender, event.size
            )

    def get_score(self, agent_id: str) -> Optional[float]:
        with self._session_factory() as session:
            record = session.get(CredibilityScore, agent_id)
            return record.score if record else None
