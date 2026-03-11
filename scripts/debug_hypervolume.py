#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrialPoint:
    number: int
    runtime_seconds: float
    average_utility: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug Pareto hypervolume behavior for an Optuna study.")
    parser.add_argument("--study-sqlite", required=True, help="Path to study.sqlite3")
    parser.add_argument("--output-dir", required=True, help="Directory for debug outputs")
    return parser.parse_args()


def load_completed_trials(study_sqlite: Path) -> list[TrialPoint]:
    con = sqlite3.connect(study_sqlite)
    cur = con.cursor()
    rows = cur.execute(
        """
        select t.number, tv0.value as runtime_seconds, tv1.value as average_utility
        from trials t
        join trial_values tv0 on tv0.trial_id=t.trial_id and tv0.objective=0
        join trial_values tv1 on tv1.trial_id=t.trial_id and tv1.objective=1
        where t.state='COMPLETE'
        order by t.number
        """
    ).fetchall()
    return [TrialPoint(number=row[0], runtime_seconds=row[1], average_utility=row[2]) for row in rows]


def dominates(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return (a[0] <= b[0] and a[1] >= b[1]) and (a[0] < b[0] or a[1] > b[1])


def pareto_front(points: list[TrialPoint]) -> list[TrialPoint]:
    front: list[TrialPoint] = []
    for candidate in points:
        candidate_pair = (candidate.runtime_seconds, candidate.average_utility)
        if any(
            dominates((other.runtime_seconds, other.average_utility), candidate_pair)
            for other in points
            if other.number != candidate.number
        ):
            continue
        front.append(candidate)
    front.sort(key=lambda point: (point.runtime_seconds, -point.average_utility, point.number))
    return front


def compute_hypervolume(front: list[TrialPoint], runtime_ref: float, utility_ref: float) -> float:
    area = 0.0
    previous_runtime = runtime_ref
    for point in sorted(front, key=lambda item: item.runtime_seconds, reverse=True):
        area += max(0.0, previous_runtime - point.runtime_seconds) * max(0.0, point.average_utility - utility_ref)
        previous_runtime = min(previous_runtime, point.runtime_seconds)
    return area


def main() -> int:
    args = parse_args()
    study_sqlite = Path(args.study_sqlite)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    completed = load_completed_trials(study_sqlite)
    if not completed:
        raise SystemExit("No completed trials found.")

    fixed_runtime_ref = max(point.runtime_seconds for point in completed) * 1.05
    fixed_utility_ref = min(point.average_utility for point in completed) * 0.95

    rows: list[dict[str, object]] = []
    previous_dynamic_hv: float | None = None
    previous_fixed_hv: float | None = None
    previous_front_numbers: list[int] = []

    for idx in range(len(completed)):
        prefix = completed[: idx + 1]
        front = pareto_front(prefix)
        front_numbers = [point.number for point in front]

        dynamic_runtime_ref = max(point.runtime_seconds for point in front) * 1.05
        dynamic_utility_ref = min(point.average_utility for point in front) * 0.95
        dynamic_hv = compute_hypervolume(front, dynamic_runtime_ref, dynamic_utility_ref)
        fixed_hv = compute_hypervolume(front, fixed_runtime_ref, fixed_utility_ref)

        point = prefix[-1]
        row = {
            "trial_number": point.number,
            "runtime_seconds": point.runtime_seconds,
            "average_utility": point.average_utility,
            "front_numbers": json.dumps(front_numbers),
            "front_size": len(front_numbers),
            "front_changed": front_numbers != previous_front_numbers,
            "on_front": point.number in front_numbers,
            "dynamic_runtime_ref": dynamic_runtime_ref,
            "dynamic_utility_ref": dynamic_utility_ref,
            "dynamic_hv": dynamic_hv,
            "dynamic_hv_delta": None if previous_dynamic_hv is None else dynamic_hv - previous_dynamic_hv,
            "fixed_runtime_ref": fixed_runtime_ref,
            "fixed_utility_ref": fixed_utility_ref,
            "fixed_hv": fixed_hv,
            "fixed_hv_delta": None if previous_fixed_hv is None else fixed_hv - previous_fixed_hv,
        }
        rows.append(row)
        previous_dynamic_hv = dynamic_hv
        previous_fixed_hv = fixed_hv
        previous_front_numbers = front_numbers

    csv_path = output_dir / "hypervolume_debug.csv"
    with csv_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    dynamic_regressions = [
        row for row in rows
        if row["dynamic_hv_delta"] is not None and row["dynamic_hv_delta"] < 0
    ]

    summary = {
        "fixed_runtime_ref": fixed_runtime_ref,
        "fixed_utility_ref": fixed_utility_ref,
        "num_completed_trials": len(completed),
        "dynamic_regression_trials": [row["trial_number"] for row in dynamic_regressions],
        "dynamic_regressions": dynamic_regressions,
    }
    (output_dir / "hypervolume_debug_summary.json").write_text(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
