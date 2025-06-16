from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class Agent(Base):
    __tablename__ = "agents"

    agent_id = Column(String, primary_key=True, default=_uuid)
    agent_type = Column(String, nullable=False)
    model_base = Column(String, nullable=True)
    creation_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String, nullable=False, default="active")

    assignments = relationship("Assignment", back_populates="agent")


class Task(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, default=_uuid)
    parent_task_id = Column(String, ForeignKey("tasks.task_id"), nullable=True)
    task_type = Column(String, nullable=False)
    query_text = Column(Text, nullable=True)
    creation_timestamp = Column(DateTime, default=datetime.utcnow)

    assignments = relationship("Assignment", back_populates="task")


class Assignment(Base):
    __tablename__ = "assignments"

    assignment_id = Column(String, primary_key=True, default=_uuid)
    task_id = Column(String, ForeignKey("tasks.task_id"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False)
    assignment_timestamp = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent", back_populates="assignments")
    task = relationship("Task", back_populates="assignments")
    evaluations = relationship("Evaluation", back_populates="assignment")


class Evaluation(Base):
    __tablename__ = "evaluations"

    evaluation_id = Column(String, primary_key=True, default=_uuid)
    assignment_id = Column(
        String, ForeignKey("assignments.assignment_id"), nullable=False
    )
    evaluator_id = Column(String, nullable=False)
    evaluation_timestamp = Column(DateTime, default=datetime.utcnow)
    performance_vector = Column(JSON, nullable=False)
    is_final = Column(Boolean, default=False)

    assignment = relationship("Assignment", back_populates="evaluations")


class ReputationScore(Base):
    __tablename__ = "reputation_scores"
    __table_args__ = (UniqueConstraint("agent_id", "context", name="uq_agent_context"),)

    id = Column(String, primary_key=True, default=_uuid)
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False)
    context = Column(String, nullable=True)
    reputation_vector = Column(JSON, nullable=False)
    confidence_score = Column(Float, default=0.0)
    last_updated_timestamp = Column(DateTime, default=datetime.utcnow)

    agent = relationship("Agent")
