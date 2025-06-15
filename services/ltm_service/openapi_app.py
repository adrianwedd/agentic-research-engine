from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import Body, FastAPI, Header, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

try:  # Avoid heavy imports when generating docs
    from .api import ALLOWED_MEMORY_TYPES, ROLE_PERMISSIONS, LTMService
except Exception:  # pragma: no cover - fallback for spec generation
    ALLOWED_MEMORY_TYPES = {"episodic", "semantic", "procedural"}
    ROLE_PERMISSIONS = {
        ("POST", "/memory"): {"editor"},
        ("GET", "/memory"): {"viewer", "editor"},
        # Deprecated paths kept for one release cycle
        ("POST", "/consolidate"): {"editor"},
        ("GET", "/retrieve"): {"viewer", "editor"},
    }

    class LTMService:  # type: ignore
        ...


def _check_role(method: str, path: str, role: str) -> bool:
    allowed = ROLE_PERMISSIONS.get((method, path), set())
    return role in allowed


class ConsolidateRequest(BaseModel):
    record: Dict = Field(..., description="Record to store")
    memory_type: str = Field(
        "episodic",
        description="Type of memory module",
        examples=["episodic"],
    )


ConsolidateRequest.model_rebuild()


class ConsolidateResponse(BaseModel):
    id: str = Field(..., description="Stored record identifier")


class RetrieveBody(BaseModel):
    query: Optional[Dict] = Field(None, description="Query to match")
    task_context: Optional[Dict] = Field(
        None, description="Deprecated alternative query field"
    )


RetrieveBody.model_rebuild()


class RetrieveResponse(BaseModel):
    results: List[Dict] = Field(..., description="Matching records")


RetrieveResponse.model_rebuild()


def create_app(service: LTMService) -> FastAPI:
    app = FastAPI(
        title="LTM Service API",
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/docs/openapi.json",
    )

    @app.post("/memory", summary="Store an experience")
    async def create_memory(
        req: ConsolidateRequest,
        x_role: str | None = Header(None),
    ) -> ConsolidateResponse:
        role = x_role or ""
        if not _check_role("POST", "/memory", role):
            raise HTTPException(status_code=403, detail="forbidden")
        if req.memory_type not in ALLOWED_MEMORY_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported memory type")
        rec_id = service.consolidate(req.memory_type, req.record)
        return ConsolidateResponse(id=rec_id)

    @app.post("/consolidate", include_in_schema=False)
    async def consolidate() -> RedirectResponse:
        return RedirectResponse(url="/memory", status_code=308)

    @app.get("/memory", summary="Retrieve similar experiences")
    async def get_memory(
        memory_type: str = Query("episodic"),
        limit: int = Query(5, ge=1, le=50),
        req: RetrieveBody = Body(default_factory=RetrieveBody),
        x_role: str | None = Header(None),
    ) -> RetrieveResponse:
        role = x_role or ""
        if not _check_role("GET", "/memory", role):
            raise HTTPException(status_code=403, detail="forbidden")
        if memory_type not in ALLOWED_MEMORY_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported memory type")
        query = req.query or req.task_context or {}
        results = service.retrieve(memory_type, query, limit=limit)
        return RetrieveResponse(results=results)

    @app.get("/retrieve", include_in_schema=False)
    async def retrieve(memory_type: str = Query("episodic"), limit: int = Query(5)) -> RedirectResponse:
        query = f"memory_type={memory_type}&limit={limit}"
        return RedirectResponse(url=f"/memory?{query}", status_code=308)

    return app


if __name__ == "__main__":  # pragma: no cover - manual execution
    from .episodic_memory import EpisodicMemoryService, InMemoryStorage
    import uvicorn

    service = LTMService(EpisodicMemoryService(InMemoryStorage()))
    uvicorn.run(create_app(service), host="0.0.0.0", port=8081)
