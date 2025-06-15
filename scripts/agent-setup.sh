#!/usr/bin/env bash
set -e

# Install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
