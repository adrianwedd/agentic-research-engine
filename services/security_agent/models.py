from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from services.reputation.models import Agent, Base


class CredibilityScore(Base):
    """Persisted credibility score for an agent."""

    __tablename__ = "credibility_scores"

    agent_id = Column(String, ForeignKey("agents.agent_id"), primary_key=True)
    score = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)

    agent = relationship(Agent)
