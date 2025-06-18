from __future__ import annotations

import asyncio
import contextlib
import os

from fastapi import APIRouter, FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from services.monitoring.events import event_stream
from services.reputation.models import Base

from .service import SecurityAgentService

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./security.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

service = SecurityAgentService(SessionLocal)

app = FastAPI(title="Security Agent Service", version="1.0.0")
router = APIRouter(prefix="/v1")


@app.on_event("startup")
async def _start_listener() -> None:
    async def _run() -> None:
        async for evt in event_stream():
            service.handle_evaluation_event(evt)

    app.state.listener = asyncio.create_task(_run())


@app.on_event("shutdown")
async def _stop_listener() -> None:
    task = getattr(app.state, "listener", None)
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


@router.get("/credibility/{agent_id}")
def get_credibility(agent_id: str) -> dict:
    score = service.get_score(agent_id)
    if score is None:
        raise HTTPException(status_code=404, detail="not found")
    return {"agent_id": agent_id, "credibility": score}


app.include_router(router)
