# TKUS-CE SIGN k=500 Study

This folder packages the completed study run `tkus-ce-sign-k500-20260310` together with analysis notes and hypervolume debugging outputs.

## Read This First

- [Run Summary](findings.md)
- [Hypervolume Debug](hypervolume-debug.md)
- [Reproduction Notes](reproduction.md)

## Bundled Artifacts

- `study-files/`
  - Full copied study output directory from `artifacts/optuna-monitor/tkus-ce-sign-k500-20260310`
- `debug/`
  - `hypervolume_debug.csv`
  - `hypervolume_debug_summary.json`

## Headline Result

- The study completed `36` trials and stopped on `hypervolume_plateau`.
- The final Pareto front spans roughly `1.004s` to `54.514s` runtime.
- Utility spans roughly `3221.284` to `12078.278` on the final Pareto set.
- The current hypervolume callback is buggy because it recomputes the reference point from the current Pareto front, which makes the reported hypervolume drop when the front improves.

## Fast Takeaways

- The search space is strongly bimodal on the SIGN smoke dataset even before moving to larger datasets.
- Some settings finish around `1-2s`, while others reach `171s` and `~1.2 GB` RSS.
- `rho=0.1` appears much more frequently on useful frontier points than `rho=0.5`.
- `pop_size=1000` can be valuable, but it also contains the most dangerous cost blowups.
