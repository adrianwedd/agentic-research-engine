#!/usr/bin/env bash

set -e

# Run a minimal smoke test
pytest tests/test_smoke.py -q "${@}"
