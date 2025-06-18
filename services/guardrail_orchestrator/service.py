from __future__ import annotations

import re
from typing import Callable, List, Tuple

from sqlalchemy.orm import Session

from .models import AuditLog


class GuardrailService:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def _detect_prompt_injection(self, text: str) -> bool:
        patterns = [
            r"(?i)ignore\s+previous",
            r"(?i)system:\s",
            r"(?i)assistant:\s",
        ]
        return any(re.search(p, text) for p in patterns)

    def _detect_pii(self, text: str) -> bool:
        email = re.compile(r"[\w.-]+@[\w.-]+")
        phone = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")
        return bool(email.search(text) or phone.search(text))

    def validate(self, text: str, direction: str) -> Tuple[bool, List[str]]:
        reasons: List[str] = []
        if self._detect_prompt_injection(text):
            reasons.append("prompt_injection")
        if self._detect_pii(text):
            reasons.append("pii")
        allowed = not reasons
        self._log(text, direction, allowed, reasons)
        return allowed, reasons

    def _log(self, text: str, direction: str, allowed: bool, reasons: List[str]) -> None:
        with self._session_factory() as session:
            rec = AuditLog(
                text=text,
                direction=direction,
                allowed=allowed,
                reasons=reasons,
            )
            session.add(rec)
            session.commit()
