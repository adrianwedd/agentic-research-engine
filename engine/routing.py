from __future__ import annotations

from typing import Callable, Dict

from .state import State


class RoutingError(Exception):
    """Raised when a router cannot determine the next node."""


def make_status_router(mapping: Dict[str, str]) -> Callable[[State], str]:
    """Create a router that selects the next node based on ``state.data['status']``.

    Parameters
    ----------
    mapping:
        Map of status values to destination node names.

    Returns
    -------
    Callable[[State], str]
        Router function that returns the destination node.

    Raises
    ------
    RoutingError
        If the status value is missing or not present in ``mapping``.
    """

    def router(state: State) -> str:
        status = state.data.get("status")
        try:
            return mapping[status]
        except KeyError as exc:  # pragma: no cover - simple error path
            raise RoutingError(f"Unknown status: {status}") from exc

    return router


def make_cosc_router(
    *,
    retry_node: str,
    pass_node: str,
    max_retries: int,
    score_threshold: float = 1.0,
    fail_node: str | None = None,
) -> Callable[[State], str]:
    """Create a router implementing the Chain of Self-Correction logic.

    Parameters
    ----------
    retry_node:
        Node to route to when evaluation fails and retries remain.
    pass_node:
        Node to route to when evaluation passes.
    max_retries:
        Maximum number of allowed retries.
    score_threshold:
        Minimum overall score considered a pass.
    fail_node:
        Optional node to route to when retries are exhausted and evaluation
        still fails. If ``None`` the router will proceed to ``pass_node``.
    """

    def router(state: State) -> str:
        score = 1.0
        if isinstance(state.evaluator_feedback, dict):
            score = float(state.evaluator_feedback.get("overall_score", score))
        elif state.evaluator_feedback is not None:
            try:
                score = float(state.evaluator_feedback)
            except (TypeError, ValueError):
                score = 0.0

        if score < score_threshold:
            if state.retry_count < max_retries:
                state.retry_count += 1
                return retry_node
            if fail_node is not None:
                return fail_node
        return pass_node

    return router
