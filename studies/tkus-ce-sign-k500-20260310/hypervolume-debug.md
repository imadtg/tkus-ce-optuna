# Hypervolume Debug

This study exposed a real bug in the hypervolume callback in [`scripts/optuna_search.py`](/home/pc/Desktop/tkus-ce-optuna/scripts/optuna_search.py).

## Short Version

The current implementation computes the hypervolume reference point from the current Pareto front itself:

- `runtime_ref = max(front.runtime) * 1.05`
- `utility_ref = min(front.utility) * 0.95`

That is not stable.

When the Pareto front improves by removing:

- the slowest frontier point, the runtime reference shrinks
- the weakest-utility frontier point, the utility reference rises

Both changes can make the reported hypervolume drop even though the frontier became better.

## Evidence

The debug outputs are in:

- `debug/hypervolume_debug.csv`
- `debug/hypervolume_debug_summary.json`

The two regression trials are:

- Trial `28`
- Trial `33`

## Trial 28

Observed:

- Trial `28` added a new frontier point at `54.514s`, `12078.278`
- The current dynamic hypervolume dropped by `-7239.456`
- A fixed-reference hypervolume increased by `+189282.290`

Why:

- Trial `28` dominated the old slower frontier extreme
- That removed the previous worst runtime point from the front
- The dynamic runtime reference shrank from the old large box to `57.2397`
- The smaller box hid the true improvement

## Trial 33

Observed:

- Trial `33` added a new frontier point at `1.004s`, `3221.284`
- The current dynamic hypervolume dropped by `-4692.766`
- The fixed-reference hypervolume stayed flat

Why:

- Trial `33` dominated the previous lowest-utility frontier point
- That raised the dynamic utility floor to `3060.2198`
- The box height shrank, so the dynamic area decreased

## Underlying Bug

The issue is not mainly the 2D area integration.

The underlying bug is the changing reference point:

- the hypervolume callback recomputes the reference from the frontier being measured
- therefore the measurement scale itself changes across trials

That breaks the core assumption behind “plateau” detection.

## Consequence

The plateau stopper can still fire, but the metric it tracks is not reliable as a monotonic signal of Pareto improvement.

This study stopped with:

- `stop_reason = "hypervolume_plateau"`

But the plateau evidence is contaminated by the moving reference-point bug.

## Correct Direction

For a stable hypervolume signal, the study should use one fixed reference point for the entire run.

Reasonable options:

- derive it once from known search bounds
- derive it once from a short warmup budget and freeze it
- pass it explicitly as configuration

For this finished study, the fixed debug reference used was:

- `runtime_ref = 179.8272`
- `utility_ref = 885.560033371296`

That fixed-reference sequence does not show the false decreases seen in the current implementation.
