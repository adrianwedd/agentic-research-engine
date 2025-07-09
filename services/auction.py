from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuctionMechanism(str, Enum):
    """Available auction mechanisms."""

    SSI = "sequential_single_item"
    PSI = "parallel_single_item"
    GCAA = "greedy_coalition"
    COMBINATORIAL = "combinatorial"
    VCG = "vcg"


@dataclass
class Workload:
    """Characteristics of the upcoming workload."""

    complexity: float  # 0.0-1.0 subjective measure
    num_tasks: int
    budget: float  # normalized 0-1 scale


@dataclass
class AuctionConfig:
    """Configuration thresholds for mechanism selection."""

    high_complexity: float = 0.7
    high_budget: float = 0.7
    many_tasks: int = 10


def select_auction_mechanism(
    workload: Workload, config: AuctionConfig | None = None
) -> AuctionMechanism:
    """Select the best auction mechanism based on workload parameters."""

    cfg = config or AuctionConfig()

    if (
        workload.complexity >= cfg.high_complexity
        and workload.budget >= cfg.high_budget
    ):
        return AuctionMechanism.VCG
    if workload.num_tasks >= cfg.many_tasks:
        if workload.complexity <= 0.4:
            return AuctionMechanism.PSI
        return AuctionMechanism.GCAA
    if (
        workload.num_tasks >= cfg.many_tasks // 2
        and workload.complexity <= cfg.high_complexity
    ):
        return AuctionMechanism.GCAA
    if workload.complexity >= cfg.high_complexity:
        return AuctionMechanism.SSI
    return AuctionMechanism.COMBINATORIAL


__all__ = [
    "AuctionMechanism",
    "Workload",
    "AuctionConfig",
    "select_auction_mechanism",
]
