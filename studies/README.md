# Studies

Put study-specific notes, commands, and later config files here.

Suggested first smoke command:

```bash
./scripts/run_optuna_search.sh \
  --study-name tkus-ce-smoke \
  --dataset /absolute/path/to/SIGN_sequence_utility.txt \
  --runner-jar algorithms/tkus-ce/runner/tkus-ce-fatjar.jar \
  --max-trials 20 \
  --min-trials-before-stop 8 \
  --stop-patience 4
```
