#!/usr/bin/env bash
set -euo pipefail

# Setup development environment

echo "[dev setup] Installing Python dependencies..."
python -m pip install --upgrade pip >/dev/null
pip install -q -r requirements.txt -c constraints.txt
pip install -q tenacity

if ! command -v pre-commit >/dev/null; then
  echo "[dev setup] Installing pre-commit..."
  pip install -q pre-commit==4.2.0
fi

echo "[dev setup] Installing git hooks..."
pre-commit install

echo "[dev setup] Done."
