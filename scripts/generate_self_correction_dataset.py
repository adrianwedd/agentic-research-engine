import json
import random
from pathlib import Path

SOURCE_PATH = Path("data/golden_judge_dataset/golden_dataset.json")
OUT_PATH = Path("data/synthetic_self_correction/self_correction_dataset.json")


def inject_typos(text: str, rate: float = 0.1) -> str:
    words = text.split()
    for i in range(len(words)):
        if random.random() < rate and len(words[i]) > 3:
            chars = list(words[i])
            j = random.randrange(len(chars) - 1)
            chars[j], chars[j + 1] = chars[j + 1], chars[j]
            words[i] = "".join(chars)
    return " ".join(words)


def critique(original: str, erroneous: str) -> str:
    issues = []
    for o, e in zip(original.split(), erroneous.split()):
        if o != e:
            issues.append(f"'{e}' should be '{o}'")
    if not issues:
        return "No issues detected"
    return "Typographical errors: " + "; ".join(issues)


def generate_examples() -> list[dict]:
    src = json.loads(SOURCE_PATH.read_text())
    reports = [entry["report"] for entry in src]
    examples = []
    for text in reports:
        for _ in range(50):
            erroneous = inject_typos(text)
            examples.append(
                {
                    "original_text": text,
                    "erroneous_version": erroneous,
                    "critique": critique(text, erroneous),
                    "corrected_version": text,
                }
            )
    return examples


def main() -> None:
    examples = generate_examples()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(examples, indent=2))
    print(f"Wrote {OUT_PATH} with {len(examples)} examples")


if __name__ == "__main__":
    main()
