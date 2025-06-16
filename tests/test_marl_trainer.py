import pytest

from services.learning.exceptions import ConfigurationError
from services.learning.marl_trainer import MARLTrainer


def test_marl_trainer_requires_guidance_loss():
    with pytest.raises(ConfigurationError):
        MARLTrainer({})

    cfg = {"guidance_loss": {"type": "cosine", "weight": 0.5}}
    trainer = MARLTrainer(cfg)
    assert trainer.guidance_loss_cfg["type"] == "cosine"
