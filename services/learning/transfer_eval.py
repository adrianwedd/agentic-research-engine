from __future__ import annotations

"""Toy transfer/generalization evaluation utilities."""

from typing import Dict, Iterable

from .feudal_network import Manager


def evaluate_transfer(tasks: Iterable[Dict[str, any]], manager: Manager) -> Dict[str, float]:
    """Return success rate across tasks using the given manager."""

    total = 0
    success = 0
    for task in tasks:
        total += 1
        goal = task.get("goal")
        description = task.get("description", "")
        manager.worker.env.goal = goal
        manager.worker.env.reset()
        manager.act(description)
        if manager.worker.env.state == goal:
            success += 1
    return {"success_rate": success / float(total) if total else 0.0}
