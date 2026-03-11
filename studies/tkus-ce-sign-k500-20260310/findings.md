# Run Summary

Study:

- Name: `tkus-ce-sign-k500-20260310`
- Dataset: `SIGN_sequence_utility.txt`
- `k = 500`
- Completed trials: `36`
- Stop reason: `hypervolume_plateau`

## Aggregate Behavior

Across all completed trials:

- Runtime min/mean/max: `1.004 / 18.450 / 171.264`
- Utility min/mean/max: `932.168 / 6355.401 / 12078.278`
- RSS min/mean/max MB: `161.364 / 329.362 / 1203.666`
- Trials with runtime `<= 2s`: `9`
- Trials with runtime `>= 20s`: `9`
- Trials with RSS `>= 500 MB`: `2`

Interpretation:

- The full default search space is already broad enough to expose both cheap and pathological regions on the tiny SIGN dataset.
- This run is enough to justify hard safety rails before scaling to larger corpora.

## Final Pareto Frontier

Final Pareto points from `study-files/pareto_front.csv`:

- `1.004s`, `3221.284`
- `1.384s`, `4613.500356886228`
- `1.448s`, `4802.618126946108`
- `1.698s`, `5167.039614371258`
- `2.236s`, `6016.892`
- `2.564s`, `6195.454`
- `3.822s`, `6303.0468`
- `4.2s`, `7685.223106586825`
- `5.896s`, `8487.48836007984`
- `12.35s`, `10532.024885429142`
- `19.822s`, `10757.5536`
- `54.514s`, `12078.278`

## Most Useful Configurations

Fast-but-usable:

- Trial `24`: `1.384s`, `4613.500356886228`
- Trial `29`: `1.448s`, `4802.618126946108`
- Trial `26`: `1.698s`, `5167.039614371258`

Balanced:

- Trial `27`: `2.236s`, `6016.892`
- Trial `4`: `2.564s`, `6195.454`
- Trial `19`: `3.822s`, `6303.0468`
- Trial `25`: `4.2s`, `7685.223106586825`
- Trial `30`: `5.896s`, `8487.48836007984`

High-utility:

- Trial `31`: `12.35s`, `10532.024885429142`
- Trial `35`: `19.822s`, `10757.5536`
- Trial `28`: `54.514s`, `12078.278`

## Risk Points

The worst pathological points found in this run were:

- Trial `22`: `171.264s`, `10231.0948`, `1203.666 MB RSS`
- Trial `23`: `93.622s`, `6545.168167664671`, `1019.484 MB RSS`

These are especially important because:

- they are not dominated by tiny utility values,
- they are still plausible search-space draws,
- and they would become operationally expensive very quickly on larger datasets.

## Parameter Signals

Directional signals from the final frontier:

- `rho=0.1` appears more often than `rho=0.5`
- `pop_size=50` and `200` cover many good tradeoff points
- `pop_size=1000` still matters for the top utility tier, but also produces the harshest runtime and memory spikes
- `max_iterations=1000` is not always bad, but it is where the most dangerous combinations live

These are observations from a single study, not a stable conclusion yet.
