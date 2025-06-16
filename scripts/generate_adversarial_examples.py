import json
import random
from pathlib import Path

CATEGORIES = [
    "percentage_misinterpretation",
    "date_confusion",
    "unit_swap",
    "logical_fallacy",
    "historical_year_error",
]


def percentage_examples(n: int) -> list[dict]:
    base = [5, 10, 20, 25, 30, 40, 60, 75, 80, 90]
    examples = []
    for _ in range(n):
        correct = random.choice(base)
        mis = (correct + random.randint(1, 9)) % 100
        examples.append(
            {
                "category": "percentage_misinterpretation",
                "prompt": f"The success rate was {correct}%.",
                "flawed_output": f"The success rate was {mis}%.",
                "critique": f"The correct percentage is {correct}%, not {mis}%.",
            }
        )
    return examples


def date_examples(n: int) -> list[dict]:
    dates = [
        ("03/06/2022", "06/03/2022"),
        ("12/05/2021", "05/12/2021"),
        ("01/04/2020", "04/01/2020"),
        ("07/08/2019", "08/07/2019"),
        ("11/02/2018", "02/11/2018"),
    ]
    examples = []
    for _ in range(n):
        correct, wrong = random.choice(dates)
        examples.append(
            {
                "category": "date_confusion",
                "prompt": f"The event occurred on {correct}.",
                "flawed_output": f"The event occurred on {wrong}.",
                "critique": f"The date {wrong} misinterprets the format; it should be {correct}.",
            }
        )
    return examples


def unit_examples(n: int) -> list[dict]:
    pairs = [
        ("10 meters", "10 feet"),
        ("5 kilograms", "5 pounds"),
        ("20 kilometers", "20 miles"),
        ("100 Celsius", "100 Fahrenheit"),
        ("2 liters", "2 gallons"),
    ]
    examples = []
    for _ in range(n):
        metric, imperial = random.choice(pairs)
        examples.append(
            {
                "category": "unit_swap",
                "prompt": f"The measurement was {metric}.",
                "flawed_output": f"The measurement was {imperial}.",
                "critique": f"Confuses units: the correct value is {metric}.",
            }
        )
    return examples


def fallacy_examples(n: int) -> list[dict]:
    statements = [
        ("If it rains, the ground gets wet.", "The ground is wet, so it rained."),
        ("All birds can fly.", "Penguins are birds, so penguins can fly."),
        (
            "If the alarm is set, the door locks.",
            "The door is locked, so the alarm is set.",
        ),
        (
            "If I study, I'll pass the exam.",
            "I passed the exam, so I must have studied.",
        ),
        ("All cats are mammals.", "Fido is a mammal, therefore Fido is a cat."),
    ]
    examples = []
    for _ in range(n):
        premise, wrong = random.choice(statements)
        examples.append(
            {
                "category": "logical_fallacy",
                "prompt": premise,
                "flawed_output": wrong,
                "critique": "The conclusion does not logically follow from the premise.",
            }
        )
    return examples


def year_examples(n: int) -> list[dict]:
    facts = [
        ("The moon landing happened in 1969.", "The moon landing happened in 1996."),
        ("The Berlin Wall fell in 1989.", "The Berlin Wall fell in 1998."),
        (
            "The Declaration of Independence was signed in 1776.",
            "The Declaration of Independence was signed in 1767.",
        ),
        ("World War II ended in 1945.", "World War II ended in 1954."),
        ("The first iPhone launched in 2007.", "The first iPhone launched in 2017."),
    ]
    examples = []
    for _ in range(n):
        correct, wrong = random.choice(facts)
        examples.append(
            {
                "category": "historical_year_error",
                "prompt": correct,
                "flawed_output": wrong,
                "critique": "Incorrect year stated.",
            }
        )
    return examples


def generate_dataset(count_per_category: int = 10) -> list[dict]:
    random.seed(42)
    data = []
    data.extend(percentage_examples(count_per_category))
    data.extend(date_examples(count_per_category))
    data.extend(unit_examples(count_per_category))
    data.extend(fallacy_examples(count_per_category))
    data.extend(year_examples(count_per_category))
    random.shuffle(data)
    return data


def main() -> None:
    dataset = generate_dataset()
    out_path = Path("data/adversarial_examples/edge_cases.json")
    out_path.write_text(json.dumps(dataset, indent=2))
    print(f"Wrote {out_path} with {len(dataset)} records")


if __name__ == "__main__":
    main()
