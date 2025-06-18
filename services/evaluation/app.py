import os
import uuid
from typing import Any, Dict, List, Optional

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel


def _parse_api_keys(raw: str) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for pair in raw.split(","):
        if not pair:
            continue
        role, token = pair.split(":", 1)
        mapping[token.strip()] = role.strip()
    return mapping


API_KEYS = _parse_api_keys(
    os.getenv("EVALUATION_API_KEYS", "editor:eval-token,viewer:view-token")
)


app = FastAPI(title="Evaluation Service", version="1.0.0")

_STORE: Dict[str, Dict[str, Any]] = {}


class CritiqueIn(BaseModel):
    critique: Dict[str, Any]


class CritiqueQuery(BaseModel):
    query: Optional[Dict[str, Any]] = None


def get_role(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
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


@app.post("/evaluator_memory", dependencies=[Depends(require_role(["editor"]))])
def store_critique(req: CritiqueIn) -> Dict[str, str]:
    cid = str(uuid.uuid4())
    record = dict(req.critique)
    record["id"] = cid
    _STORE[cid] = record
    return {"id": cid}


@app.get(
    "/evaluator_memory",
    dependencies=[Depends(require_role(["viewer", "editor"]))],
)
def get_critiques(
    limit: int = Query(5, ge=1, le=50),
    body: CritiqueQuery = Body(default_factory=CritiqueQuery),
) -> Dict[str, List[Dict[str, Any]]]:
    query = body.query or {}
    results = []
    for rec in _STORE.values():
        if all(rec.get(k) == v for k, v in query.items()):
            results.append(rec)
    return {"results": results[:limit]}
