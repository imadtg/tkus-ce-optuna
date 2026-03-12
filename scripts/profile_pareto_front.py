#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_DATASET = "/home/pc/Desktop/TKUS-CE/testdata/smoke/SIGN_sequence_utility.txt"
DEFAULT_BUILD_SCRIPT = "/home/pc/Desktop/TKUS-CE/scripts/build-fatjar.sh"


@dataclass
class ProfileResult:
    trial_number: int
    runtime_seconds: float
    average_utility: float
    params: dict[str, Any]
    seed: int
    wall_seconds: float
    jfr_path: str
    output_path: str
    iteration_metrics_path: str
    sample_count: int
    top_self_hotspots: list[dict[str, Any]]
    top_inclusive_hotspots: list[dict[str, Any]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile all Pareto-front trials with JFR.")
    parser.add_argument(
        "--study-bundle-dir",
        default="studies/tkus-ce-sign-k500-main-20260311",
        help="Study bundle directory containing study-files/trials.csv and pareto_front.csv.",
    )
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--k", type=int, default=500)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument(
        "--runner-jar",
        default=None,
        help="Existing runnable JAR. If omitted, the sibling TKUS-CE build script is used.",
    )
    parser.add_argument("--build-script", default=DEFAULT_BUILD_SCRIPT)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Profile output directory. Defaults to <study-bundle-dir>/pareto-profile-seed-<seed>.",
    )
    parser.add_argument(
        "--only-trials",
        nargs="*",
        type=int,
        default=None,
        help="Optional subset of Pareto trial numbers to profile.",
    )
    parser.add_argument("--top-n", type=int, default=15)
    return parser.parse_args()


def ensure_runner_jar(args: argparse.Namespace, output_dir: Path) -> Path:
    if args.runner_jar is not None:
        path = Path(args.runner_jar).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Runner JAR does not exist: {path}")
        return path

    built_jar = output_dir / "runner" / "tkus-ce-profile-fatjar.jar"
    built_jar.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([args.build_script, str(built_jar)], check=True)
    return built_jar


