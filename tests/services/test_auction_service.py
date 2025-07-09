import pytest

from services import AuctionConfig, AuctionMechanism, Workload, select_auction_mechanism


@pytest.mark.parametrize(
    "workload,expected",
    [
        (Workload(complexity=0.9, num_tasks=5, budget=0.9), AuctionMechanism.VCG),
        (Workload(complexity=0.3, num_tasks=15, budget=0.3), AuctionMechanism.PSI),
        (Workload(complexity=0.5, num_tasks=8, budget=0.5), AuctionMechanism.GCAA),
        (Workload(complexity=0.8, num_tasks=3, budget=0.5), AuctionMechanism.SSI),
        (
            Workload(complexity=0.6, num_tasks=2, budget=0.4),
            AuctionMechanism.COMBINATORIAL,
        ),
    ],
)
def test_select_mechanism(workload, expected):
    assert select_auction_mechanism(workload) == expected


def test_custom_config():
    cfg = AuctionConfig(high_complexity=0.5, many_tasks=5)
    wl = Workload(complexity=0.6, num_tasks=6, budget=0.4)
    assert select_auction_mechanism(wl, cfg) == AuctionMechanism.GCAA
