
# Security: Only bind to all interfaces in production
import os
HOST = HOST if os.getenv("ENVIRONMENT") == "production" else "127.0.0.1"
"""OpenAPI FastAPI application exposing the LTM service."""

from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import Body, FastAPI, Header, HTTPException, Query, BackgroundTasks
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

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
        ("GET", "/snapshot"): {"viewer", "editor"},
        # Deprecated paths kept for one release cycle
        ("POST", "/consolidate"): {"editor"},
        ("GET", "/retrieve"): {"viewer", "editor"},
    }

    class LTMService:  # type: ignore
        ...


def _check_role(method: str, path: str, role: str) -> bool:
    """Return ``True`` if the role is permitted for the operation."""
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


<<<<<<< Updated upstream
class ProvenanceResponse(BaseModel):
    provenance: Dict = Field(..., description="Provenance metadata")


ProvenanceResponse.model_rebuild()


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


class SkillRequest(BaseModel):
    skill_policy: Dict = Field(..., description="Skill policy data")
    skill_representation: str | List[float] = Field(
        ..., description="Vector or text rep"
    )
    skill_metadata: Dict = Field(default_factory=dict, description="Arbitrary metadata")


class SkillQuery(BaseModel):
    query: str | List[float] | Dict = Field(..., description="Vector or metadata")
    limit: int = Field(5, description="Max results")


class CritiqueRequest(BaseModel):
    critique: Dict = Field(..., description="Critique record")


class CritiqueQuery(BaseModel):
    query: Optional[Dict] = None


CritiqueRequest.model_rebuild()
CritiqueQuery.model_rebuild()


SkillRequest.model_rebuild()
SkillQuery.model_rebuild()


def create_app(service: LTMService) -> FastAPI:
    """Construct the FastAPI application exposing the LTM endpoints."""

=======
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    app.state.start_time = time.time()
    yield
    # Shutdown
    if hasattr(app.state, "ltm_service"):
        app.state.ltm_service.close()

def create_app(service: LTMService) -> FastAPI:
    """Create optimized FastAPI application with performance enhancements."""
