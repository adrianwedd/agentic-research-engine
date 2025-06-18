import argparse
import datetime
import json
from pathlib import Path

from scripts import train_evaluator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fine-tune the Evaluator on synthetic error/correction pairs"
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path("data/synthetic_self_correction/self_correction_dataset.json"),
    )
    parser.add_argument(
        "--model",
        default="hf-internal-testing/tiny-random-T5",
        help="Base model to fine-tune",
    )
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--version", default=None)
    parser.add_argument("--out-root", type=Path, default=Path("models/evaluator"))
    args = parser.parse_args()

    version = args.version or datetime.datetime.now(datetime.UTC).strftime(
        "finetuned-%Y%m%d_%H%M%S"
    )
    out_dir = args.out_root / version

    train_ds, eval_ds = train_evaluator.prepare_datasets(args.data_path)

    trainer = train_evaluator.train_model(
        train_ds, eval_ds, args.model, out_dir, args.epochs
    )
    finetuned_acc = train_evaluator.evaluate_model(trainer)

    metrics = {
        "finetuned_accuracy": finetuned_acc,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, indent=2)

    print(f"Saved model to {out_dir}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
