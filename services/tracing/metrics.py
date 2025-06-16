from __future__ import annotations

"""Context utilities for accumulating task-level metrics."""

from contextvars import ContextVar
from typing import Dict

# Each task run resets this context variable with a new metrics dict
_CURRENT_METRICS: ContextVar[Dict[str, float]] = ContextVar(
    "CURRENT_METRICS", default={}
)


def reset_metrics() -> Dict[str, float]:
    """Initialize and return a fresh metrics dictionary for the current context."""
    metrics: Dict[str, float] = {
        "total_tokens_consumed": 0.0,
        "tool_call_count": 0.0,
    }
    _CURRENT_METRICS.set(metrics)
    return metrics


def get_metrics() -> Dict[str, float]:
    """Return the metrics dictionary for the current context."""
    return _CURRENT_METRICS.get()


def increment_metric(name: str, value: float = 1.0) -> None:
    """Increment a numeric metric in the current context."""
    metrics = _CURRENT_METRICS.get()
    metrics[name] = metrics.get(name, 0.0) + value
    _CURRENT_METRICS.set(metrics)
