from __future__ import annotations

"""Aggregate agent contributions using credibility weights."""

from typing import Callable, Dict, Mapping


class CredibilityAwareAggregator:
    """Combine numeric contributions weighted by agent credibility."""

    def __init__(self, score_provider: Callable[[str], float]) -> None:
        """Create a new aggregator.

        Args:
            score_provider (Callable[[str], float]): Function returning the
                credibility score for a given agent id.
        """

        self._score_provider = score_provider

    def aggregate(self, contributions: Mapping[str, float]) -> float:
        """Return weighted average of contributions using credibility scores."""
        if not contributions:
            return 0.0
        weights: Dict[str, float] = {
            aid: float(self._score_provider(aid)) for aid in contributions
        }
        total_weight = sum(weights.values())
        if total_weight == 0.0:
            return sum(contributions.values()) / len(contributions)
        return (
            sum(contributions[aid] * weights[aid] for aid in contributions)
            / total_weight
        )
