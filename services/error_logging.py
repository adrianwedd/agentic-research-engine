from __future__ import annotations

"""Middleware for structured error logging in agent flows."""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ErrorLoggingMiddleware:
    """Capture unhandled exceptions with structured context."""

    def __init__(
        self, *, enabled: bool = True, logger: logging.Logger | None = None
    ) -> None:
        self.enabled = enabled
        self.logger = logger or logging.getLogger(__name__)

    def __call__(self, exc: Exception, node: str, state: Any) -> None:
        if not self.enabled:
            return
        try:
            state_data = (
                state.model_dump() if hasattr(state, "model_dump") else str(state)
            )
        except Exception:
            state_data = str(state)
        payload = {
            "node": node,
            "error": str(exc),
            "state": state_data,
        }
        self.logger.error(
            "Unhandled agent error", extra={"error_payload": json.dumps(payload)}
        )
