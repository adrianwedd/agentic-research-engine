import argparse
import datetime
import json
from pathlib import Path
from typing import Tuple

from datasets import Dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)


def load_dataset(path: Path) -> list:
    """Load synthetic error/correction pairs from ``path``."""
    text = path.read_text(encoding="utf-8")
    return json.loads(text)


def prepare_datasets(path: Path, test_split: float = 0.1) -> Tuple[Dataset, Dataset]:
    """Return train and evaluation ``Dataset`` objects."""
    records = load_dataset(path)
    data = [
        {"input": r["erroneous_version"], "label": r["corrected_version"]}
        for r in records
    ]
    ds = Dataset.from_list(data)
    splits = ds.train_test_split(test_size=test_split, seed=42)
    return splits["train"], splits["test"]


def build_trainer(
    train_ds: Dataset,
    eval_ds: Dataset,
    model_name: str,
    out_dir: Path,
    epochs: int = 3,
) -> Seq2SeqTrainer:
    """Return a ``Seq2SeqTrainer`` instance for ``model_name``."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    def preprocess(batch):
        inputs = tokenizer(batch["input"], truncation=True)
        with tokenizer.as_target_tokenizer():
            labels = tokenizer(batch["label"], truncation=True)
        inputs["labels"] = labels["input_ids"]
        return inputs

    tokenized_train = train_ds.map(
        preprocess,
        batched=True,
        remove_columns=train_ds.column_names,
    )
    tokenized_eval = eval_ds.map(
        preprocess,
        batched=True,
        remove_columns=eval_ds.column_names,
    )
    collator = DataCollatorForSeq2Seq(tokenizer, model=model)
    args = Seq2SeqTrainingArguments(
        output_dir=str(out_dir),
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        num_train_epochs=epochs,
        evaluation_strategy="epoch",
        save_total_limit=1,
        logging_steps=10,
    )
    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        data_collator=collator,
        tokenizer=tokenizer,
    )
    return trainer


def train_model(
    train_ds: Dataset,
    eval_ds: Dataset,
    model_name: str,
    out_dir: Path,
    epochs: int = 3,
) -> Seq2SeqTrainer:
    """Fine-tune ``model_name`` on the provided dataset."""
    trainer = build_trainer(train_ds, eval_ds, model_name, out_dir, epochs)
    trainer.train()
    out_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(out_dir)
    trainer.tokenizer.save_pretrained(out_dir)
    return trainer


def evaluate_model(trainer: Seq2SeqTrainer, eval_ds: Dataset | None = None) -> float:
    """Return exact-match accuracy on ``eval_ds`` or the trainer's eval dataset."""
    if eval_ds is None:
        eval_ds = trainer.eval_dataset
    tokenizer = trainer.tokenizer
    preds = trainer.predict(eval_ds).predictions
    decoded = tokenizer.batch_decode(preds, skip_special_tokens=True)
    labels = [ex["label"] for ex in eval_ds]
    correct = sum(p.strip() == l.strip() for p, l in zip(decoded, labels))
    return correct / len(labels)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fine-tune Evaluator model")
    parser.add_argument(
        "--data-path",
        type=Path,
        default=Path("data/synthetic_self_correction/self_correction_dataset.json"),
    )
    parser.add_argument("--model", default="google/flan-t5-small")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--version", default=None)
    parser.add_argument("--test-split", type=float, default=0.1)
    parser.add_argument(
        "--out-root",
        type=Path,
        default=Path("models/evaluator_finetuned"),
        help="Directory to store fine-tuned model artifacts",
    )
    args = parser.parse_args()

    version = (
        args.version
        or f"evaluator-{datetime.datetime.now(datetime.UTC).strftime('%Y%m%d')}"
    )
    out_dir = args.out_root / version

    train_ds, eval_ds = prepare_datasets(args.data_path, args.test_split)

    # evaluate baseline model before fine-tuning
    baseline_trainer = build_trainer(
        train_ds, eval_ds, args.model, out_dir, args.epochs
    )
    baseline_acc = evaluate_model(baseline_trainer, eval_ds)

    # fine-tune and evaluate
    trainer = train_model(train_ds, eval_ds, args.model, out_dir, args.epochs)
    finetuned_acc = evaluate_model(trainer, eval_ds)

    metrics = {
        "baseline_model_accuracy": baseline_acc,
        "finetuned_model_accuracy": finetuned_acc,
    }
    metrics_file = out_dir / "metrics.json"
    metrics_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Saved model to {out_dir}")
    print(f"Baseline accuracy: {baseline_acc:.3f}")
    print(f"Finetuned accuracy: {finetuned_acc:.3f}")
    if finetuned_acc > baseline_acc:
        print("Fine-tuned model improved over baseline")
    else:
        print("Fine-tuned model did not improve over baseline")


if __name__ == "__main__":
    main()
