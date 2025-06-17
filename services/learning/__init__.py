"""Learning utilities and optimizers."""

from importlib import import_module
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - for type checkers only
    from .exceptions import ConfigurationError
    from .feudal_network import Manager, Worker
    from .marl_trainer import MARLTrainer
    from .ppo_policy_optimizer import PPOPolicyOptimizer
    from .rlaif_system import RLAIFSystem
    from .skill_discovery import SkillDiscoveryModule
    from .skill_spec import SkillSpec, generate_skill_specs, store_skill_specs


def __getattr__(name: str):
    if name == "PPOPolicyOptimizer":
        return import_module(".ppo_policy_optimizer", __name__).PPOPolicyOptimizer
    if name == "RLAIFSystem":
        return import_module(".rlaif_system", __name__).RLAIFSystem
    if name == "MARLTrainer":
        return import_module(".marl_trainer", __name__).MARLTrainer
    if name == "SkillDiscoveryModule":
        return import_module(".skill_discovery", __name__).SkillDiscoveryModule
    if name == "Manager":
        return import_module(".feudal_network", __name__).Manager
    if name == "Worker":
        return import_module(".feudal_network", __name__).Worker
    if name == "SkillSpec":
        return import_module(".skill_spec", __name__).SkillSpec
    if name == "generate_skill_specs":
        return import_module(".skill_spec", __name__).generate_skill_specs
    if name == "store_skill_specs":
        return import_module(".skill_spec", __name__).store_skill_specs
    if name == "ConfigurationError":
        return import_module(".exceptions", __name__).ConfigurationError
    raise AttributeError(name)


__all__ = [
    "RLAIFSystem",
    "PPOPolicyOptimizer",
    "MARLTrainer",
    "SkillDiscoveryModule",
    "SkillSpec",
    "generate_skill_specs",
    "store_skill_specs",
    "Manager",
    "Worker",
    "ConfigurationError",
]
