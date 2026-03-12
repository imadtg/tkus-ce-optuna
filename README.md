# tkus-ce-optuna

Optuna search and benchmarking harness for TKUS-CE and similar sequence-mining runners.

This repo now consumes released `TKUS-CE` runner jars by default instead of rebuilding from imported source for every study.

## Layout

- `scripts/fetch_tkus_ce_release.py`: resolves `latest` or an exact `TKUS-CE` version from GitHub Releases
- `pyproject.toml` / `uv.lock`: pinned Python environment for the harness
- `scripts/optuna_search.py`: Optuna driver executed from the project `uv` environment
- `scripts/run_optuna_search.sh`: thin launcher for the Optuna driver
- `studies/`: example study notes and commands
- `datasets/`: dataset manifests and local dataset conventions
- `artifacts/`: local study outputs, ignored by git

## Current status

This repo resolves runners from the published `TKUS-CE` GitHub releases:

- `https://github.com/imadtg/TKUS-CE.git`

Use `--runner-release latest` for the latest semver release or `--runner-release <x.y.z>` for an exact version. Every study records the resolved tag and commit SHA in `runner/resolution.json` and `study_summary.json`.

## Bootstrap

1. Sync the Python environment with `uv`.
2. Launch Optuna with a released runner.

Example:

```bash
uv sync

./scripts/run_optuna_search.sh \
  --study-name tkus-ce-smoke \
  --dataset /absolute/path/to/SIGN_sequence_utility.txt \
  --runner-release latest \
  --max-trials 20
```

## Notes

- `artifacts/` is intentionally untracked.
- The Optuna driver records per-trial files and study summaries locally.
- Study summaries now include the resolved runner tag and exact commit SHA.
- Python dependencies are no longer resolved from inline script metadata; use `uv sync` to materialize the pinned project environment.
- The driver expects output lines containing `#UTIL:` values.
