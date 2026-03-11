# Defaults Recommendation

## Current sibling defaults

From `TKUS-CE`:

- `params.yaml` currently sets:
  - `n=5`
  - `model-confidence=0.9`
  - `end-confidence=0.5`
  - `end-prob-prior=0.5`
  - `alpha=1.0`
  - `pop-size=10`
  - `max-iterations=1`
- code fallback defaults in `Main.java` are:
  - `n=5`
  - `model-confidence=0.9`
  - `end-confidence=0.5`
  - `end-prob-prior=0.5`
  - `alpha=1.0`
  - `rho=0.2`
  - `pop-size=200`
  - `max-iterations=200`

## Conservative recommendation

This is the lowest-risk update path from the current sibling defaults:

- `n: 5 -> 1`
- keep `model-confidence=0.9`
- keep `end-confidence=0.5`
- keep `end-prob-prior=0.5`
- keep `alpha=1.0`
- keep `rho=0.2`
- `pop-size: 10 -> 200`
- `max-iterations: 1 -> 200`

Rationale:

- `n=1` is the strongest signal in the whole study
- `200/200` already matches the code fallback defaults
- this avoids jumping immediately to the expensive `1000`-population regime

## Aggressive recommendation

If defaults are intended to favor quality over cheapness:

- `n=1`
- `model-confidence=0.5`
- `end-confidence=0.5`
- `end-prob-prior=0.5`
- `alpha=0.1`
- `rho=0.1`
- `pop-size=1000`
- `max-iterations=200`

This is inspired by Trial `176`, but it should not be treated as fully settled. The local neighborhood around Trial `176` does not isolate all hyperparameters one at a time.

## What not to do from this study alone

- Do not keep `n=5` just because it is the current default.
- Do not jump to `rho=0.5` as a default.
- Do not treat `1000 x 1000` as a sensible everyday default regime.
