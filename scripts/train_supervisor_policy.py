import argparse
from pathlib import Path

from pipelines.supervisor_policy import SupervisorPolicyTrainer


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Supervisor policy via RLAIF")
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--reward-model", type=Path, required=True)
    parser.add_argument("--model", default="sshleifer/tiny-gpt2")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument(
        "--out-dir", type=Path, default=Path("models/supervisor_policy")
    )
    args = parser.parse_args()

    trainer = SupervisorPolicyTrainer(
        args.data_path, args.reward_model, args.model, args.out_dir
    )
    metrics = trainer.run(epochs=args.epochs)
    print(f"Saved policy to {args.out_dir / 'policy'}")
    print(f"Avg reward: {metrics.get('average_reward', 0):.3f}")


if __name__ == "__main__":
    main()
