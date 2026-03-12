# Profile Findings

This document summarizes the full JFR profile pass over all `20` Pareto-front configurations from the `SIGN` / `k=500` study, using seed `11`.

Source methods referenced below:

- [`NGramModel.sampleItemset`](/home/pc/Desktop/TKUS-CE/src/NGramModel.java:108)
- [`NGramModel.getContextItems`](/home/pc/Desktop/TKUS-CE/src/NGramModel.java:170)
- [`NGramModel.getItemProbability`](/home/pc/Desktop/TKUS-CE/src/NGramModel.java:191)
- [`Particle.computeExtensionFromParent`](/home/pc/Desktop/TKUS-CE/src/Particle.java:208)
- [`Particle.matchItemset`](/home/pc/Desktop/TKUS-CE/src/Particle.java:261)
- [`AlgoTKUSCE.samplePopulation`](/home/pc/Desktop/TKUS-CE/src/AlgoTKUSCE.java:374)
- [`AlgoTKUSCE.insertTopList`](/home/pc/Desktop/TKUS-CE/src/AlgoTKUSCE.java:505)

## Core hotspot picture

Across the whole Pareto frontier, the hottest self-sampled functions were:

- `NGramModel.sampleItemset`: `6428` samples
- `java.util.HashMap.getNode`: `3789`
- `java.util.HashMap$HashIterator.nextNode`: `2685`
- `java.util.BitSet.nextSetBit`: `2644`
- `NGramModel.getContextItems`: `2464`
- `NGramModel.getItemProbability`: `1777`
- `java.util.HashMap$HashIterator.<init>`: `1171`
- `Particle.matchItemset`: `548`
- `Particle.computeExtensionFromParent`: `494`

That means the main scaling bottleneck is not the retained-top-k bookkeeping. It is the model sampling path plus the hash-heavy context/probability machinery around it.

## What changes as runs get heavier

### Fast frontier points (`<= 2.5s`)

Fast runs still show extension work prominently:

- `Particle.computeExtensionFromParent`
- `Particle.matchItemset`
- `BitSet.nextSetBit`

These matter at the low end because the model has not yet become overwhelmingly expensive.

### Mid frontier points (`2.5s` to `12s`)

The center of gravity shifts toward:

- `NGramModel.sampleItemset`
- `BitSet.nextSetBit`
- `HashMap` iteration/lookups
- `NGramModel.getItemProbability`
- `NGramModel.getContextItems`

This is the first regime where repeated sampling and context feature lookups dominate clearly.

### Heavy frontier points (`> 12s`)

The heavy end is where the real pain is:

- `NGramModel.sampleItemset`: mean self-share `24.83%`
- `HashMap.getNode`: `20.79%`
- `NGramModel.getContextItems`: `12.88%`
- `HashMap$HashIterator.nextNode`: `10.75%`
- `BitSet.nextSetBit`: `8.10%`
- `NGramModel.getItemProbability`: `8.06%`

This is a very clear signal:

- the heavy regime is driven primarily by repeated hash lookups and set reconstruction in the model path
- not by frontier insertion, sorting, or top-k retention

## Trial-shape comparison

### Trial 82 (`0.630s`, `1471.07`)

The fastest frontier point is still mixed:

- `BitSet.nextSetBit`: `11.11%`
- `Particle.computeExtensionFromParent`: `9.88%`
- `NGramModel.sampleItemset`: `6.17%`
- `NGramModel.getContextItems`: `6.17%`

At the low end, extension mechanics still compete with model sampling.

### Trial 176 (`10.766s`, `11316.26`)

The practical champion is already model-heavy:

- `NGramModel.sampleItemset`: `20.26%`
- `BitSet.nextSetBit`: `17.33%`
- `HashMap$HashIterator.nextNode`: `13.35%`
- `NGramModel.getItemProbability`: `8.69%`
- `NGramModel.getContextItems`: `8.50%`
- `Integer.equals`: `7.39%`

Trial `176` is the right picture of the useful serious regime: the model path dominates, and hash/iteration overhead is already substantial.

### Trial 39 (`46.812s`, `12373.96`)

The global utility winner is even more dominated by hash/context work:

- `NGramModel.sampleItemset`: `23.91%`
- `HashMap.getNode`: `19.54%`
- `NGramModel.getContextItems`: `12.63%`
- `HashMap$HashIterator.nextNode`: `12.07%`
- `NGramModel.getItemProbability`: `8.32%`

Compared with Trial `176`, the heavy tail spends much more of its time in lookups and context reconstruction rather than buying utility through fundamentally different useful work.

## Correlation read

Among the top hotspot functions:

- `NGramModel.getContextItems` had the strongest runtime correlation: `0.680`
- `HashMap.getNode` also correlated strongly with runtime: `0.590`
- `NGramModel.getItemProbability` was moderately runtime-correlated: `0.441`
- `Particle.computeExtensionFromParent` was negatively runtime-correlated: `-0.610`

Interpretation:

- the longer runs are not “more extension-heavy”
- they are “more model-lookup-heavy”
- extension work is relatively more important in fast frontier points than in the heavy utility-maximizing tail

## What needs attention first

### 1. Stop rebuilding context features as a fresh hashed set

`NGramModel.getContextItems` is hot both directly and indirectly via `sampleItemset` and `getItemProbability`.

Likely direction:

- cache a compact context representation on the particle or model side
- avoid allocating a fresh `HashSet<Integer>` for each sampled itemset
- consider a dense boolean/bitset/indexed representation keyed by considered-item index

### 2. Reduce `HashMap` churn in the probability path

The heavy regime is saturated with:

- `HashMap.getNode`
- `HashMap$HashIterator.nextNode`
- `HashMap$HashIterator.<init>`
- `Integer.equals`

Likely direction:

- replace nested boxed `HashMap<Integer, Integer>` structures with indexed arrays or primitive maps where feasible
- especially for feature counts keyed by considered item ids

### 3. Rework `sampleItemset` / `getItemProbability` together

`sampleItemset` dominates every runtime band. It currently:

- rebuilds context features
- loops all active items
- calls `getItemProbability` for each one
- each probability call performs more hash lookups and log-odds math

Likely direction:

- compute context-derived terms once per sampled itemset instead of per candidate item
- pre-index item stats by active-item position, not boxed item id

### 4. Treat extension-path optimization as secondary for the heavy regime

`Particle.computeExtensionFromParent` and `Particle.matchItemset` matter, especially on the fast frontier, but they are not what drives the expensive upper-utility tail.

That means:

- optimizing them can still improve cheap and midrange runs
- but they are not the first place to attack if the goal is to cut the heavy frontier cost

## Files

- [profile README](/home/pc/Desktop/tkus-ce-optuna/studies/tkus-ce-sign-k500-main-20260311/pareto-profile-seed-11/README.md)
- [profile analysis](/home/pc/Desktop/tkus-ce-optuna/studies/tkus-ce-sign-k500-main-20260311/pareto-profile-seed-11/analysis.md)
- [profile summary json](/home/pc/Desktop/tkus-ce-optuna/studies/tkus-ce-sign-k500-main-20260311/pareto-profile-seed-11/profile_summary.json)
- [profile hotspots csv](/home/pc/Desktop/tkus-ce-optuna/studies/tkus-ce-sign-k500-main-20260311/pareto-profile-seed-11/profile_hotspots_by_trial.csv)
