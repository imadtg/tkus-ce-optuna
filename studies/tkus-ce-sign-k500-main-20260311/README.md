# tkus-ce-sign-k500-main-20260311

Final analysis for the cleaned 100-trial SIGN / `k=500` study.

## Read First

- `study-files/study_summary.json`
- `study-files/trials.csv`
- `study-files/pareto_front.csv`
- `findings.md`
- `frontier-analysis.md`
- `defaults-recommendation.md`
- `hypervolume-notes.md`

## Core Outcome

- Completed trials: `100`
- Stop reason: none recorded
- The run ended on the configured trial budget, not on the hypervolume stopper.
- Dashboard: `http://127.0.0.1:8087`

## High-Level Shape

- Runtime min / mean / max: `0.63 / 20.30 / 248.86` seconds
- Average utility min / mean / max: `278.22 / 5667.41 / 12373.96`
- Peak RSS min / mean / max: `131.66 / 379.00 / 1891.83` MB

This search space stayed strongly bimodal:

- a fast regime around `0.6s` to `6s`
- a heavy regime extending past `45s` and up to `248.86s`

## Correlations

- Runtime vs utility:
  - Pearson: `0.065`
  - Spearman: `0.478`
- Runtime vs RSS:
  - Pearson: `0.967`
- RSS vs utility:
  - Pearson: `0.150`

Interpretation:

- Utility does rise with runtime in rank terms, but not linearly.
- Memory is almost entirely a runtime proxy in this study.
- Paying much more runtime does not reliably buy proportional utility.

## Pareto Front

Pareto front size: `20`

Useful frontier points:

- Fastest:
  - Trial `82`: `0.63s`, `1471.07`
  - Trial `46`: `0.662s`, `2075.48`
  - Trial `63`: `0.88s`, `3001.11`
- Best fast/mid tradeoff:
  - Trial `172`: `1.33s`, `5355.12`
  - Trial `97`: `1.858s`, `6083.61`
  - Trial `4`: `2.022s`, `6195.45`
  - Trial `179`: `2.258s`, `6930.06`
- Best upper-mid tradeoff:
  - Trial `177`: `6.082s`, `8664.47`
  - Trial `20`: `10.098s`, `9603.99`
  - Trial `3`: `10.412s`, `10012.92`
  - Trial `176`: `10.766s`, `11316.26`
- Best utility:
  - Trial `39`: `46.812s`, `12373.96`

Trial `176` is the standout practical point:

- `10.766s`
- `11316.26` utility
- much cheaper than Trial `39`
- only about `1058` utility below the global best

## Parameter Signals

### Strongest overall practical signal

`n_grams=1` was the most consistently useful setting:

- `30` total trials
- `11` Pareto-front trials
- Pareto enrichment: `1.83x`

`n_grams=5` was usually a bad bargain:

- `29` total trials
- only `1` Pareto-front trial
- Pareto enrichment: `0.17x`

### End confidence

`end_confidence=1.0` underperformed badly on the frontier:

- `44` total trials
- only `4` Pareto-front trials
- Pareto enrichment: `0.45x`

`end_confidence=0.9` and `0.5` were much healthier frontier settings.

### Alpha

`alpha=10.0` was clearly overrepresented on the frontier:

- `29` total trials
- `9` Pareto-front trials
- Pareto enrichment: `1.55x`

`alpha=1.0` mostly underperformed.

### Population size

`pop_size=1000` was expensive, but it was also overrepresented on the frontier:

- `29` total trials
- `9` Pareto-front trials
- Pareto enrichment: `1.55x`

That means large populations were often only worth it in the upper-utility regime.

### Iteration budget

`max_iterations=50` was the most frontier-efficient value:

- `37` total trials
- `10` Pareto-front trials
- Pareto enrichment: `1.35x`

`max_iterations=1000` improved the heavy end, but it was not broadly efficient.

## Practical Recommendations

If the goal is a balanced next-stage search on this dataset:

1. Anchor around `n_grams=1`
2. De-emphasize `n_grams=5`
3. Favor `end_confidence` in `{0.5, 0.9}` over `1.0`
4. Keep `alpha=10.0` in the search
5. Keep `pop_size=1000` only for the high-utility band
6. Bias toward `max_iterations=50` or `200` for efficient search

## Stopper Note

The hypervolume stopper did not fire here.

The final `study_summary.json` has no `stop_reason`, which means the run stopped because the trial budget was reached after cleanup and resumption, not because the Pareto front plateaued.

## Included Files

- `study-files/`
  - copied final study directory from `artifacts/optuna-monitor/tkus-ce-sign-k500-main-20260311`
- `findings.md`
  - ranked findings from the completed run
- `frontier-analysis.md`
  - full Pareto-front interpretation
- `defaults-recommendation.md`
  - conservative and aggressive default-setting guidance relative to current `TKUS-CE`
- `hypervolume-notes.md`
  - stopper notes and why this run did not stop on plateau
