#!/usr/bin/env bash
set -euo pipefail

UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache}" JBANG_DIR="${JBANG_DIR:-.cache/jbang}" uv run scripts/optuna_search.py "$@"
