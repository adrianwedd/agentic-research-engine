#!/usr/bin/env python3
"""Scrape repository data from GitHub."""
import argparse
import json

import requests

GITHUB_API = "https://api.github.com"


def search_repos(min_stars: int):
    """Return repositories with at least ``min_stars`` stars."""
    page = 1
    repos = []
    while True:
        resp = requests.get(
            f"{GITHUB_API}/search/repositories",
            params={
                "q": f"stars:>={min_stars}",
                "sort": "stars",
                "order": "desc",
                "per_page": 100,
                "page": page,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        repos.extend(data.get("items", []))
        if "next" not in resp.links:
            break
        page += 1
    return repos


def fetch_repo(full_name: str):
    """Return metadata for a single repository."""
    resp = requests.get(f"{GITHUB_API}/repos/{full_name}", timeout=10)
    resp.raise_for_status()
    return resp.json()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--min-stars", type=int, default=0)
    parser.add_argument("--output", required=True)
    parser.add_argument("--one-shot", action="store_true")
    parser.add_argument("--repos", nargs="*")
    args = parser.parse_args(argv)

    if args.repos:
        results = [fetch_repo(r) for r in args.repos]
    else:
        results = search_repos(args.min_stars)

    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
