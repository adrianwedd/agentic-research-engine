from __future__ import annotations

import asyncio
import contextlib
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator, constr
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from services.monitoring.events import event_stream

from .models import Base
from .service import ReputationService

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reputation.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

service = ReputationService(SessionLocal)
app = FastAPI(
    title="Reputation Service", 
    version=os.getenv("SERVICE_VERSION", "1.0.0"),
    description="Production-ready reputation service with health monitoring"
)

# Service startup time for readiness checks
STARTUP_TIME = time.time()

# Security middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

# Rate limiting storage (in-memory for simplicity, use Redis in production)
request_counts: Dict[str, Dict[str, float]] = {}

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Security middleware for rate limiting and security headers."""
    # Rate limiting based on IP address
    client_ip = request.client.host if request.client else "unknown"
    current_time = time.time()
    
    # Clean old entries (older than 1 minute)
    if client_ip in request_counts:
        request_counts[client_ip] = {
            timestamp: count for timestamp, count in request_counts[client_ip].items()
            if current_time - float(timestamp) < 60
        }
    
    # Check rate limit (30 requests per minute per IP)
    if client_ip not in request_counts:
        request_counts[client_ip] = {}
    
    minute_key = str(int(current_time // 60) * 60)
    current_count = request_counts[client_ip].get(minute_key, 0)
    
    if current_count >= 30:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"Retry-After": "60"}
        )
    
    request_counts[client_ip][minute_key] = current_count + 1
    
    # Process request
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response


@app.on_event("startup")
async def _start_listener() -> None:
    async def _run() -> None:
        async for evt in event_stream():
            service.handle_evaluation_event(evt)

    app.state.listener_task = asyncio.create_task(_run())


@app.on_event("shutdown")
async def _stop_listener() -> None:
    task = getattr(app.state, "listener_task", None)
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


def _parse_api_keys(raw: str) -> Dict[str, str]:
    """Parse API keys from string with security validation."""
    mapping: Dict[str, str] = {}
    for pair in raw.split(","):
        if not pair.strip():
            continue
        try:
            role, token = pair.split(":", 1)
            role = role.strip()
            token = token.strip()
            
            # Security validation
            if len(token) < 32:
                raise ValueError(f"Token for role '{role}' is too short (minimum 32 characters)")
            if not role or not token:
                raise ValueError("Role and token cannot be empty")
            if role in ["", "null", "undefined"]:
                raise ValueError(f"Invalid role: {role}")
                
            mapping[token] = role
        except ValueError as e:
            if "not enough values to unpack" in str(e):
                raise ValueError(f"Invalid API key format in pair: {pair}")
            raise
    return mapping


# Load API keys from environment (no default tokens for security)
API_KEYS_RAW = os.getenv("REPUTATION_API_KEYS")
if not API_KEYS_RAW:
    raise ValueError(
        "REPUTATION_API_KEYS environment variable must be set. "
        "Format: 'role1:token1,role2:token2'"
    )
API_KEYS = _parse_api_keys(API_KEYS_RAW)


def get_role(authorization: str = Header(...)) -> str:
    """Authenticate request and return role with security hardening."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="unauthorized",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        token = authorization.split()[1]
        # Basic token format validation
        if len(token) < 32:
            raise HTTPException(status_code=401, detail="unauthorized")
        
        role = API_KEYS.get(token)
        if not role:
            raise HTTPException(status_code=401, detail="unauthorized")
        
        return role
    except (IndexError, AttributeError):
        raise HTTPException(
            status_code=401, 
            detail="unauthorized",
            headers={"WWW-Authenticate": "Bearer"}
        )


def require_role(allowed: List[str]):
    def _inner(role: str = Depends(get_role)) -> str:
        if role not in allowed:
            raise HTTPException(status_code=403, detail="forbidden")
        return role

    return _inner


router = APIRouter(prefix="/v1")


class AgentCreate(BaseModel):
    agent_type: constr(min_length=1, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    model_base: Optional[constr(min_length=1, max_length=100)] = None
    status: constr(regex=r'^(active|inactive|suspended)$') = "active"
    
    @validator('agent_type')
    def validate_agent_type(cls, v):
        if v.lower() in ['system', 'root', 'admin', 'null']:
            raise ValueError('Reserved agent type')
        return v


class TaskCreate(BaseModel):
    task_type: constr(min_length=1, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    query_text: Optional[constr(max_length=1000)] = None
    parent_task_id: Optional[constr(regex=r'^[a-zA-Z0-9-]{36}$')] = None
    
    @validator('query_text')
    def validate_query_text(cls, v):
        if v and any(char in v for char in ['<', '>', '&', '"', "'"]):
            raise ValueError('Query text contains potentially unsafe characters')
        return v


class AssignmentCreate(BaseModel):
    task_id: constr(regex=r'^[a-zA-Z0-9-]{36}$')
    agent_id: constr(regex=r'^[a-zA-Z0-9-]{36}$')


class EvaluationCreate(BaseModel):
    assignment_id: constr(regex=r'^[a-zA-Z0-9-]{36}$')
    evaluator_id: constr(min_length=1, max_length=50)
    performance_vector: Dict[str, Any] = Field(default_factory=dict)
    is_final: bool = False
    
    @validator('performance_vector')
    def validate_performance_vector(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Performance vector must be a dictionary')
        if len(v) > 50:
            raise ValueError('Performance vector cannot have more than 50 keys')
        for key, value in v.items():
            if not isinstance(key, str) or len(key) > 100:
                raise ValueError('Performance vector keys must be strings with max 100 chars')
            if not isinstance(value, (int, float, str, bool)):
                raise ValueError('Performance vector values must be int, float, string, or boolean')
        return v


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


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Liveness probe endpoint - checks if the service is running."""
    try:
        # Basic health check - service is responsive
        return {
            "status": "healthy",
            "service": "reputation-service",
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
        
        # Test database connectivity
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "service": "reputation-service",
            "version": os.getenv("SERVICE_VERSION", "1.0.0"),
            "uptime_seconds": round(uptime, 2),
            "database": "connected"
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
        "service": "reputation-service",
        "uptime_seconds": round(uptime, 2),
        "version": os.getenv("SERVICE_VERSION", "1.0.0"),
        "environment": os.getenv("ENVIRONMENT", "development")
    }


app.include_router(router, prefix="/api")
