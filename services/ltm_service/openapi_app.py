from __future__ import annotations

import asyncio
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
        ("POST", "/semantic_consolidate"): {"editor"},
        ("POST", "/temporal_consolidate"): {"editor"},
        ("POST", "/propagate_subgraph"): {"editor"},
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


class SemanticConsolidateRequest(BaseModel):
    payload: Dict | str = Field(..., description="JSON-LD object or Cypher string")
    format: str = Field("jsonld", description="Payload format")


class SemanticConsolidateResponse(BaseModel):
    result: List = Field(..., description="Results from consolidation")


class PropagateSubgraphRequest(BaseModel):
    entities: List[Dict] = Field(default_factory=list)
    relations: List[Dict] = Field(default_factory=list)


class PropagateSubgraphResponse(BaseModel):
    ids: List[str] = Field(..., description="Stored relation ids")


PropagateSubgraphRequest.model_rebuild()
PropagateSubgraphResponse.model_rebuild()


SemanticConsolidateRequest.model_rebuild()
SemanticConsolidateResponse.model_rebuild()


class TemporalConsolidateRequest(BaseModel):
    subject: str = Field(..., description="Fact subject")
    predicate: str = Field(..., description="Relation type")
    object: str = Field(..., description="Fact object")
    value: Optional[str] = Field(None, description="Fact value")
    valid_from: float = Field(..., description="Start of validity")
    valid_to: Optional[float] = Field(None, description="End of validity")
    location: Optional[Dict] = Field(None, description="Location context")


class TemporalConsolidateResponse(BaseModel):
    id: str = Field(..., description="Stored fact identifier")


TemporalConsolidateRequest.model_rebuild()
TemporalConsolidateResponse.model_rebuild()


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
        rec_id = await asyncio.to_thread(
            service.consolidate,
            req.memory_type,
            req.record,
        )
        return ConsolidateResponse(id=rec_id)

    @app.post("/semantic_consolidate", summary="Store facts in the knowledge graph")
    async def semantic_consolidate(
        req: SemanticConsolidateRequest,
        x_role: str | None = Header(None),
    ) -> SemanticConsolidateResponse:
        role = x_role or ""
        if not _check_role("POST", "/semantic_consolidate", role):
            raise HTTPException(status_code=403, detail="forbidden")
        result = await asyncio.to_thread(
            service.semantic_consolidate,
            req.payload,
            fmt=req.format,
        )
        return SemanticConsolidateResponse(result=result)

    @app.post("/propagate_subgraph", summary="Propagate a completed subgraph")
    async def propagate_subgraph(
        req: PropagateSubgraphRequest,
        x_role: str | None = Header(None),
    ) -> PropagateSubgraphResponse:
        role = x_role or ""
        if not _check_role("POST", "/propagate_subgraph", role):
            raise HTTPException(status_code=403, detail="forbidden")
        ids = await asyncio.to_thread(service.propagate_subgraph, req.model_dump())
        return PropagateSubgraphResponse(ids=ids)

    @app.post("/temporal_consolidate", summary="Merge fact versions")
    async def temporal_consolidate(
        req: TemporalConsolidateRequest,
        x_role: str | None = Header(None),
    ) -> TemporalConsolidateResponse:
        role = x_role or ""
        if not _check_role("POST", "/temporal_consolidate", role):
            raise HTTPException(status_code=403, detail="forbidden")
        fid = await asyncio.to_thread(
            service.temporal_consolidate,
            req.model_dump(),
        )
        return TemporalConsolidateResponse(id=fid)

    @app.get("/spatial_query", summary="Query facts by bounding box")
    async def spatial_query(
        bbox: str = Query(..., description="min_lon,min_lat,max_lon,max_lat"),
        valid_from: float = Query(..., description="Start time"),
        valid_to: float = Query(..., description="End time"),
        x_role: str | None = Header(None),
    ) -> RetrieveResponse:
        role = x_role or ""
        if not _check_role("GET", "/spatial_query", role):
            raise HTTPException(status_code=403, detail="forbidden")
        try:
            coords = [float(x) for x in bbox.split(",")]
            if len(coords) != 4:
                raise ValueError
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid bbox")
        results = await asyncio.to_thread(
            service.spatial_query,
            coords,
            valid_from,
            valid_to,
        )
        return RetrieveResponse(results=results)

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
        results = await asyncio.to_thread(
            service.retrieve,
            memory_type,
            query,
            limit=limit,
        )
        return RetrieveResponse(results=results)

    @app.get("/retrieve", include_in_schema=False)
    async def retrieve(
        memory_type: str = Query("episodic"), limit: int = Query(5)
    ) -> RedirectResponse:
        query = f"memory_type={memory_type}&limit={limit}"
        return RedirectResponse(url=f"/memory?{query}", status_code=308)

    return app


if __name__ == "__main__":  # pragma: no cover - manual execution
    import uvicorn

    from .episodic_memory import EpisodicMemoryService, InMemoryStorage
    from .procedural_memory import ProceduralMemoryService

    episodic = EpisodicMemoryService(InMemoryStorage())
    service = LTMService(
        episodic,
        procedural_memory=ProceduralMemoryService(InMemoryStorage()),
    )
    uvicorn.run(create_app(service), host="0.0.0.0", port=8081)
