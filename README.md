# tkus-ce-optuna

Optuna search and benchmarking harness for TKUS-CE and similar sequence-mining runners.

This repo follows the DVC playground pattern: the algorithm source is treated as an imported dependency under `algorithms/` instead of being developed inline here.

## Layout

- `algorithms/tkus-ce/src.dvc`: imported TKUS-CE source dependency
- `algorithms/tkus-ce/dvc.yaml`: compile stage for the imported algorithm
- `scripts/optuna_search.py`: self-contained `uv` Optuna driver
- `scripts/run_optuna_search.sh`: thin launcher for the Optuna driver
- `studies/`: example study notes and commands
- `datasets/`: dataset manifests and local dataset conventions
- `artifacts/`: local study outputs, ignored by git

## Current status

This repo is wired to the pushed TKUS-CE GitHub repository:

- `https://github.com/imadtg/TKUS-CE.git`

If local TKUS-CE changes are required for telemetry or CLI flags, push those changes first and then update the DVC import revision.

## Bootstrap

1. Pull or update the imported TKUS-CE source.
2. Compile the runner with DVC.
3. Launch Optuna with the compiled runner jar.

Example:

```bash
dvc pull algorithms/tkus-ce/src.dvc

dvc repro algorithms/tkus-ce:compile

./scripts/run_optuna_search.sh \
  --study-name tkus-ce-smoke \
  --dataset /absolute/path/to/SIGN_sequence_utility.txt \
  --runner-jar algorithms/tkus-ce/runner/tkus-ce-fatjar.jar \
  --max-trials 20
```

## Notes

- `artifacts/` is intentionally untracked.
- The Optuna driver records per-trial files and study summaries locally.
- The driver expects output lines containing `#UTIL:` values.
