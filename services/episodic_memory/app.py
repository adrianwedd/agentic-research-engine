from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

from fastapi import Body, FastAPI
from pydantic import BaseModel, Field

from services.ltm_service import EpisodicMemoryService, InMemoryStorage


class ConsolidateRequest(BaseModel):
    task_context: Dict = Field(...)
    execution_trace: Dict = Field(...)
    outcome: Dict = Field(...)


class ConsolidateResponse(BaseModel):
    id: str


class RetrieveBody(BaseModel):
    query: Optional[Dict] = None
    task_context: Optional[Dict] = None


class RetrieveResponse(BaseModel):
    results: List[Dict]


storage = InMemoryStorage()
service = EpisodicMemoryService(storage)

app = FastAPI(title="Episodic Memory Service")


@app.post("/consolidate", response_model=ConsolidateResponse)
async def consolidate(req: ConsolidateRequest) -> ConsolidateResponse:
    rec_id = await asyncio.to_thread(
        service.store_experience,
        req.task_context,
        req.execution_trace,
        req.outcome,
    )
    return ConsolidateResponse(id=rec_id)


@app.get("/retrieve", response_model=RetrieveResponse)
async def retrieve(
    limit: int = 5,
    body: RetrieveBody = Body(default_factory=RetrieveBody),
) -> RetrieveResponse:
    query = body.query or body.task_context or {}
    results = await asyncio.to_thread(
        service.retrieve_similar_experiences,
        query,
        limit=limit,
    )
    return RetrieveResponse(results=results)
