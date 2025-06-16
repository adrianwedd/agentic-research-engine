import pytest

from services.evaluation import compute_cic, compute_interpretability, compute_zsc_score
from services.ltm_service import SimpleEmbeddingClient


def test_compute_zsc_score():
    assert compute_zsc_score([1.0, 2.0, 3.0]) == 2.0
    assert compute_zsc_score([]) == 0.0


def test_compute_cic():
    msgs = ["a", "a", "b", "b"]
    acts = ["a", "a", "b", "b"]
    val = compute_cic(msgs, acts)
    assert val == pytest.approx(0.6931, rel=1e-3)
    assert compute_cic([], []) == 0.0


def test_compute_interpretability():
    embedder = SimpleEmbeddingClient()
    concepts = ["hi", "bye"]
    vecs = embedder.embed(concepts)
    score = compute_interpretability(vecs, concepts, embedder)
    assert score == pytest.approx(1.0)
