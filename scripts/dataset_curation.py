import argparse
import datetime
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback if PyYAML missing
    yaml = None

REQUIRED_FIELDS = [
    "original_text",
    "erroneous_version",
    "critique",
    "corrected_version",
]


def load_config(path: Path) -> Dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix in {".yml", ".yaml"}:
        if yaml is None:
            raise RuntimeError("PyYAML required for YAML config parsing")
        return yaml.safe_load(text) or {}
    if path.suffix == ".json":
        return json.loads(text or "{}")
    return {}


def validate_records(
    records: List[Dict], required_fields: List[str] | None = None
) -> Tuple[List[Dict], List[Dict]]:
    required_fields = required_fields or REQUIRED_FIELDS
    valid: List[Dict] = []
    invalid: List[Dict] = []
    seen = set()
    for rec in records:
        errors = []
        if not isinstance(rec, dict):
            errors.append("record is not an object")
        else:
            for field in required_fields:
                if not rec.get(field):
                    errors.append(f"missing {field}")
            if (
                rec.get("erroneous_version")
                and rec.get("corrected_version")
                and rec.get("erroneous_version") == rec.get("corrected_version")
            ):
                errors.append("erroneous_version identical to corrected_version")
        rec_hash = json.dumps(rec, sort_keys=True)
        if rec_hash in seen:
            errors.append("duplicate record")
        else:
            seen.add(rec_hash)
        if errors:
            rec_copy = dict(rec)
            rec_copy["_errors"] = errors
            invalid.append(rec_copy)
        else:
            valid.append(rec)
    return valid, invalid


def save_version(records: List[Dict], out_dir: Path) -> str:
    version_id = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
    version_path = out_dir / version_id
    version_path.mkdir(parents=True, exist_ok=True)
    (version_path / "dataset.json").write_text(
        json.dumps(records, indent=2), encoding="utf-8"
    )
    return version_id


def sample_for_review(records: List[Dict], percent: float) -> List[Dict]:
    if not records:
        return []
    k = max(1, int(len(records) * percent / 100))
    return random.sample(records, k)


def interactive_review(records: List[Dict]) -> List[Dict]:
    results = []
    for rec in records:
        print("--- Review Record ---")
        print("Original:", rec.get("original_text"))
        print("Erroneous:", rec.get("erroneous_version"))
        print("Correction:", rec.get("corrected_version"))
        rating = input("Rate quality 1-5 (enter to skip): ").strip()
        if rating:
            results.append({"record": rec, "rating": int(rating)})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and curate dataset")
    parser.add_argument("dataset", type=Path, help="Path to dataset JSON file")
    parser.add_argument("--out-dir", type=Path, default=Path("data/curated"))
    parser.add_argument("--sample-percent", type=float, default=5.0)
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()

    config: Dict = {}
    if args.config:
        config = load_config(args.config)

    dataset_path = Path(config.get("dataset", args.dataset))
    out_dir = Path(config.get("out_dir", args.out_dir))
    sample_percent = float(config.get("sample_percent", args.sample_percent))
    required_fields = config.get("required_fields")

    data = json.loads(dataset_path.read_text(encoding="utf-8"))
    valid, invalid = validate_records(data, required_fields)
    version_id = save_version(valid, out_dir)
    invalid_path = out_dir / version_id / "invalid_records.json"
    if invalid:
        invalid_path.write_text(json.dumps(invalid, indent=2), encoding="utf-8")
        print(f"Flagged {len(invalid)} invalid records -> {invalid_path}")
    print(f"Saved {len(valid)} validated records under version {version_id}")

    sample = sample_for_review(valid, sample_percent)
    review = interactive_review(sample)
    if review:
        review_path = out_dir / version_id / "human_review.json"
        review_path.write_text(json.dumps(review, indent=2), encoding="utf-8")
        print(f"Stored human review results to {review_path}")


if __name__ == "__main__":
    main()
