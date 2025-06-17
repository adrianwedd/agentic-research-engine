from __future__ import annotations

"""Metrics for measuring policy divergence and specialization."""

import math
from typing import Mapping, Sequence


def cosine_distance(vec1: Sequence[float], vec2: Sequence[float]) -> float:
    """Return cosine distance ``1 - cosine_similarity`` between two vectors."""
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if not norm1 or not norm2:
        return 0.0
    return 1.0 - dot / (norm1 * norm2)


def average_pairwise_divergence(embeddings: Mapping[str, Sequence[float]]) -> float:
    """Compute average pairwise cosine distance between agent embeddings."""
    agent_ids = list(embeddings)
    if len(agent_ids) < 2:
        return 0.0
    total = 0.0
    count = 0
    for i, aid in enumerate(agent_ids):
        vec_i = embeddings[aid]
        for j in range(i + 1, len(agent_ids)):
            vec_j = embeddings[agent_ids[j]]
            total += cosine_distance(vec_i, vec_j)
            count += 1
    return total / count if count else 0.0
