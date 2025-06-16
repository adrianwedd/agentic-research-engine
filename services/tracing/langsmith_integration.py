from __future__ import annotations

"""Utilities for integrating with LangSmith tracing and datasets."""

import json
import os
from typing import Any

try:  # pragma: no cover - optional dependency
    from langsmith import Client
except Exception:  # pragma: no cover - fallback

    class Client:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            raise ImportError("langsmith package is required")


def configure_langsmith(project_name: str) -> None:
    """Set environment variables for LangSmith tracing."""
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", project_name)


class LangSmithCheckpointer:
    """Simple checkpointer that logs state transitions to LangSmith."""

    def __init__(self, client: Client, project_name: str = "default") -> None:
        self.client = client
        self.project_name = project_name

    def start(self, run_id: str, state: Any) -> None:  # pragma: no cover - thin wrapper
        self.client.create_run(
            id=run_id,
            name="graph",
            inputs=getattr(state, "data", {}),
            run_type="chain",
            project_name=self.project_name,
        )

    def save(
        self, run_id: str, node: str, state: Any
    ) -> None:  # pragma: no cover - thin wrapper
        self.client.create_run(
            id=f"{run_id}-{node}",
            parent_run_id=run_id,
            name=node,
            inputs=getattr(state, "data", {}),
            run_type="tool",
            project_name=self.project_name,
        )


def import_dataset(path: str, dataset_name: str, client: Client | None = None) -> None:
    """Import a JSON QA dataset into LangSmith if it does not exist."""
    client = client or Client()
    if client.has_dataset(dataset_name=dataset_name):
        return
    dataset = client.create_dataset(dataset_name)
    with open(path, "r", encoding="utf-8") as f:
        cases = json.load(f)
    for case in cases:
        client.create_example(
            inputs={"question": case.get("question", "")},
            outputs={"answer": case.get("answer", "")},
            dataset_id=dataset.id,
        )