def load_pareto_trials(study_bundle_dir: Path) -> list[dict[str, Any]]:
    study_files = study_bundle_dir / "study-files"
    with (study_files / "pareto_front.csv").open(newline="") as csv_file:
        front_points = {
            (float(row["runtime_seconds"]), float(row["average_utility"]))
            for row in csv.DictReader(csv_file)
        }

    selected: list[dict[str, Any]] = []
    with (study_files / "trials.csv").open(newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            if row.get("state") != "COMPLETE":
                continue
            point = (float(row["runtime_seconds"]), float(row["average_utility"]))
            if point not in front_points:
                continue
            selected.append({
                "trial_number": int(row["number"]),
                "runtime_seconds": float(row["runtime_seconds"]),
                "average_utility": float(row["average_utility"]),
                "params": {
                    "n_grams": int(float(row["n_grams"])),
                    "model_confidence": float(row["model_confidence"]),
                    "end_confidence": float(row["end_confidence"]),
                    "end_prob_prior": float(row["end_prob_prior"]),
                    "alpha": float(row["alpha"]),
                    "rho": float(row["rho"]),
                    "pop_size": int(float(row["pop_size"])),
                    "max_iterations": int(float(row["max_iterations"])),
                },
            })
    selected.sort(key=lambda item: (item["runtime_seconds"], -item["average_utility"]))
    return selected


def fqmn(frame: dict[str, Any]) -> str:
    method = frame.get("method") or {}
    class_name = ((method.get("type") or {}).get("name") or "<unknown>").replace("/", ".")
    method_name = method.get("name") or "<unknown>"
    return f"{class_name}.{method_name}"


def parse_execution_samples(jfr_path: Path, top_n: int) -> tuple[int, list[dict[str, Any]], list[dict[str, Any]]]:
    raw = subprocess.check_output(
        ["jfr", "print", "--json", "--events", "jdk.ExecutionSample", "--stack-depth", "64", str(jfr_path)],
        text=True,
    )
    payload = json.loads(raw)
    events = payload["recording"]["events"]

    self_counts: Counter[str] = Counter()
    inclusive_counts: Counter[str] = Counter()
    for event in events:
        frames = (event.get("values") or {}).get("stackTrace", {}).get("frames", [])
        names = [fqmn(frame) for frame in frames]
        if not names:
            continue
        self_counts[names[0]] += 1
        for name in set(names):
            inclusive_counts[name] += 1

    total_samples = sum(self_counts.values())

    def serialize(counter: Counter[str]) -> list[dict[str, Any]]:
        hotspots: list[dict[str, Any]] = []
        for function_name, samples in counter.most_common(top_n):
            hotspots.append({
                "function": function_name,
                "samples": samples,
                "pct": (samples / total_samples * 100.0) if total_samples else 0.0,
            })
        return hotspots

    return total_samples, serialize(self_counts), serialize(inclusive_counts)


def run_profile(
    *,
    runner_jar: Path,
    dataset: Path,
    profile_dir: Path,
    trial_number: int,
    runtime_seconds: float,
    average_utility: float,
    params: dict[str, Any],
    k: int,
    seed: int,
    top_n: int,
) -> ProfileResult:
    trial_dir = profile_dir / f"trial_{trial_number:05d}"
    trial_dir.mkdir(parents=True, exist_ok=True)
    jfr_path = trial_dir / f"seed_{seed}.jfr"
    output_path = trial_dir / f"seed_{seed}_output.txt"
    iteration_metrics_path = trial_dir / f"seed_{seed}_iteration_metrics.csv"

    command = [
        "java",
        f"-XX:StartFlightRecording=filename={jfr_path},settings=profile,dumponexit=true",
        "-jar",
        str(runner_jar),
        "--no-config",
        "-i", str(dataset),
        "-o", str(output_path),
        "-q",
        "-k", str(k),
        "-s", str(seed),
        "-n", str(params["n_grams"]),
        "--model-confidence", str(params["model_confidence"]),
        "--end-confidence", str(params["end_confidence"]),
        "--end-prob-prior", str(params["end_prob_prior"]),
        "--alpha", str(params["alpha"]),
        "--rho", str(params["rho"]),
        "--pop-size", str(params["pop_size"]),
        "--max-iterations", str(params["max_iterations"]),
        "--iteration-metrics", str(iteration_metrics_path),
    ]
    started = time.perf_counter()
    subprocess.run(command, check=True)
    wall_seconds = time.perf_counter() - started

    sample_count, top_self_hotspots, top_inclusive_hotspots = parse_execution_samples(jfr_path, top_n)

    result = ProfileResult(
        trial_number=trial_number,
        runtime_seconds=runtime_seconds,
        average_utility=average_utility,
        params=params,
        seed=seed,
        wall_seconds=wall_seconds,
        jfr_path=str(jfr_path),
        output_path=str(output_path),
        iteration_metrics_path=str(iteration_metrics_path),
        sample_count=sample_count,
        top_self_hotspots=top_self_hotspots,
        top_inclusive_hotspots=top_inclusive_hotspots,
    )
    (trial_dir / "profile_summary.json").write_text(json.dumps(result.__dict__, indent=2))
    return result


def write_outputs(profile_dir: Path, results: list[ProfileResult], top_n: int) -> None:
    rows: list[dict[str, Any]] = []
    aggregate_self: Counter[str] = Counter()
    aggregate_inclusive: Counter[str] = Counter()

    for result in results:
        for hotspot in result.top_self_hotspots:
            aggregate_self[hotspot["function"]] += int(hotspot["samples"])
        for hotspot in result.top_inclusive_hotspots:
            aggregate_inclusive[hotspot["function"]] += int(hotspot["samples"])
        for rank, hotspot in enumerate(result.top_self_hotspots, start=1):
            rows.append({
                "trial_number": result.trial_number,
                "runtime_seconds": result.runtime_seconds,
                "average_utility": result.average_utility,
                "seed": result.seed,
                "rank": rank,
                "function": hotspot["function"],
                "samples": hotspot["samples"],
                "pct": hotspot["pct"],
            })

    with (profile_dir / "profile_hotspots_by_trial.csv").open("w", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["trial_number", "runtime_seconds", "average_utility", "seed", "rank", "function", "samples", "pct"],
        )
        writer.writeheader()
        writer.writerows(rows)

    aggregate_payload = {
        "aggregate_self_hotspots": [
            {"function": name, "samples": samples}
            for name, samples in aggregate_self.most_common(top_n)
        ],
        "aggregate_inclusive_hotspots": [
            {"function": name, "samples": samples}
            for name, samples in aggregate_inclusive.most_common(top_n)
        ],
        "profiled_trials": [result.__dict__ for result in results],
    }
    (profile_dir / "profile_summary.json").write_text(json.dumps(aggregate_payload, indent=2))

    lines = [
        "# Pareto Front Profile",
        "",
        f"- Profiled trials: `{len(results)}`",
        f"- Seed: `{results[0].seed if results else 'n/a'}`",
        "",
        "## Aggregate Self Hotspots",
        "",
    ]
    for hotspot in aggregate_payload["aggregate_self_hotspots"]:
        lines.append(f"- `{hotspot['function']}`: `{hotspot['samples']}` samples")
    lines.extend(["", "## Aggregate Inclusive Hotspots", ""])
    for hotspot in aggregate_payload["aggregate_inclusive_hotspots"]:
        lines.append(f"- `{hotspot['function']}`: `{hotspot['samples']}` samples")
    lines.extend(["", "## Per-Trial Outputs", ""])
    for result in results:
        lines.append(
            f"- Trial `{result.trial_number}`: runtime `{result.runtime_seconds:.3f}s`, "
            f"utility `{result.average_utility:.3f}`, wall `{result.wall_seconds:.3f}s`"
        )
    (profile_dir / "README.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    args = parse_args()
    study_bundle_dir = Path(args.study_bundle_dir).resolve()
    output_dir = Path(args.output_dir).resolve() if args.output_dir else (
        study_bundle_dir / f"pareto-profile-seed-{args.seed}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    runner_jar = ensure_runner_jar(args, output_dir)
    pareto_trials = load_pareto_trials(study_bundle_dir)
    if args.only_trials:
        wanted = set(args.only_trials)
        pareto_trials = [trial for trial in pareto_trials if trial["trial_number"] in wanted]
    if not pareto_trials:
        raise SystemExit("No Pareto-front trials selected for profiling.")

    results: list[ProfileResult] = []
    dataset = Path(args.dataset).resolve()
    for trial in pareto_trials:
        result = run_profile(
            runner_jar=runner_jar,
            dataset=dataset,
            profile_dir=output_dir,
            trial_number=trial["trial_number"],
            runtime_seconds=trial["runtime_seconds"],
            average_utility=trial["average_utility"],
            params=trial["params"],
            k=args.k,
            seed=args.seed,
            top_n=args.top_n,
        )
        results.append(result)

    write_outputs(output_dir, results, args.top_n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
