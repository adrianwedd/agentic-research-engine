from __future__ import annotations

import logging
import math
from typing import Dict, Iterable, List, Tuple

from services.ltm_service import SimpleEmbeddingClient

from .exceptions import ConfigurationError


class MARLTrainer:
    """Simplified multi-agent training loop."""

    def __init__(
        self, config: Dict, dataset: Dict[Tuple[str, str], str] | None = None
    ) -> None:
        if "guidance_loss" not in config:
            raise ConfigurationError(
                "guidance_loss block required by ADR-003 for LLM-grounded training"
            )
        self.config = config
        self.guidance_loss_cfg = config["guidance_loss"]
        self.dataset = dataset or {}
        self.embedder = SimpleEmbeddingClient()
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na and nb else 0.0

    def train(self, batch: Iterable[Dict]) -> None:
        """Run a toy training loop computing guidance loss."""
        weight = float(self.guidance_loss_cfg.get("weight", 1.0))
        for item in batch:
            obs = item.get("observation", "")
            act = item.get("action", "")
            msg_vec: List[float] = item.get("message_vec", [])
            policy_loss = float(item.get("policy_loss", 0.0))
            ref_text = self.dataset.get((obs, act), "")
            ref_vec = (
                self.embedder.embed([ref_text])[0] if ref_text else [0.0] * len(msg_vec)
            )
            guidance_loss = 1.0 - self._cosine(msg_vec, ref_vec)
            total = policy_loss + weight * guidance_loss
            self.logger.info(
                "policy_loss=%s guidance_loss=%s", policy_loss, guidance_loss
            )
            item["total_loss"] = total
