#!/usr/bin/env bash
set -e

# Minimal setup for Agentic Research Engine
python -m pip install --upgrade pip
pip install --no-cache-dir -r requirements.txt -c constraints.txt

echo "Minimal environment setup complete."
