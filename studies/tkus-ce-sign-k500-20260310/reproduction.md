# Reproduction Notes

## Study Command

The completed study was launched with:

```bash
./scripts/run_optuna_search.sh \
  --study-name tkus-ce-sign-k500-20260310 \
  --artifacts-dir artifacts/optuna-monitor \
  --dataset /home/pc/Desktop/TKUS-CE/testdata/smoke/SIGN_sequence_utility.txt \
  --runner-jar /tmp/tkus-ce-optuna-smoke.jar \
  --k 500 \
  --max-trials 100
```

## Runner Build

The runner JAR was built from the sibling `TKUS-CE` repo with:

```bash
/home/pc/Desktop/TKUS-CE/scripts/build-fatjar.sh /tmp/tkus-ce-optuna-smoke.jar
```

## Hypervolume Debug Command

```bash
uv run scripts/debug_hypervolume.py \
  --study-sqlite artifacts/optuna-monitor/tkus-ce-sign-k500-20260310/study.sqlite3 \
  --output-dir studies/tkus-ce-sign-k500-20260310/debug
```

## Packaged Study Files

The copied study directory lives at:

- `studies/tkus-ce-sign-k500-20260310/study-files/`

That copy includes:

- `study.sqlite3`
- `study_summary.json`
- `trials.csv`
- `pareto_front.csv`
- `pareto_scatter.png`
- `hypervolume_history.png`
- all per-trial subdirectories under `trials/`
