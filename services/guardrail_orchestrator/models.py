from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    direction = Column(String, nullable=False)
    allowed = Column(Boolean, default=True)
    reasons = Column(JSON, default=list)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
