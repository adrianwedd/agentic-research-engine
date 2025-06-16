import json
import random
from pathlib import Path

from googletrans import Translator

translator = Translator()

SAMPLES = [
    (
        "Long-Term Memory Consolidation & Forgetting Research (P2-19A)"
        "\n\nThis document summarizes a research spike into lifecycle management"
        " algorithms for the Long-Term Memory (LTM) service. The goal was to"
        " compare advanced forgetting strategies and recommend an approach for"
        " Phase 2 implementation."
    ),
    (
        "Graph Compilation Strategies Research"
        "\n\nA short research spike evaluated dynamic graph execution versus"
        " ahead-of-time compilation for the orchestration engine."
    ),
]


def back_translate(text: str, lang: str = "ru") -> str:
    inter = translator.translate(text, dest=lang).text
    back = translator.translate(inter, src=lang, dest="en").text
    return back


def inject_typos(text: str, rate: float = 0.1) -> str:
    words = text.split()
    for i in range(len(words)):
        if random.random() < rate:
            word = words[i]
            if len(word) > 3:
                # swap two characters to create a typo
                chars = list(word)
                j = random.randrange(len(chars) - 1)
                chars[j], chars[j + 1] = chars[j + 1], chars[j]
                words[i] = "".join(chars)
    return " ".join(words)


def main():
    data = []
    for text in SAMPLES:
        bt = back_translate(text)
        typo = inject_typos(text)
        data.append(
            {
                "original": text,
                "back_translation": bt,
                "typo_perturbation": typo,
            }
        )
    out_path = Path("data/synthetic_self_correction/sample_pairs.json")
    out_path.write_text(json.dumps(data, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
