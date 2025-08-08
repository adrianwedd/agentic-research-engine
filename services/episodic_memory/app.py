from __future__ import annotations

import asyncio
import os
import time
from typing import Dict, List, Optional

<<<<<<< Updated upstream
"""Minimal FastAPI service exposing episodic memory operations."""

from fastapi import Body, FastAPI
=======
from fastapi import Body, FastAPI, HTTPException, status
>>>>>>> Stashed changes
from pydantic import BaseModel, Field

from services.ltm_service import EpisodicMemoryService
from services.ltm_service.persistent_storage import create_storage_backend
from services.reliability import resilient_endpoint, health_checker, graceful_shutdown


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


# Initialize with persistent storage backend
storage = create_storage_backend(os.getenv("STORAGE_BACKEND", "file"))
service = EpisodicMemoryService(storage)

# Register health checks
health_checker.register_check("storage", lambda: storage.health_check() if hasattr(storage, 'health_check') else {"status": "healthy"})
health_checker.register_check("service", lambda: {"status": "healthy", "storage_type": type(storage).__name__})

# Register cleanup for graceful shutdown
graceful_shutdown.register_cleanup(lambda: None)  # Add actual cleanup if needed

app = FastAPI(
    title="Episodic Memory Service",
    version=os.getenv("SERVICE_VERSION", "1.0.0"),
    description="Production-ready episodic memory service with health monitoring"
)

# Service startup time for readiness checks
STARTUP_TIME = time.time()


@app.post("/consolidate", response_model=ConsolidateResponse)
@resilient_endpoint(timeout=30)
async def consolidate(req: ConsolidateRequest) -> ConsolidateResponse:
    """Store a completed experience in episodic memory."""
    rec_id = await asyncio.to_thread(
        service.store_experience,
        req.task_context,
        req.execution_trace,
        req.outcome,
    )
    return ConsolidateResponse(id=rec_id)


@app.get("/retrieve", response_model=RetrieveResponse)
@resilient_endpoint(timeout=30)
async def retrieve(
    limit: int = 5,
    body: RetrieveBody = Body(default_factory=RetrieveBody),
) -> RetrieveResponse:
    """Retrieve experiences similar to the provided query."""
    query = body.query or body.task_context or {}
    results = await asyncio.to_thread(
        service.retrieve_similar_experiences,
        query,
        limit=limit,
    )
    return RetrieveResponse(results=results)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Liveness probe endpoint - checks if the service is running."""
    try:
        # Basic health check - service is responsive
        return {
            "status": "healthy",
            "service": "episodic-memory",
            "version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "timestamp": str(time.time())
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@app.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """Readiness probe endpoint - checks if the service can handle requests."""
    try:
        # Check if service has been running for minimum time
        uptime = time.time() - STARTUP_TIME
        if uptime < 5:  # Minimum 5 seconds startup time
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service is still starting up"
            )
        
        # Run comprehensive health checks
        health_results = await health_checker.run_checks()
        overall_status = health_checker.get_overall_status()
        
        if overall_status != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Health checks failed: {health_results}"
            )
        
        # Test basic service functionality
        test_query = {"test": "readiness_check"}
        await asyncio.to_thread(
            service.retrieve_similar_experiences,
            test_query,
            limit=1,
        )
        
        return {
            "status": "ready",
            "service": "episodic-memory",
            "version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "uptime_seconds": round(uptime, 2),
            "storage_backend": type(storage).__name__,
            "health_checks": health_results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}"
        )


@app.get("/metrics")
async def metrics() -> Dict[str, any]:
    """Basic metrics endpoint for monitoring."""
    uptime = time.time() - STARTUP_TIME
    return {
        "service": "episodic-memory",
        "uptime_seconds": round(uptime, 2),
        "version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }
