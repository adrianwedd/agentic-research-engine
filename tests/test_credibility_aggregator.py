from engine.collaboration.credibility_aggregator import CredibilityAwareAggregator


def test_weighted_aggregation():
    scores = {"A": 0.9, "B": 0.1}
    contributions = {"A": 10.0, "B": 20.0}

    aggregator = CredibilityAwareAggregator(lambda aid: scores.get(aid, 0.0))
    result = aggregator.aggregate(contributions)

    expected = (10.0 * 0.9 + 20.0 * 0.1) / (0.9 + 0.1)
    assert result == expected


def test_zero_scores_fallback():
    scores = {"A": 0.0, "B": 0.0}
    contributions = {"A": 1.0, "B": 3.0}

    aggregator = CredibilityAwareAggregator(lambda aid: scores.get(aid, 0.0))
    result = aggregator.aggregate(contributions)

    assert result == 2.0
