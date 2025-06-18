from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base
from .service import GuardrailService

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./guardrail.db")


class TextRequest(BaseModel):
    text: str


class ValidationResponse(BaseModel):
    safe: bool
    reasons: list[str]


def create_app(service: GuardrailService | None = None) -> FastAPI:
    if service is None:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        service = GuardrailService(SessionLocal)
    app = FastAPI(title="Guardrail Orchestrator")

    @app.post("/validate_input", response_model=ValidationResponse)
    async def validate_input(req: TextRequest):
        allowed, reasons = service.validate(req.text, "input")
        if not allowed:
            raise HTTPException(status_code=400, detail={"reasons": reasons})
        return ValidationResponse(safe=True, reasons=[])

    @app.post("/validate_output", response_model=ValidationResponse)
    async def validate_output(req: TextRequest):
        allowed, reasons = service.validate(req.text, "output")
        if not allowed:
            raise HTTPException(status_code=400, detail={"reasons": reasons})
        return ValidationResponse(safe=True, reasons=[])

    return app


app = create_app()
