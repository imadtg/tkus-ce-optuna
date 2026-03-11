# Frontier Analysis

The final Pareto front has `20` points.

## Full Frontier

- Trial `82`: `0.63s`, `1471.07`
- Trial `46`: `0.662s`, `2075.48`
- Trial `63`: `0.88s`, `3001.11`
- Trial `33`: `1.146s`, `3221.28`
- Trial `40`: `1.196s`, `3553.07`
- Trial `172`: `1.33s`, `5355.12`
- Trial `97`: `1.858s`, `6083.61`
- Trial `4`: `2.022s`, `6195.45`
- Trial `38`: `2.072s`, `6438.48`
- Trial `179`: `2.258s`, `6930.06`
- Trial `93`: `3.52s`, `7609.04`
- Trial `62`: `3.672s`, `7693.55`
- Trial `10`: `4.358s`, `7933.92`
- Trial `41`: `5.336s`, `8572.20`
- Trial `177`: `6.082s`, `8664.47`
- Trial `20`: `10.098s`, `9603.99`
- Trial `3`: `10.412s`, `10012.92`
- Trial `176`: `10.766s`, `11316.26`
- Trial `0`: `45.644s`, `11868.23`
- Trial `39`: `46.812s`, `12373.96`

## Regimes

### Ultra-fast

Trials `82`, `46`, `63`, `33`, `40`

- `0.63s` to `1.20s`
- utility `1471` to `3553`

Good for smoke-health checks, not for serious quality.

### Fast efficient

Trials `172`, `97`, `4`, `38`, `179`

- `1.33s` to `2.26s`
- utility `5355` to `6930`

This is the strongest value-per-second region in the whole study.

### Middle

Trials `93`, `62`, `10`, `41`, `177`

- `3.52s` to `6.08s`
- utility `7609` to `8664`

Returns are still good, but visibly flattening.

### Upper-middle

Trials `20`, `3`, `176`

- `10.10s` to `10.77s`
- utility `9604` to `11316`

This is the practical sweet spot for “serious quality without absurd cost.”

### Heavy tail

Trials `0`, `39`

- `45.64s` to `46.81s`
- utility `11868` to `12374`

Still Pareto-optimal, but weak on marginal returns.

## Key Knee Points

- Trial `172`: first strong jump into meaningful quality at low cost
- Trial `179`: last clearly cheap frontier point before the middle band
- Trial `176`: practical champion before diminishing returns become severe
