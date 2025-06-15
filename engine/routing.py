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