>>>>>>> Stashed changes
    app = FastAPI(
        title="LTM Service API",
        version="1.0.0",
        docs_url="/docs",
        openapi_url="/docs/openapi.json",
        lifespan=lifespan,
    )
    
    # Store service in app state for lifecycle management
    app.state.ltm_service = service
    
    # Add CORS middleware for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/memory", summary="Store an experience")
    async def create_memory(
        req: ConsolidateRequest,
        x_role: str | None = Header(None),
        background_tasks: BackgroundTasks = BackgroundTasks(),
    ) -> ConsolidateResponse:
        """Store memory record with async processing and background cleanup."""
        start_time = time.perf_counter()
        
        role = x_role or ""
        if not _check_role("POST", "/memory", role):
            raise HTTPException(status_code=403, detail="forbidden")
        if req.memory_type not in ALLOWED_MEMORY_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported memory type")
        
        try:
            # Use optimized async method instead of asyncio.to_thread
            rec_id = await service.consolidate_async(req.memory_type, req.record)
            
            # Add background task for cleanup if needed
            response_time = time.perf_counter() - start_time
            if response_time > 1.0:  # Log slow requests
                background_tasks.add_task(
                    _log_slow_request, "create_memory", response_time, req.memory_type
                )
                
            return ConsolidateResponse(id=rec_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error")

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

    @app.get("/snapshot", summary="Retrieve spatio-temporal snapshot")
    async def snapshot(
        valid_at: float = Query(..., description="Valid time"),
        tx_at: float = Query(..., description="Transaction time"),
        x_role: str | None = Header(None),
    ) -> RetrieveResponse:
        role = x_role or ""
        if not _check_role("GET", "/snapshot", role):
            raise HTTPException(status_code=403, detail="forbidden")
        results = await asyncio.to_thread(
            service.get_snapshot,
            valid_at,
            tx_at,
        )
        return RetrieveResponse(results=results)

    @app.post("/consolidate", include_in_schema=False)
    async def consolidate() -> RedirectResponse:
        return RedirectResponse(url="/memory", status_code=308)

    @app.get("/memory", summary="Retrieve similar experiences")
    async def get_memory(
        memory_type: str = Query("episodic"),
        limit: int = Query(5, ge=1, le=100),  # Increased max limit
        req: RetrieveBody = Body(default_factory=RetrieveBody),
        x_role: str | None = Header(None),
        background_tasks: BackgroundTasks = BackgroundTasks(),
    ) -> RetrieveResponse:
        """Retrieve memory records with async processing and caching."""
        start_time = time.perf_counter()
        
        role = x_role or ""
        if not _check_role("GET", "/memory", role):
            raise HTTPException(status_code=403, detail="forbidden")
        if memory_type not in ALLOWED_MEMORY_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported memory type")
        
        try:
            query = req.query or req.task_context or {}
            # Use optimized async method
            results = await service.retrieve_async(memory_type, query, limit=limit)
            
            # Add background task for performance monitoring
            response_time = time.perf_counter() - start_time
            if response_time > 0.5:
                background_tasks.add_task(
                    _log_slow_request, "get_memory", response_time, memory_type, len(results)
                )
                
            return RetrieveResponse(results=results)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/retrieve", include_in_schema=False)
    async def retrieve(
        memory_type: str = Query("episodic"), limit: int = Query(5)
    ) -> RedirectResponse:
        query = f"memory_type={memory_type}&limit={limit}"
        return RedirectResponse(url=f"/memory?{query}", status_code=308)

<<<<<<< Updated upstream
    @app.get("/provenance/{memory_type}/{record_id}", summary="Get provenance")
    async def get_provenance(
        memory_type: str,
        record_id: str,
        x_role: str | None = Header(None),
    ) -> ProvenanceResponse:
        role = x_role or ""
        if not _check_role("GET", "/provenance", role):
            raise HTTPException(status_code=403, detail="forbidden")
        prov = await asyncio.to_thread(
            service.get_provenance,
            memory_type,
            record_id,
        )
        return ProvenanceResponse(provenance=prov)

    @app.post("/skill", summary="Store a skill")
    async def store_skill(
        req: SkillRequest, x_role: str | None = Header(None)
    ) -> ConsolidateResponse:
        role = x_role or ""
        if not _check_role("POST", "/skill", role):
            raise HTTPException(status_code=403, detail="forbidden")
        sid = await asyncio.to_thread(
            service.add_skill,
            req.skill_policy,
            req.skill_representation,
            req.skill_metadata,
        )
        return ConsolidateResponse(id=sid)

    @app.post("/skill_vector_query", summary="Query skills by vector")
    async def skill_vector_query(
        req: SkillQuery, x_role: str | None = Header(None)
    ) -> RetrieveResponse:
        role = x_role or ""
        if not _check_role("POST", "/skill_vector_query", role):
            raise HTTPException(status_code=403, detail="forbidden")
        results = await asyncio.to_thread(
            service.skill_vector_query,
            req.query,
            limit=req.limit,
        )
        return RetrieveResponse(results=results)

    @app.post("/skill_metadata_query", summary="Query skills by metadata")
    async def skill_metadata_query(
        req: SkillQuery, x_role: str | None = Header(None)
    ) -> RetrieveResponse:
        role = x_role or ""
        if not _check_role("POST", "/skill_metadata_query", role):
            raise HTTPException(status_code=403, detail="forbidden")
        if not isinstance(req.query, dict):
            raise HTTPException(status_code=400, detail="metadata query must be dict")
        results = await asyncio.to_thread(
            service.skill_metadata_query,
            req.query,
            limit=req.limit,
        )
        return RetrieveResponse(results=results)

    @app.post("/evaluator_memory", summary="Store evaluator critique")
    async def evaluator_memory_store(
        req: CritiqueRequest, x_role: str | None = Header(None)
    ) -> ConsolidateResponse:
        role = x_role or ""
        if not _check_role("POST", "/evaluator_memory", role):
            raise HTTPException(status_code=403, detail="forbidden")
        cid = await asyncio.to_thread(service.store_evaluator_memory, req.critique)
        return ConsolidateResponse(id=cid)

    @app.get("/evaluator_memory", summary="Retrieve evaluator critiques")
    async def evaluator_memory_get(
        limit: int = Query(5, ge=1, le=50),
        req: CritiqueQuery = Body(default_factory=CritiqueQuery),
        x_role: str | None = Header(None),
    ) -> RetrieveResponse:
        role = x_role or ""
        if not _check_role("GET", "/evaluator_memory", role):
            raise HTTPException(status_code=403, detail="forbidden")
        query = req.query or {}
        results = await asyncio.to_thread(
            service.retrieve_evaluator_memory,
            query,
            limit=limit,
        )
        return RetrieveResponse(results=results)

=======
    @app.get("/health", summary="Health check")
    async def health_check():
        """Health check endpoint with performance metrics."""
        uptime = time.time() - app.state.start_time
        stats = service.get_stats()
        return {
            "status": "healthy",
            "uptime": uptime,
            "performance": stats,
        }
        
    @app.delete("/forget/{identifier}", summary="Forget a memory record")
    async def forget_memory(
        identifier: str,
        memory_type: str = Query("episodic"),
        hard: bool = Query(False),
        x_role: str | None = Header(None),
    ):
        """Forget a memory record with async processing."""
        role = x_role or ""
        if not _check_role("DELETE", "/forget", role):
            raise HTTPException(status_code=403, detail="forbidden")
        if memory_type not in ALLOWED_MEMORY_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported memory type")
            
        try:
            success = await service.forget_async(memory_type, identifier, hard=hard)
            if not success:
                raise HTTPException(status_code=404, detail="Memory record not found")
            return {"status": "forgotten"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Internal server error")
    
>>>>>>> Stashed changes
    return app


async def _log_slow_request(endpoint: str, response_time: float, *args) -> None:
    """Background task to log slow requests."""
    print(f"SLOW REQUEST: {endpoint} took {response_time:.3f}s with args: {args}")


def run_optimized_server(
    service: LTMService,
    host: str = HOST,
    port: int = 8081,
    workers: int = 1,
    log_level: str = "info"
) -> None:
    """Run optimized uvicorn server with performance tuning."""
    app = create_app(service)
    
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        access_log=True,
        # Performance optimizations
        loop="asyncio",  # Use asyncio loop (uvloop requires separate install)
        http="httptools",  # Use httptools for faster HTTP parsing
        # Connection tuning
        backlog=2048,
        # Keep-alive settings
        timeout_keep_alive=65,
        timeout_notify=30,
        # Limit request size
        limit_max_requests=10000,
        limit_concurrency=1000,
    )
    
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":  # pragma: no cover - manual execution
    import os
    from .episodic_memory import EpisodicMemoryService, InMemoryStorage
    from .procedural_memory import ProceduralMemoryService

<<<<<<< Updated upstream
    episodic = EpisodicMemoryService(InMemoryStorage())
    service = LTMService(
        episodic,
        procedural_memory=ProceduralMemoryService(InMemoryStorage()),
    )
    uvicorn.run(create_app(service), host=HOST, port=8081)
=======
    # Create optimized service
    max_workers = int(os.getenv("LTM_MAX_WORKERS", "8"))
    service = LTMService(EpisodicMemoryService(InMemoryStorage()), max_workers=max_workers)
    
    # Run with optimized settings
    run_optimized_server(
        service=service,
        host=HOST,
        port=int(os.getenv("LTM_PORT", "8081")),
        workers=1,  # Single worker for shared state
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
>>>>>>> Stashed changes
