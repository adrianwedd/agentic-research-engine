from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query
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
app = FastAPI(title="Reputation Service", version="1.0.0")


def _parse_api_keys(raw: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for pair in raw.split(","):
        if not pair:
            continue
        role, token = pair.split(":", 1)
        mapping[token.strip()] = role.strip()
    return mapping


API_KEYS = _parse_api_keys(
    os.getenv(
        "REPUTATION_API_KEYS",
        "evaluator:evaluator-token,planner:planner-token,admin:admin-token",
    )
)


def get_role(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")
    token = authorization.split()[1]
    role = API_KEYS.get(token)
    if not role:
        raise HTTPException(status_code=401, detail="unauthorized")
    return role


def require_role(allowed: List[str]):
    def _inner(role: str = Depends(get_role)) -> str:
        if role not in allowed:
            raise HTTPException(status_code=403, detail="forbidden")
        return role

    return _inner


router = APIRouter(prefix="/v1")


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


@router.post(
    "/evaluations",
    status_code=201,
    dependencies=[Depends(require_role(["evaluator"]))],
)
def create_evaluation_v1(req: EvaluationCreate) -> Dict[str, str]:
    evaluation_id = service.record_evaluation(
        req.assignment_id,
        req.evaluator_id,
        req.performance_vector,
        is_final=req.is_final,
    )
    return {"evaluation_id": evaluation_id}


@router.get(
    "/reputation/{agent_id}",
    dependencies=[Depends(require_role(["planner", "admin"]))],
)
def get_reputation_v1(agent_id: str, context: Optional[str] = None) -> Dict[str, Any]:
    rep = service.get_reputation_record(agent_id, context)
    if not rep:
        raise HTTPException(status_code=404, detail="not found")
    return rep


@router.get(
    "/reputation/query",
    dependencies=[Depends(require_role(["planner", "admin"]))],
)
def query_reputation_v1(
    context: Optional[str] = Query(None),
    top_n: int = Query(10, ge=1, le=100),
    sort_by: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
) -> Dict[str, Any]:
    results = service.query_reputations(
        context, top_n=top_n, sort_by=sort_by, offset=offset
    )
    return {"results": results, "offset": offset, "limit": top_n}


@router.get(
    "/agents/{agent_id}/history",
    dependencies=[Depends(require_role(["admin"]))],
)
def get_history_v1(
    agent_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    records = service.get_history(agent_id, offset=offset, limit=limit)
    return {"results": records, "offset": offset, "limit": limit}


app.include_router(router, prefix="/api")
