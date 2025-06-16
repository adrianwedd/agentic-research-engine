import argparse
import datetime
from pathlib import Path

from pipelines.reward_model import RewardModelTrainer


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Reward Model")
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--out-root", type=Path, default=Path("models/reward_model"))
    parser.add_argument("--version", default=None)
    args = parser.parse_args()

    version = args.version or datetime.datetime.now(datetime.UTC).strftime(
        "reward-%Y%m%d_%H%M%S"
    )
    out_dir = args.out_root / version

    trainer = RewardModelTrainer(args.data_path, out_dir)
    mse = trainer.run()
    print(f"Saved model to {out_dir}")
    print(f"Eval MSE: {mse:.3f}")


if __name__ == "__main__":
    main()
