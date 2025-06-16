from __future__ import annotations

from typing import Dict

from .exceptions import ConfigurationError


class MARLTrainer:
    """Simplified multi-agent training loop."""

    def __init__(self, config: Dict) -> None:
        if "guidance_loss" not in config:
            raise ConfigurationError(
                "guidance_loss block required by ADR-003 for LLM-grounded training"
            )
        self.config = config
        self.guidance_loss_cfg = config["guidance_loss"]

    def train(self) -> None:  # pragma: no cover - placeholder
        """Run a single training step (stub)."""
        pass
