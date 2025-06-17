from __future__ import annotations

from datetime import datetime
from math import exp
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.monitoring.events import EvaluationCompletedEvent

from .models import Agent, Assignment, Evaluation, ReputationScore, Task


class ReputationService:
    """Manage reputation data and aggregation logic."""

    def __init__(self, session_factory) -> None:
        self._session_factory = session_factory

    def add_agent(
        self, agent_type: str, model_base: str | None = None, status: str = "active"
    ) -> str:
        with self._session_factory() as session:
            agent = Agent(agent_type=agent_type, model_base=model_base, status=status)
            session.add(agent)
            session.commit()
            return agent.agent_id

    def add_task(
        self,
        task_type: str,
        query_text: str | None = None,
        parent_task_id: str | None = None,
    ) -> str:
        with self._session_factory() as session:
            task = Task(
                task_type=task_type,
                query_text=query_text,
                parent_task_id=parent_task_id,
            )
            session.add(task)
            session.commit()
            return task.task_id

    def assign(self, task_id: str, agent_id: str) -> str:
        with self._session_factory() as session:
            assignment = Assignment(task_id=task_id, agent_id=agent_id)
            session.add(assignment)
            session.commit()
            return assignment.assignment_id

    def record_evaluation(
        self,
        assignment_id: str,
        evaluator_id: str,
        performance_vector: Dict[str, Any],
        *,
        is_final: bool = False,
    ) -> str:
        with self._session_factory() as session:
            evaluation = Evaluation(
                assignment_id=assignment_id,
                evaluator_id=evaluator_id,
                performance_vector=performance_vector,
                is_final=is_final,
            )
            session.add(evaluation)
            session.commit()
            # Update reputation cache
            assignment = session.get(Assignment, assignment_id)
            if assignment is None:
                return evaluation.evaluation_id
            task = session.get(Task, assignment.task_id)
            context = task.task_type if task else None
            self._update_reputation(
                session,
                assignment.agent_id,
                context,
                performance_vector,
                evaluation.evaluation_timestamp,
            )
            session.commit()
            return evaluation.evaluation_id

    def handle_evaluation_event(self, event: EvaluationCompletedEvent) -> None:
        """Ingest an EvaluationCompletedEvent and update reputation."""
        with self._session_factory() as session:
            task = session.execute(
                select(Task).where(Task.task_id == event.task_id)
            ).scalar_one_or_none()
            if task is None:
                task = Task(
                    task_id=event.task_id, task_type=event.task_type or "unknown"
                )
                session.add(task)

            agent = session.execute(
                select(Agent).where(Agent.agent_id == event.worker_agent_id)
            ).scalar_one_or_none()
            if agent is None:
                agent = Agent(agent_id=event.worker_agent_id, agent_type="worker")
                session.add(agent)

            assignment = session.execute(
                select(Assignment).where(
                    Assignment.task_id == task.task_id,
                    Assignment.agent_id == agent.agent_id,
                )
            ).scalar_one_or_none()
            if assignment is None:
                assignment = Assignment(task_id=task.task_id, agent_id=agent.agent_id)
                session.add(assignment)
                session.flush()

            evaluation = Evaluation(
                assignment_id=assignment.assignment_id,
                evaluator_id=event.evaluator_id,
                evaluation_timestamp=event.timestamp,
                performance_vector=event.performance_vector,
                is_final=event.is_final,
            )
            session.add(evaluation)
            self._update_reputation(
                session,
                agent.agent_id,
                task.task_type,
                event.performance_vector,
                event.timestamp,
            )
            session.commit()

    def _update_reputation(
        self,
        session: Session,
        agent_id: str,
        context: str | None,
        new_vector: Dict[str, Any],
        timestamp: datetime,
    ) -> None:
        rep = session.execute(
            select(ReputationScore).where(
                ReputationScore.agent_id == agent_id,
                ReputationScore.context == context,
            )
        ).scalar_one_or_none()
        if rep is None:
            rep = ReputationScore(
                agent_id=agent_id,
                context=context,
                reputation_vector=new_vector,
                confidence_score=1.0,
                last_updated_timestamp=timestamp,
            )
            session.add(rep)
            session.flush()
            return

        age_days = (timestamp - rep.last_updated_timestamp).total_seconds() / 86400.0
        decay = exp(-age_days / 7.0)
        old_weight = rep.confidence_score * decay
        new_weight = 1.0
        total_weight = old_weight + new_weight
        merged: Dict[str, float] = {}
        keys = set(rep.reputation_vector.keys()) | set(new_vector.keys())
        for k in keys:
            old_val = float(rep.reputation_vector.get(k, 0.0))
            new_val = float(new_vector.get(k, 0.0))
            merged[k] = (old_val * old_weight + new_val * new_weight) / total_weight
        rep.reputation_vector = merged
        rep.confidence_score = total_weight
        rep.last_updated_timestamp = timestamp
        session.flush()

    def get_reputation(
        self, agent_id: str, context: str | None = None
    ) -> Dict[str, Any] | None:
        with self._session_factory() as session:
            rep = session.execute(
                select(ReputationScore).where(
                    ReputationScore.agent_id == agent_id,
                    ReputationScore.context == context,
                )
            ).scalar_one_or_none()
            return rep.reputation_vector if rep else None

    def get_reputation_record(
        self, agent_id: str, context: str | None = None
    ) -> Optional[Dict[str, Any]]:
        """Return full reputation record for an agent."""
        with self._session_factory() as session:
            rep = session.execute(
                select(ReputationScore).where(
                    ReputationScore.agent_id == agent_id,
                    ReputationScore.context == context,
                )
            ).scalar_one_or_none()
            if rep is None:
                return None
            return {
                "agent_id": rep.agent_id,
                "context": rep.context,
                "reputation_vector": rep.reputation_vector,
                "confidence_score": rep.confidence_score,
                "last_updated_timestamp": rep.last_updated_timestamp,
            }

    def query_reputations(
        self,
        context: str | None = None,
        *,
        top_n: int = 10,
        sort_by: str | None = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Return a list of reputation records sorted by the given dimension."""
        with self._session_factory() as session:
            stmt = select(ReputationScore)
            if context is not None:
                stmt = stmt.where(ReputationScore.context == context)
            reps = session.execute(stmt).scalars().all()
            if sort_by:
                reps.sort(
                    key=lambda r: float(r.reputation_vector.get(sort_by, 0.0)),
                    reverse=True,
                )
            else:
                reps.sort(key=lambda r: r.confidence_score, reverse=True)
            sliced = reps[offset : offset + top_n]
            return [
                {
                    "agent_id": r.agent_id,
                    "context": r.context,
                    "reputation_vector": r.reputation_vector,
                    "confidence_score": r.confidence_score,
                    "last_updated_timestamp": r.last_updated_timestamp,
                }
                for r in sliced
            ]

    def get_history(
        self, agent_id: str, *, offset: int = 0, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Return evaluation history for an agent ordered by timestamp desc."""
        with self._session_factory() as session:
            stmt = (
                select(Evaluation)
                .join(Assignment, Evaluation.assignment_id == Assignment.assignment_id)
                .where(Assignment.agent_id == agent_id)
                .order_by(Evaluation.evaluation_timestamp.desc())
                .offset(offset)
                .limit(limit)
            )
            rows = session.execute(stmt).scalars().all()
            return [
                {
                    "evaluation_id": e.evaluation_id,
                    "assignment_id": e.assignment_id,
                    "evaluator_id": e.evaluator_id,
                    "evaluation_timestamp": e.evaluation_timestamp,
                    "performance_vector": e.performance_vector,
                    "is_final": e.is_final,
                }
                for e in rows
            ]
