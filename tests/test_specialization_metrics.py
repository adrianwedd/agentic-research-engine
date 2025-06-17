import pytest

from services.evaluation.specialization_metrics import (
    average_pairwise_divergence,
    cosine_distance,
)


def test_cosine_distance():
    assert cosine_distance([1, 0], [1, 0]) == 0.0
    assert cosine_distance([1, 0], [0, 1]) == 1.0


def test_average_pairwise_divergence():
    embeds = {
        "a": [1.0, 0.0],
        "b": [0.0, 1.0],
        "c": [1.0, 1.0],
    }
    val = average_pairwise_divergence(embeds)
    assert val == pytest.approx((1 + 0.2928932188 * 2) / 3, rel=1e-5)
