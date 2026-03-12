# Runner Provenance Notes

Older study bundles in this repo were produced before exact runner git refs were recorded automatically.

Current best-known bounds:

- `tkus-ce-sign-k500-20260310`
  - Imported source dependency was pinned at [`89692d2`](https://github.com/imadtg/TKUS-CE/commit/89692d2ec47da35b334c5a015a5e4093066a448a).
  - Treat this study as using `89692d2` exactly unless later evidence contradicts it.
- `tkus-ce-sign-k500-hvcheck-20260311`
  - Produced on March 11, 2026.
  - Safe upper bound: [`c4047b8`](https://github.com/imadtg/TKUS-CE/commit/c4047b8c8755c05f478b2af9797a00b62929da17) or older.
- `tkus-ce-sign-k500-main-20260311`
  - Produced on March 11, 2026.
  - Safe upper bound: [`c4047b8`](https://github.com/imadtg/TKUS-CE/commit/c4047b8c8755c05f478b2af9797a00b62929da17) or older.

Future studies should rely on `scripts/optuna_search.py`, which now writes the resolved release tag and exact commit SHA into `runner/resolution.json` and includes that data in `study_summary.json`.
