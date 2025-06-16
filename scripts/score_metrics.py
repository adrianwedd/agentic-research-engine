#!/usr/bin/env python3
"""Compute simple metrics for scraped repositories."""
import argparse
import json
import statistics
from typing import Dict, List


def compute_metrics(repos: List[Dict]) -> Dict[str, float]:
    stars = [r.get("stargazers_count", 0) for r in repos]
    forks = [r.get("forks_count", 0) for r in repos]
    return {
        "repo_count": len(repos),
        "avg_stars": statistics.mean(stars) if stars else 0.0,
        "avg_forks": statistics.mean(forks) if forks else 0.0,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--output")
    args = parser.parse_args(argv)

    with open(args.input_file) as f:
        repos = json.load(f)

    metrics = compute_metrics(repos)
    if args.output:
        with open(args.output, "w") as f:
            json.dump(metrics, f, indent=2)
    for k, v in metrics.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
