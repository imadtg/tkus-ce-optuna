# Backlog

## 1. Fix average-utility metric at the source (`TKUS-CE`)

The convergence plot metric labeled as average utility must represent:

- the average utility of the best `k` found so far

This means it should be monotone non-decreasing over time.

If the emitted metric is not monotone, that is a source bug in the sibling `TKUS-CE` repo and must be corrected there. After fixing it:

- publish a new artifact / release of `TKUS-CE`
- then update this harness to consume that corrected build

Context:

- this has not been fully closed out yet because the clean jar packaging/release path is not finalized
- the GitHub CI workflows for jar publishing have not yet been pushed to remote

## 2. Finish the jar packaging / release flow for `TKUS-CE`

We do not yet have the final clean artifact-consumption path for sourcing the runner jar here.

Additional constraints noted by the user:

- do not use the self-hosted runner yet
- for now, prefer a more granular / manual release flow

This means the release design should support:

- manual releases first
- easy verification before automating anything
- later transition to cleaner artifact sourcing in this repo

## 3. Iteration-speed visualization needs design work

The user wants plot coordinates to visually expand or compress based on how fast iterations are processed, similar in spirit to how log plots distort the grid.

Current interpretation:

- faster processing should visually compress one region of the x-axis less, and slower processing should visually stretch it more
- the goal is to make iteration pace visible directly in the coordinate geometry, not only in a separate secondary series

This still needs further clarification and design work before implementation.

## 4. Stopper confidence still needs one clean plateau-stop run

We can trust the stopper enough to proceed for now, but it still needs one successful study where:

- the corrected stopper ends the search itself
- the stop reason is clearly a plateau

That will provide stronger confidence than a run that merely reaches its configured trial budget.

## 5. Run budget semantics

Failed runs should not count toward the intended run budget.

The desired semantics are:

- budget should reflect successful completed trials
- failed trials may exist operationally, but they should not reduce the number of real evaluations obtained

## 6. Failed-run cleanup policy

For now, it is acceptable to clean up polluted study DBs after failures manually.

This is not ideal, but it is tolerable in the short term.

## 7. Default-setting caution

Trial `176` gave a useful rough idea for promising defaults, but it is not sufficient by itself to justify all default changes.

Use it as:

- a strong practical reference point

Do not use it as:

- the only source of truth for every sibling default
