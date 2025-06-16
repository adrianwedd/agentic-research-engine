"""Learning utilities and optimizers."""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from .exceptions import ConfigurationError
    from .marl_trainer import MARLTrainer
    from .ppo_policy_optimizer import PPOPolicyOptimizer
    from .rlaif_system import RLAIFSystem


def __getattr__(name: str):
    if name == "PPOPolicyOptimizer":
        return import_module(".ppo_policy_optimizer", __name__).PPOPolicyOptimizer
    if name == "RLAIFSystem":
        return import_module(".rlaif_system", __name__).RLAIFSystem
    if name == "MARLTrainer":
        return import_module(".marl_trainer", __name__).MARLTrainer
    if name == "ConfigurationError":
        return import_module(".exceptions", __name__).ConfigurationError
    raise AttributeError(name)


__all__ = ["RLAIFSystem", "PPOPolicyOptimizer", "MARLTrainer", "ConfigurationError"]
