from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

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
            self._update_reputation(session, assignment.agent_id, context)
            session.commit()
            return evaluation.evaluation_id

    def _update_reputation(
        self, session: Session, agent_id: str, context: str | None
    ) -> None:
        stmt = (
            select(Evaluation.performance_vector)
            .join(Assignment, Evaluation.assignment_id == Assignment.assignment_id)
            .join(Task, Assignment.task_id == Task.task_id)
            .where(Assignment.agent_id == agent_id)
        )
        if context:
            stmt = stmt.where(Task.task_type == context)
        rows = session.execute(stmt).all()
        if not rows:
            return
        totals: defaultdict[str, float] = defaultdict(float)
        for row in rows:
            vec = row[0] or {}
            for k, v in vec.items():
                totals[k] += float(v)
        count = len(rows)
        avg = {k: v / count for k, v in totals.items()}
        rep = session.execute(
            select(ReputationScore).where(
                ReputationScore.agent_id == agent_id, ReputationScore.context == context
            )
        ).scalar_one_or_none()
        if rep is None:
            rep = ReputationScore(
                agent_id=agent_id,
                context=context,
                reputation_vector=avg,
                confidence_score=float(count),
            )
            session.add(rep)
        else:
            rep.reputation_vector = avg
            rep.confidence_score = float(count)
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
