from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from services.monitoring.events import EvaluationCompletedEvent
from services.reputation.service import ReputationService

from .models import CredibilityScore


class SecurityAgentService:
    """Maintain per-agent credibility scores based on reputation."""

    def __init__(
        self, session_factory, *, reputation_service: ReputationService | None = None
    ) -> None:
        self._session_factory = session_factory
        self._reputation = reputation_service or ReputationService(session_factory)

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

    def get_score(self, agent_id: str) -> Optional[float]:
        with self._session_factory() as session:
            record = session.get(CredibilityScore, agent_id)
            return record.score if record else None
