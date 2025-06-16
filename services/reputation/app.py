from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base
from .service import ReputationService

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reputation.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

service = ReputationService(SessionLocal)
app = FastAPI(title="Reputation Service")


class AgentCreate(BaseModel):
    agent_type: str
    model_base: Optional[str] = None
    status: str = "active"


class TaskCreate(BaseModel):
    task_type: str
    query_text: Optional[str] = None
    parent_task_id: Optional[str] = None


class AssignmentCreate(BaseModel):
    task_id: str
    agent_id: str


class EvaluationCreate(BaseModel):
    assignment_id: str
    evaluator_id: str
    performance_vector: Dict[str, Any] = Field(default_factory=dict)
    is_final: bool = False


@app.post("/agents")
def create_agent(req: AgentCreate) -> Dict[str, str]:
    agent_id = service.add_agent(req.agent_type, req.model_base, req.status)
    return {"agent_id": agent_id}


@app.post("/tasks")
def create_task(req: TaskCreate) -> Dict[str, str]:
    task_id = service.add_task(req.task_type, req.query_text, req.parent_task_id)
    return {"task_id": task_id}


@app.post("/assignments")
def create_assignment(req: AssignmentCreate) -> Dict[str, str]:
    assignment_id = service.assign(req.task_id, req.agent_id)
    return {"assignment_id": assignment_id}


@app.post("/evaluations")
def create_evaluation(req: EvaluationCreate) -> Dict[str, str]:
    evaluation_id = service.record_evaluation(
        req.assignment_id,
        req.evaluator_id,
        req.performance_vector,
        is_final=req.is_final,
    )
    return {"evaluation_id": evaluation_id}


@app.get("/reputation/{agent_id}")
def get_reputation(agent_id: str, context: Optional[str] = None) -> Dict[str, Any]:
    rep = service.get_reputation(agent_id, context)
    return {"reputation": rep}
