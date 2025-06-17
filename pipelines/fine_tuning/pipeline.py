from __future__ import annotations

import concurrent.futures
from pathlib import Path
from typing import Dict, Mapping, Type

from pipelines.supervisor_policy import SupervisorPolicyTrainer


class MultiAgentFinetunePipeline:
    """Run fine-tuning jobs for multiple agents in parallel."""

    def __init__(
        self,
        dataset_map: Mapping[str, str | Path],
        reward_model_path: str | Path,
        model_name: str = "sshleifer/tiny-gpt2",
        out_root: str | Path = "models/agent_society",
        trainer_cls: Type[SupervisorPolicyTrainer] = SupervisorPolicyTrainer,
    ) -> None:
        self.dataset_map = {k: Path(v) for k, v in dataset_map.items()}
        self.reward_model_path = Path(reward_model_path)
        self.model_name = model_name
        self.out_root = Path(out_root)
        self.trainer_cls = trainer_cls

    def _run_job(self, agent_id: str, data_path: Path, epochs: int) -> Dict:
        out_dir = self.out_root / agent_id
        trainer = self.trainer_cls(
            data_path,
            self.reward_model_path,
            model_name=self.model_name,
            out_dir=out_dir,
        )
        return trainer.run(epochs=epochs)

    def run(self, epochs: int = 1, max_workers: int | None = None) -> Dict[str, Dict]:
        """Execute fine-tuning for all agents and return metrics per agent."""
        results: Dict[str, Dict] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as exe:
            futures = {
                exe.submit(self._run_job, aid, path, epochs): aid
                for aid, path in self.dataset_map.items()
            }
            for future in concurrent.futures.as_completed(futures):
                aid = futures[future]
                results[aid] = future.result()
        return results
