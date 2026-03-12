#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze Pareto-front JFR profile summaries.")
    parser.add_argument(
        "--profile-dir",
        default="studies/tkus-ce-sign-k500-main-20260311/pareto-profile-seed-11",
    )
    parser.add_argument(
        "--output-markdown",
        default=None,
        help="Defaults to <profile-dir>/analysis.md",
    )
    return parser.parse_args()


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    den_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))
    if den_x == 0.0 or den_y == 0.0:
        return None
    return num / (den_x * den_y)


def runtime_band(runtime_seconds: float) -> str:
    if runtime_seconds <= 2.5:
        return "fast"
    if runtime_seconds <= 12.0:
        return "mid"
    return "heavy"


def top_pct_map(trial: dict[str, Any]) -> dict[str, float]:
    return {row["function"]: float(row["pct"]) for row in trial["top_self_hotspots"]}


def main() -> int:
    args = parse_args()
    profile_dir = Path(args.profile_dir).resolve()
    summary = json.loads((profile_dir / "profile_summary.json").read_text())
    trials: list[dict[str, Any]] = summary["profiled_trials"]
    trials.sort(key=lambda trial: float(trial["runtime_seconds"]))

    aggregate_self = summary["aggregate_self_hotspots"]
    candidate_functions = [row["function"] for row in aggregate_self[:12]]

    runtime_series = [float(trial["runtime_seconds"]) for trial in trials]
    utility_series = [float(trial["average_utility"]) for trial in trials]

    function_corrs: list[dict[str, Any]] = []
    band_samples: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for function_name in candidate_functions:
        pct_series = []
        for trial in trials:
            pct = top_pct_map(trial).get(function_name, 0.0)
            pct_series.append(pct)
            band_samples[runtime_band(float(trial["runtime_seconds"]))][function_name].append(pct)
        function_corrs.append({
            "function": function_name,
            "runtime_pearson": pearson(pct_series, runtime_series),
            "utility_pearson": pearson(pct_series, utility_series),
        })

    lines = [
        "# Pareto Profile Analysis",
        "",
        f"- Profile directory: `{profile_dir}`",
        f"- Profiled trials: `{len(trials)}`",
        "",
        "## Aggregate Self Hotspots",
        "",
    ]
    for row in aggregate_self[:12]:
        lines.append(f"- `{row['function']}`: `{row['samples']}` samples")

    lines.extend(["", "## Runtime-Band Hotspots", ""])
    for band in ["fast", "mid", "heavy"]:
        lines.append(f"### {band.capitalize()}")
        band_rows = []
        for function_name, values in band_samples[band].items():
            if not values:
                continue
            band_rows.append((sum(values) / len(values), function_name))
        if not band_rows:
            lines.append("")
            lines.append("- none")
            lines.append("")
            continue
        for mean_pct, function_name in sorted(band_rows, reverse=True)[:8]:
            lines.append(f"- `{function_name}`: mean self-sample share `{mean_pct:.2f}%`")
        lines.append("")

    lines.extend(["## Function Correlations", ""])
    for row in function_corrs:
        runtime_corr = "n/a" if row["runtime_pearson"] is None else f"{row['runtime_pearson']:.3f}"
        utility_corr = "n/a" if row["utility_pearson"] is None else f"{row['utility_pearson']:.3f}"
        lines.append(
            f"- `{row['function']}`: runtime Pearson `{runtime_corr}`, utility Pearson `{utility_corr}`"
        )

    lines.extend(["", "## Per-Trial Top Self Hotspots", ""])
    for trial in trials:
        lines.append(
            f"### Trial {trial['trial_number']} "
            f"(`{float(trial['runtime_seconds']):.3f}s`, `{float(trial['average_utility']):.3f}`)"
        )
        for row in trial["top_self_hotspots"][:8]:
            lines.append(f"- `{row['function']}`: `{row['pct']:.2f}%`")
        lines.append("")

    output_markdown = Path(args.output_markdown).resolve() if args.output_markdown else (profile_dir / "analysis.md")
    output_markdown.write_text("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
