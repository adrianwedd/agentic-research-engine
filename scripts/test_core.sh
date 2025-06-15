#!/usr/bin/env bash
set -e

pytest -m "core" "$@"
