# RLAIFSystem: Reinforcement Learning with AI Feedback
"""Reinforcement learning loop that uses a Reward Model to refine agent policies."""

from __future__ import annotations

from typing import Dict, List


class RLAIFSystem:
    def __init__(self, reward_model, policy_optimizer):
        """Initialize reinforcement learning framework.

        Parameters
        ----------
        reward_model:
            Object with a ``score`` method returning a numeric reward for a
            trajectory dict.
        policy_optimizer:
            Object exposing an ``update`` method that consumes a trajectory and
            reward to update the policy parameters and returns the loss.
        """
        self.reward_model = reward_model
        self.policy_optimizer = policy_optimizer
        self.replay_buffer: List[Dict] = []
        self.metrics: Dict[str, float | int] = {"updates": 0}

    def update_agent_policies(self, experience_batch: List[Dict]) -> Dict[str, float]:
        """Update agent behaviors based on performance feedback.

        Policy update process:
        1. Experience quality assessment via ``reward_model``
        2. Reward signal computation
        3. Policy gradient calculation using ``policy_optimizer``
        4. Model parameter updates
        5. Performance metric aggregation
        """
        rewards: List[float] = []
        losses: List[float] = []

        for exp in experience_batch:
            reward = float(self.reward_model.score(exp))
            loss = float(self.policy_optimizer.update(exp, reward))
            self.replay_buffer.append(exp)
            rewards.append(reward)
            losses.append(loss)

        if rewards:
            avg_reward = sum(rewards) / len(rewards)
            avg_loss = sum(losses) / len(losses)
        else:
            avg_reward = 0.0
            avg_loss = 0.0

        self.metrics["updates"] += 1
        self.metrics["average_reward"] = avg_reward
        self.metrics["average_loss"] = avg_loss
        return {"average_reward": avg_reward, "average_loss": avg_loss}
