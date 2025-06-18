from __future__ import annotations

"""Utilities for persisting simulation runs."""

import json
from pathlib import Path
from typing import Any, Dict, List

try:  # optional dependency
    from opentelemetry.sdk.trace import ReadableSpan
except Exception:  # pragma: no cover - fallback
    ReadableSpan = Any

from engine.state import State

from .graph_api import spans_to_graph

_SIM_DIR = Path(__file__).with_name("simulations")
_SIM_DIR.mkdir(exist_ok=True)


def save_simulation(
    run_id: str, state: State, metrics: Dict[str, float], spans: List[ReadableSpan]
) -> None:
    """Persist a simulation result to a JSON file."""
    data = {
        "state": state.model_dump(),
        "metrics": metrics,
        "graph": spans_to_graph(spans),
    }
    path = _SIM_DIR / f"{run_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_simulation(run_id: str) -> Dict[str, Any]:
    """Load a previously saved simulation."""
    path = _SIM_DIR / f"{run_id}.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
