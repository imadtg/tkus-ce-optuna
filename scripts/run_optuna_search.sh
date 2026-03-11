#!/usr/bin/env bash
set -euo pipefail

JBANG_DIR="${JBANG_DIR:-.cache/jbang}" uv run scripts/optuna_search.py "$@"
