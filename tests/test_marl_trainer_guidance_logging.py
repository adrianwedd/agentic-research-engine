import logging

from services.learning.marl_trainer import MARLTrainer


def test_guidance_loss_logging(caplog):
    cfg = {"guidance_loss": {"type": "cosine", "weight": 0.5}}
    dataset = {("obs", "act"): "hello"}
    trainer = MARLTrainer(cfg, dataset)
    batch = [
        {
            "observation": "obs",
            "action": "act",
            "message_vec": [0.1, 0.2],
            "policy_loss": 0.3,
        }
    ]
    with caplog.at_level(logging.INFO):
        trainer.train(batch)
    assert any(
        "policy_loss" in r.message and "guidance_loss" in r.message
        for r in caplog.records
    )
