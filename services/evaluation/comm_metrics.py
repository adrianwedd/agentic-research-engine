from __future__ import annotations

import math
from collections import Counter
from typing import Sequence

from services.ltm_service import SimpleEmbeddingClient


def compute_zsc_score(rewards: Sequence[float]) -> float:
    """Return mean reward over evaluation episodes."""
    return sum(rewards) / len(rewards) if rewards else 0.0


def compute_cic(messages: Sequence[str], actions: Sequence[str]) -> float:
    """Compute mutual information between messages and subsequent actions."""
    if len(messages) != len(actions):
        raise ValueError("messages and actions must be same length")
    n = len(messages)
    if n == 0:
        return 0.0

    joint = Counter(zip(messages, actions))
    msg_counts = Counter(messages)
    act_counts = Counter(actions)

    mi = 0.0
    for (m, a), count in joint.items():
        p_joint = count / n
        p_m = msg_counts[m] / n
        p_a = act_counts[a] / n
        mi += p_joint * math.log(p_joint / (p_m * p_a + 1e-12) + 1e-12)
    return mi


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def compute_interpretability(
    message_vectors: Sequence[Sequence[float]],
    concept_texts: Sequence[str],
    embedder: SimpleEmbeddingClient | None = None,
) -> float:
    """Compute average cosine similarity between messages and concept embeddings."""
    if len(message_vectors) != len(concept_texts):
        raise ValueError("message_vectors and concept_texts must be same length")
    if not message_vectors:
        return 0.0
    embedder = embedder or SimpleEmbeddingClient()
    concept_vectors = embedder.embed(list(concept_texts))
    sims = [_cosine(m, c) for m, c in zip(message_vectors, concept_vectors)]
    return sum(sims) / len(sims)
