from __future__ import annotations

"""PPO-based policy optimizer using the TRL library."""

from pathlib import Path
from typing import Dict

import logging

from transformers import AutoTokenizer
from trl import AutoModelForCausalLMWithValueHead, PPOConfig, PPOTrainer

logger = logging.getLogger(__name__)


class PPOPolicyOptimizer:
    """Wrapper around :class:`~trl.PPOTrainer` to update language model policies."""

    def __init__(self, model_name: str, *, lr: float = 1e-5, log_dir: str | Path | None = None) -> None:
        self.model_name = model_name
        self.log_dir = Path(log_dir or "ppo_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.config = PPOConfig(model_name=model_name, learning_rate=lr)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLMWithValueHead.from_pretrained(model_name)
        self.trainer = PPOTrainer(config=self.config, model=self.model, tokenizer=self.tokenizer)
        self.step_count = 0

    def update(self, trajectory: Dict, reward: float) -> float:
        """Run a single PPO update step for ``trajectory`` with ``reward``."""
        query = trajectory.get("prompt", "")
        response = trajectory.get("response", "")
        stats = self.trainer.step([query], [response], [reward])
        self.step_count += 1
        loss = float(stats.get("ppo/loss/total", 0.0))
        for key, val in stats.items():
            logger.info("%s: %s", key, val)
        self.save()
        return loss

    def save(self, path: str | Path | None = None) -> None:
        """Persist the current policy model to ``path``."""
        dest = Path(path or self.log_dir / "policy")
        dest.mkdir(parents=True, exist_ok=True)
        self.model.save_pretrained(dest)
        self.tokenizer.save_pretrained(dest)
