from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from sentence_transformers import SentenceTransformer, util


class LinearPreferenceModel:
    """Simple linear preference model used as the base quality scorer."""

    def __init__(self, weights: Dict[str, float]):
        self.a = float(weights.get("a", 0))
        self.b = float(weights.get("b", 0))

    @classmethod
    def from_file(cls, path: str | Path) -> "LinearPreferenceModel":
        weights = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(weights)

    def score(self, prompt: str, output: str) -> float:  # noqa: D401
        """Return linear score based on output length."""
        length = len(str(output).split())
        return self.a * length + self.b


@dataclass
class CompositeRewardConfig:
    w_quality: float = 1.0
    w_correction: float = 1.0
    w_cost: float = 0.1
    beta: float = 1.0
    alpha: float = 1.0
    tau_fail: float = 0.2
    tau_pass: float = 0.8
    lambda_cost: float = 0.01


class CompositeRewardFunction:
    """Calculate a SCoRe-inspired composite reward."""

    def __init__(
        self,
        preference_model: LinearPreferenceModel,
        sbert_model: str | SentenceTransformer = "paraphrase-MiniLM-L6-v2",
        config: CompositeRewardConfig | None = None,
    ) -> None:
        self.preference_model = preference_model
        self.sbert = (
            sbert_model
            if isinstance(sbert_model, SentenceTransformer)
            else SentenceTransformer(sbert_model)
        )
        self.config = config or CompositeRewardConfig()
        self.last_components: Dict[str, float] | None = None
        self.logger = logging.getLogger(__name__)

    def semantic_distance(self, output1: str, output2: str) -> float:
        embeddings = self.sbert.encode([output1, output2], convert_to_tensor=True)
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        return 1 - similarity

    def __call__(self, prompt: str, output1: str, output2: str) -> float:
        pm2 = self.preference_model.score(prompt, output2)
        pm1 = self.preference_model.score(prompt, output1)
        r_base = pm2
        r_progress = (
            self.config.beta
            if pm2 > self.config.tau_pass and pm1 < self.config.tau_fail
            else 0.0
        )
        distance = self.semantic_distance(output1, output2)
        m_semantic = max(0.0, min(1.0, self.config.alpha * distance))
        c_eff = self.config.lambda_cost * len(output2.split())
        reward = (
            self.config.w_quality * r_base
            + self.config.w_correction * (r_progress * m_semantic)
            - self.config.w_cost * c_eff
        )
        self.last_components = {
            "base_quality": r_base,
            "progress_bonus": r_progress,
            "semantic_multiplier": m_semantic,
            "efficiency_cost": c_eff,
        }
        self.logger.debug("Reward components: %s", self.last_components)
        return reward
