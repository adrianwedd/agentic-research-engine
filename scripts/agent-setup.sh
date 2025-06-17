#!/usr/bin/env bash
# Light-weight setup script for local development.
set -euo pipefail

echo "[setup] installing Python dependencies..."
python -m pip install --upgrade pip > /dev/null
pip install -q torch==2.2.2+cpu --extra-index-url https://download.pytorch.org/whl/cpu
pip install -q -r requirements.txt -c constraints.txt

if ! command -v pre-commit >/dev/null; then
  echo "[setup] installing pre-commit..."
  pip install -q pre-commit==4.2.0
fi

echo "[setup] installing git hooks..."
pre-commit install

# Enable LangSmith tracing by default
export LANGCHAIN_TRACING_V2="${LANGCHAIN_TRACING_V2:-true}"
export LANGCHAIN_PROJECT="${LANGCHAIN_PROJECT:-agentic-research-engine}"

echo "[setup] done."
