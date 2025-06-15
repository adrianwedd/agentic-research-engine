#!/usr/bin/env bash
set -e

# Install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install

# Enable LangSmith tracing by default
export LANGCHAIN_TRACING_V2="${LANGCHAIN_TRACING_V2:-true}"
export LANGCHAIN_PROJECT="${LANGCHAIN_PROJECT:-agentic-research-engine}"
