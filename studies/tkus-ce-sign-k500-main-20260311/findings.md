# Findings

## 1. The practical best point is not the absolute best point

Trial `176` is the best practical tradeoff discovered in this run:

- runtime: `10.766s`
- average utility: `11316.2558`

The absolute best utility point is Trial `39`:

- runtime: `46.812s`
- average utility: `12373.958`

That only buys about `1058` extra utility for roughly `4.3x` the runtime.

## 2. `n_grams=1` is the clearest default-change candidate

`n_grams=1` was the most overrepresented setting on the Pareto front and consistently outperformed the current `TKUS-CE` config default of `n=5`.

## 3. The space is bimodal

The run separated cleanly into:

- a cheap band around `0.6s` to `6s`
- a heavy band past `10s`, with extreme cases above `45s`

The heavy band is real, but much of it has poor marginal returns.

## 4. Runtime and memory are tightly linked

Peak RSS tracked runtime very closely in this run.

- Pearson(runtime, RSS): `0.967`

That makes runtime a decent shorthand for memory risk on this dataset.

## 5. The stopper did not trigger here

The hypervolume stopper did not end the run. The study finished on the configured completed-trial budget after cleanup and resumption.
