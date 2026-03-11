#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "Usage: $0 STUDY_SQLITE [ARTIFACT_DIR]" >&2
  exit 1
fi

study_sqlite="$1"
artifact_dir="${2:-artifacts/optuna-monitor/_dashboard_artifacts}"

uv run optuna-dashboard "sqlite:///$study_sqlite" --artifact-dir "$artifact_dir" --host 127.0.0.1 --port 8087
