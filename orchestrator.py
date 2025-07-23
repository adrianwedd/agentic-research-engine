from __future__ import annotations

"""Command line and REST entry point for the research orchestrator."""

import argparse
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from engine.orchestrator import Orchestrator, Planner, Reflector

app = FastAPI(title="Research Orchestrator")

orc: Orchestrator = Orchestrator(Planner(), Reflector())


class RunRequest(BaseModel):
    prompt: str


@app.post("/run")
async def run_endpoint(req: RunRequest) -> dict[str, str]:
    """FastAPI endpoint executing a research task."""
    result: str = orc.run_task(req.prompt)
    return {"result": result}


def run_cli(argv: Optional[list[str]] = None) -> None:
    """Execute a research task from the command line."""
    parser = argparse.ArgumentParser(description="Run orchestrator task")
    parser.add_argument("prompt", help="Task prompt")
    args = parser.parse_args(argv)
    result: str = orc.run_task(args.prompt)
    print(result)


if __name__ == "__main__":  # pragma: no cover - manual invocation
    run_cli()
