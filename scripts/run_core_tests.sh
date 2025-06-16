#!/usr/bin/env bash
set -e

# Run the core test suite in parallel with coverage
pytest -m "core" --cov=./ --cov-report=xml --cov-report=html --cov-fail-under=80 -v "${@}"
