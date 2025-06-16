#!/usr/bin/env bash
set -euo pipefail

# Run the lightweight core test suite and fail fast on first error
pytest -m "core" --maxfail=1 -vv "$@"
