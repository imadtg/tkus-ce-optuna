#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import optuna
from optuna.artifacts import FileSystemArtifactStore
from optuna.artifacts import upload_artifact
from optuna_dashboard import save_note
from optuna_dashboard.artifact import get_artifact_path
from optuna.trial import TrialState


SEEDS = [11, 29, 47, 71, 101]
SEARCH_SPACE = {
    "n_grams": [0, 1, 3, 5],
    "model_confidence": [0.5, 0.9, 1.0],
    "end_confidence": [0.5, 0.9, 1.0],
    "end_prob_prior": [0.1, 0.5],
    "alpha": [0.1, 1.0, 10.0],
    "rho": [0.1, 0.2, 0.5],
    "pop_size": [50, 200, 1000],
    "max_iterations": [50, 200, 1000],
}


@dataclass
class SeedRunResult:
    seed: int
    runtime_seconds: float
    peak_rss_mb: float | None
    average_utility: float
    total_utility: int
    num_sequences: int
    return_code: int
    output_path: str
    iteration_metrics_path: str
    repeat_runtimes: list[float]
    repeat_peak_rss_mb: list[float | None]
    representative_repeat_index: int | None


class HypervolumeStagnationStopper:
    def __init__(
        self,
        min_trials: int,
        patience: int,
        min_improvement: float,
        runtime_ref: float,
        utility_ref: float,
        debug: bool = False,
        debug_log_path: Path | None = None,
    ) -> None:
        self.min_trials = min_trials
        self.patience = patience
        self.min_improvement = min_improvement
        self.runtime_ref = runtime_ref
        self.utility_ref = utility_ref
        self.best_hv = float("-inf")
        self.stale_callbacks = 0
        self.history: list[dict[str, float | int]] = []
        self.debug = debug
        self.debug_log_path = debug_log_path
        self._initialized = False

    def _hydrate_from_study(self, study: optuna.Study) -> None:
        if self._initialized:
            return
        raw_history = study.user_attrs.get("hypervolume_history", [])
        if isinstance(raw_history, list):
            self.history = list(raw_history)
        if self.history:
            self.best_hv = max(float(item["hypervolume"]) for item in self.history)
        self._initialized = True

    def _append_debug_row(
        self,
        *,
        trial_number: int,
        hv: float,
        front_size: int,
        max_runtime: float,
        min_utility: float,
        reference_valid: bool,
    ) -> None:
        debug_row = {
            "trial_number": trial_number,
            "hypervolume": hv,
            "best_hypervolume": self.best_hv,
            "stale_callbacks": self.stale_callbacks,
            "front_size": front_size,
            "max_runtime": max_runtime,
            "min_utility": min_utility,
            "runtime_ref": self.runtime_ref,
            "utility_ref": self.utility_ref,
            "reference_valid": reference_valid,
        }
        if self.debug:
            print(f"[hv] {json.dumps(debug_row, sort_keys=True)}", file=sys.stderr, flush=True)
        if self.debug_log_path is None:
            return
        self.debug_log_path.parent.mkdir(parents=True, exist_ok=True)
        write_header = not self.debug_log_path.exists()
        with self.debug_log_path.open("a", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=list(debug_row.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(debug_row)

    def __call__(self, study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        self._hydrate_from_study(study)
        completed = [
            t for t in study.get_trials(deepcopy=False)
            if t.state == TrialState.COMPLETE and t.values is not None
        ]
        if not completed:
            return

        max_runtime = max(float(t.values[0]) for t in completed)
        min_utility = min(float(t.values[1]) for t in completed)
        front_size = len(pareto_points(completed))
        reference_valid = self.runtime_ref >= max_runtime and self.utility_ref <= min_utility
        if not reference_valid:
            study.set_user_attr("stop_reason", "hypervolume_reference_invalid")
            study.set_user_attr("hypervolume_reference_warning", {
                "runtime_ref": self.runtime_ref,
                "utility_ref": self.utility_ref,
                "max_runtime_seen": max_runtime,
                "min_utility_seen": min_utility,
            })
            self._append_debug_row(
                trial_number=trial.number,
                hv=float("nan"),
                front_size=front_size,
                max_runtime=max_runtime,
                min_utility=min_utility,
                reference_valid=False,
            )
            return

        hv = compute_hypervolume_2d(completed, self.runtime_ref, self.utility_ref)
        self.history.append({"trial_number": trial.number, "hypervolume": hv})
        study.set_user_attr("hypervolume_history", self.history)
        study.set_user_attr("hypervolume_reference", {
            "runtime_ref": self.runtime_ref,
            "utility_ref": self.utility_ref,
        })
        self._append_debug_row(
            trial_number=trial.number,
            hv=hv,
            front_size=front_size,
            max_runtime=max_runtime,
            min_utility=min_utility,
            reference_valid=True,
        )

        if len(completed) < self.min_trials:
            return

        if hv > self.best_hv + self.min_improvement:
            self.best_hv = hv
            self.stale_callbacks = 0
            return

        self.stale_callbacks += 1
        if self.stale_callbacks >= self.patience:
            study.set_user_attr("stop_reason", "hypervolume_plateau")
            study.stop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run multi-objective Optuna search for externally sourced sequence-mining runners.")
    parser.add_argument(
        "--dataset",
        action="append",
        required=True,
        help="Dataset path. Repeat the flag to evaluate multiple datasets per trial.",
    )
    parser.add_argument("--study-name", default="tkus_ce_mo")
    parser.add_argument("--storage", default=None, help="Optuna storage URL. Defaults to local SQLite in artifacts.")
    parser.add_argument("--artifacts-dir", default="artifacts/optuna")
    parser.add_argument(
        "--artifact-store-dir",
        default=None,
        help="Artifact store directory for dashboard-visible uploads. Defaults to <artifacts-dir>/_dashboard_artifacts.",
    )
    parser.add_argument("--k", type=int, default=500)
    parser.add_argument("--max-trials", type=int, default=1000)
    parser.add_argument("--timeout-seconds", type=int, default=None)
    parser.add_argument("--min-trials-before-stop", type=int, default=24)
    parser.add_argument("--stop-patience", type=int, default=12)
    parser.add_argument("--stop-min-improvement", type=float, default=1e-6)
    parser.add_argument(
        "--hypervolume-runtime-ref",
        type=float,
        default=1000.0,
        help="Fixed runtime reference for hypervolume. Must be worse than useful runtime points.",
    )
    parser.add_argument(
        "--hypervolume-utility-ref",
        type=float,
        default=0.0,
        help="Fixed utility floor for hypervolume.",
    )
    parser.add_argument(
        "--hypervolume-debug",
        action="store_true",
        help="Emit per-callback hypervolume diagnostics to stderr and CSV.",
    )
    parser.add_argument(
        "--runner-release",
        default="latest",
        help="Released TKUS-CE runner to use when --runner-jar is not provided: latest, edge, or an exact version.",
    )
    parser.add_argument(
        "--runner-repo",
        default="imadtg/TKUS-CE",
        help="GitHub repository that publishes the TKUS-CE release artifacts.",
    )
    parser.add_argument(
        "--build-script",
        default="algorithms/tkus-ce/src/Main.java",
        help="Deprecated source-build fallback. Kept only for compatibility with older local workflows.",
    )
    parser.add_argument("--runner-jar", default=None, help="Use an existing runnable jar instead of building one.")
    parser.add_argument("--runtime-repeats", type=int, default=1)
    parser.add_argument("--warmup-runs", type=int, default=0)
    parser.add_argument(
        "--ce-early-stop-patience",
        type=int,
        default=0,
        help="Optional algorithm-level plateau patience. Disabled by default.",
    )
    parser.add_argument("--ce-early-stop-warmup", type=int, default=0)
    parser.add_argument("--ce-early-stop-min-delta", type=float, default=0.0)
    return parser.parse_args()


def parse_utilities(output_path: Path) -> tuple[int, int]:
    total = 0
    count = 0
    if not output_path.exists():
        return total, count
    for line in output_path.read_text().splitlines():
        marker = "#UTIL:"
        if marker not in line:
            continue
        total += int(line.split(marker, 1)[1].strip())
        count += 1
    return total, count


def parse_peak_rss_mb(time_output_path: Path) -> float | None:
    if not time_output_path.exists():
        return None
    for line in time_output_path.read_text().splitlines():
        prefix = "Maximum resident set size (kbytes):"
        stripped = line.strip()
        if stripped.startswith(prefix):
            value = stripped.split(":", 1)[1].strip()
            return int(value) / 1024.0
    return None


def parse_elapsed_seconds(time_output_path: Path) -> float | None:
    if not time_output_path.exists():
        return None
    pattern = re.compile(r"Elapsed \(wall clock\) time \(h:mm:ss or m:ss\):\s*(?P<value>\S+)")
    for line in time_output_path.read_text().splitlines():
        match = pattern.search(line)
        if not match:
            continue
        value = match.group("value")
        parts = value.split(":")
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
        if len(parts) == 2:
            minutes, seconds = parts
            return float(minutes) * 60 + float(seconds)
        return float(parts[0])
    return None


def run_invocation(command: list[str], output_path: Path, iteration_metrics_path: Path, time_output_path: Path,
                   stdout_path: Path, stderr_path: Path) -> tuple[int, float, float | None]:
    started = time.perf_counter()
    with stdout_path.open("w") as stdout_file, stderr_path.open("w") as stderr_file:
        completed = subprocess.run(
            command,
            check=False,
            stdout=stdout_file,
            stderr=stderr_file,
            text=True,
        )
    runtime_seconds = parse_elapsed_seconds(time_output_path)
    if runtime_seconds is None:
        runtime_seconds = time.perf_counter() - started
    peak_rss_mb = parse_peak_rss_mb(time_output_path)
    return completed.returncode, runtime_seconds, peak_rss_mb


def representative_float(values: list[float]) -> float:
    return statistics.median(values)


def representative_optional_float(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return statistics.median(present)


def representative_repeat_index(repeat_runtimes: list[float]) -> int | None:
    if not repeat_runtimes:
        return None
    target = statistics.median(repeat_runtimes)
    return min(range(len(repeat_runtimes)), key=lambda index: abs(repeat_runtimes[index] - target))


def completed_trial_count(study: optuna.Study) -> int:
    return len([
        trial for trial in study.get_trials(deepcopy=False)
        if trial.state == TrialState.COMPLETE and trial.values is not None
    ])


def build_runner_jar(args: argparse.Namespace, study_dir: Path) -> Path:
    runner_dir = study_dir / "runner"
    runner_dir.mkdir(parents=True, exist_ok=True)
    resolution_path = runner_dir / "resolution.json"

    if args.runner_jar is not None:
        runner_jar = Path(args.runner_jar)
        if not runner_jar.exists():
            raise FileNotFoundError(f"Runner JAR does not exist: {runner_jar}")
        if not resolution_path.exists():
            local_resolution = {
                "runner_requested_spec": "local-path",
                "runner_repo": args.runner_repo,
                "runner_output_jar": str(runner_jar.resolve()),
            }
            build_metadata_path = runner_jar.with_suffix(runner_jar.suffix + ".build.json")
            if build_metadata_path.exists():
                local_resolution["build_metadata"] = json.loads(build_metadata_path.read_text())
                for key in ["version", "release_channel", "git_ref", "git_sha", "repository", "built_at_utc"]:
                    if key in local_resolution["build_metadata"]:
                        local_resolution[f"runner_{key}"] = local_resolution["build_metadata"][key]
            resolution_path.write_text(json.dumps(local_resolution, indent=2))
        return runner_jar

    runner_jar = runner_dir / "tkus-ce-runner.jar"
    if runner_jar.exists() and resolution_path.exists():
        return runner_jar

    resolver = Path(__file__).with_name("fetch_tkus_ce_release.py")
    command = [
        "uv",
        "run",
        str(resolver),
        "--repo",
        args.runner_repo,
        "--spec",
        args.runner_release,
        "--output-jar",
        str(runner_jar),
        "--output-json",
        str(resolution_path),
    ]
    subprocess.run(command, check=True)
    return runner_jar


def run_seed(
    args: argparse.Namespace,
    runner_jar: Path,
    dataset: Path,
    trial_dir: Path,
    params: dict[str, Any],
    seed: int,
) -> SeedRunResult:
    dataset_name = dataset.stem
    seed_dir = trial_dir / f"{dataset_name}_seed_{seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)

    base_command = [
        "java",
        "-jar",
        str(runner_jar),
        "--no-config",
        "-i", str(dataset),
        "-q",
        "-k", str(args.k),
        "-s", str(seed),
        "-n", str(params["n_grams"]),
        "--model-confidence", str(params["model_confidence"]),
        "--end-confidence", str(params["end_confidence"]),
        "--end-prob-prior", str(params["end_prob_prior"]),
        "--alpha", str(params["alpha"]),
        "--rho", str(params["rho"]),
        "--pop-size", str(params["pop_size"]),
        "--max-iterations", str(params["max_iterations"]),
    ]
    if args.ce_early_stop_patience > 0:
        base_command.extend([
            "--early-stop-patience", str(args.ce_early_stop_patience),
            "--early-stop-warmup", str(args.ce_early_stop_warmup),
            "--early-stop-min-delta", str(args.ce_early_stop_min_delta),
        ])

    for warmup_index in range(args.warmup_runs):
        warmup_dir = seed_dir / f"warmup_{warmup_index:02d}"
        warmup_dir.mkdir(parents=True, exist_ok=True)
        warmup_output = warmup_dir / "output.txt"
        warmup_iteration_metrics = warmup_dir / "iteration_metrics.csv"
        warmup_time_output = warmup_dir / "time.txt"
        warmup_stdout = warmup_dir / "stdout.txt"
        warmup_stderr = warmup_dir / "stderr.txt"
        warmup_command = base_command + [
            "-o", str(warmup_output),
            "--iteration-metrics", str(warmup_iteration_metrics),
        ]
        if Path("/usr/bin/time").exists():
            warmup_command = ["/usr/bin/time", "-v", "-o", str(warmup_time_output)] + warmup_command
        run_invocation(warmup_command, warmup_output, warmup_iteration_metrics, warmup_time_output,
                       warmup_stdout, warmup_stderr)

    repeat_runtimes: list[float] = []
    repeat_peak_rss_mb: list[float | None] = []
    repeat_average_utilities: list[float] = []
    repeat_total_utilities: list[int] = []
    repeat_num_sequences: list[int] = []
    measured_return_code = 0
    repeat_output_paths: list[Path] = []
    repeat_iteration_paths: list[Path] = []

    for repeat_index in range(args.runtime_repeats):
        repeat_dir = seed_dir / f"repeat_{repeat_index:02d}"
        repeat_dir.mkdir(parents=True, exist_ok=True)
        output_path = repeat_dir / "output.txt"
        iteration_metrics_path = repeat_dir / "iteration_metrics.csv"
        stdout_path = repeat_dir / "stdout.txt"
        stderr_path = repeat_dir / "stderr.txt"
        time_output_path = repeat_dir / "time.txt"

        measured_command = base_command + [
            "-o", str(output_path),
            "--iteration-metrics", str(iteration_metrics_path),
        ]
        if Path("/usr/bin/time").exists():
            measured_command = ["/usr/bin/time", "-v", "-o", str(time_output_path)] + measured_command

        return_code, runtime_seconds, peak_rss_mb = run_invocation(
            measured_command,
            output_path,
            iteration_metrics_path,
            time_output_path,
            stdout_path,
            stderr_path,
        )
        if repeat_index == 0:
            measured_return_code = return_code
        if return_code != 0:
            measured_return_code = return_code
            break

        total_utility, num_sequences = parse_utilities(output_path)
        average_utility = (total_utility / num_sequences) if num_sequences else 0.0

        repeat_runtimes.append(runtime_seconds)
        repeat_peak_rss_mb.append(peak_rss_mb)
        repeat_average_utilities.append(average_utility)
        repeat_total_utilities.append(total_utility)
        repeat_num_sequences.append(num_sequences)
        repeat_output_paths.append(output_path)
        repeat_iteration_paths.append(iteration_metrics_path)

    if measured_return_code != 0:
        runtime_seconds = repeat_runtimes[0] if repeat_runtimes else float("inf")
        peak_rss_mb = repeat_peak_rss_mb[0] if repeat_peak_rss_mb else None
        average_utility = repeat_average_utilities[0] if repeat_average_utilities else 0.0
        total_utility = repeat_total_utilities[0] if repeat_total_utilities else 0
        num_sequences = repeat_num_sequences[0] if repeat_num_sequences else 0
        chosen_repeat_index = 0 if repeat_output_paths else None
    else:
        runtime_seconds = representative_float(repeat_runtimes)
        peak_rss_mb = representative_optional_float(repeat_peak_rss_mb)
        average_utility = representative_float(repeat_average_utilities)
        total_utility = int(statistics.median(repeat_total_utilities))
        num_sequences = int(statistics.median(repeat_num_sequences))
        chosen_repeat_index = representative_repeat_index(repeat_runtimes)

    chosen_output_path = repeat_output_paths[chosen_repeat_index] if chosen_repeat_index is not None else None
    chosen_iteration_metrics_path = (
        repeat_iteration_paths[chosen_repeat_index] if chosen_repeat_index is not None else None
    )

    result = SeedRunResult(
        seed=seed,
        runtime_seconds=runtime_seconds,
        peak_rss_mb=peak_rss_mb,
        average_utility=average_utility,
        total_utility=total_utility,
        num_sequences=num_sequences,
        return_code=measured_return_code,
        output_path=str(chosen_output_path) if chosen_output_path is not None else "",
        iteration_metrics_path=str(chosen_iteration_metrics_path) if chosen_iteration_metrics_path is not None else "",
        repeat_runtimes=repeat_runtimes,
        repeat_peak_rss_mb=repeat_peak_rss_mb,
        representative_repeat_index=chosen_repeat_index,
    )
    (seed_dir / "metrics.json").write_text(json.dumps(asdict(result), indent=2))
    if chosen_iteration_metrics_path is not None and chosen_repeat_index is not None:
        plot_seed_convergence(Path(chosen_iteration_metrics_path), seed_dir)
    return result


def trial_objective(
    trial: optuna.Trial,
    args: argparse.Namespace,
    study_dir: Path,
    runner_jar: Path,
    artifact_store: FileSystemArtifactStore,
) -> tuple[float, float]:
    params = {
        "n_grams": trial.suggest_categorical("n_grams", SEARCH_SPACE["n_grams"]),
        "model_confidence": trial.suggest_categorical("model_confidence", SEARCH_SPACE["model_confidence"]),
        "end_confidence": trial.suggest_categorical("end_confidence", SEARCH_SPACE["end_confidence"]),
        "end_prob_prior": trial.suggest_categorical("end_prob_prior", SEARCH_SPACE["end_prob_prior"]),
        "alpha": trial.suggest_categorical("alpha", SEARCH_SPACE["alpha"]),
        "rho": trial.suggest_categorical("rho", SEARCH_SPACE["rho"]),
        "pop_size": trial.suggest_categorical("pop_size", SEARCH_SPACE["pop_size"]),
        "max_iterations": trial.suggest_categorical("max_iterations", SEARCH_SPACE["max_iterations"]),
    }

    trial_dir = study_dir / "trials" / f"trial_{trial.number:05d}"
    trial_dir.mkdir(parents=True, exist_ok=True)
    (trial_dir / "params.json").write_text(json.dumps(params, indent=2))

    seed_results: list[SeedRunResult] = []
    for dataset_str in args.dataset:
        dataset = Path(dataset_str)
        for seed in SEEDS:
            seed_results.append(run_seed(args, runner_jar, dataset, trial_dir, params, seed))

    failed_runs = [result for result in seed_results if result.return_code != 0]
    if failed_runs:
        summary = {
            "params": params,
            "failed_runs": [asdict(result) for result in failed_runs],
        }
        (trial_dir / "failure.json").write_text(json.dumps(summary, indent=2))
        trial.set_user_attr("artifact_dir", str(trial_dir))
        trial.set_user_attr("status", "failed")
        update_trial_dashboard_note(trial, trial_dir, params, None, artifact_store)
        raise RuntimeError(f"Trial {trial.number} failed for all seed runs.")

    runtime_values = [result.runtime_seconds for result in seed_results]
    average_utility_values = [result.average_utility for result in seed_results]
    total_utility_values = [result.total_utility for result in seed_results]
    rss_values = [result.peak_rss_mb for result in seed_results if result.peak_rss_mb is not None]

    aggregated = {
        "params": params,
        "datasets": args.dataset,
        "k": args.k,
        "seeds": SEEDS,
        "mean_runtime_seconds": statistics.fmean(runtime_values),
        "std_runtime_seconds": statistics.pstdev(runtime_values) if len(runtime_values) > 1 else 0.0,
        "mean_average_utility": statistics.fmean(average_utility_values),
        "std_average_utility": statistics.pstdev(average_utility_values) if len(average_utility_values) > 1 else 0.0,
        "mean_total_utility": statistics.fmean(total_utility_values),
        "mean_peak_rss_mb": statistics.fmean(rss_values) if rss_values else None,
        "std_peak_rss_mb": statistics.pstdev(rss_values) if len(rss_values) > 1 else 0.0,
        "seed_runs": [asdict(result) for result in seed_results],
    }
    (trial_dir / "summary.json").write_text(json.dumps(aggregated, indent=2))

    plot_trial_convergence(seed_results, trial_dir)

    trial.set_user_attr("artifact_dir", str(trial_dir))
    trial.set_user_attr("status", "ok")
    trial.set_user_attr("mean_peak_rss_mb", aggregated["mean_peak_rss_mb"])
    update_trial_dashboard_note(trial, trial_dir, params, aggregated, artifact_store)
    return aggregated["mean_runtime_seconds"], aggregated["mean_average_utility"]


def read_iteration_metric_series(path: Path, field: str) -> list[float]:
    if not path.exists():
        return []
    with path.open(newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [float(row[field]) for row in reader]


def plot_trial_convergence(seed_results: list[SeedRunResult], trial_dir: Path) -> None:
    topk_series = [
        read_iteration_metric_series(Path(result.iteration_metrics_path), "top_k_average_utility_so_far")
        for result in seed_results
    ]
    topk_series = [series for series in topk_series if series]
    if not topk_series:
        return

    max_len = max(len(series) for series in topk_series)
    averaged: list[float] = []
    for idx in range(max_len):
        values = [series[idx] for series in topk_series if idx < len(series)]
        averaged.append(statistics.fmean(values))

    plt.figure(figsize=(8, 4.5))
    for idx, series in enumerate(topk_series):
        plt.plot(range(len(series)), series, alpha=0.25, linewidth=1, label="seed" if idx == 0 else None)
    plt.plot(range(len(averaged)), averaged, color="black", linewidth=2, label="mean")
    plt.xlabel("CE iteration")
    plt.ylabel("Best top-k average utility so far")
    plt.title("Best top-k average convergence by seed")
    plt.legend()
    plt.tight_layout()
    plt.savefig(trial_dir / "convergence_topk_average.png", dpi=160)
    plt.close()


def plot_seed_convergence(iteration_metrics_path: Path, seed_dir: Path) -> None:
    if not iteration_metrics_path.exists():
        return

    with iteration_metrics_path.open(newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))
    if not rows:
        return

    elapsed_seconds = [float(row["elapsed_ms"]) / 1000.0 for row in rows]
    iterations = [int(row["iteration"]) for row in rows]
    top_k_average_utility = [float(row["top_k_average_utility_so_far"]) for row in rows]
    best_elite_utility = [float(row["best_elite_utility"]) for row in rows]
    min_utility = [float(row["min_utility"]) for row in rows]
    min_elite_utility = [float(row["min_elite_utility"]) for row in rows]

    plt.figure(figsize=(12, 7))
    plt.plot(elapsed_seconds, top_k_average_utility, label="Best top-k average utility so far", linewidth=2.2)
    plt.plot(elapsed_seconds, best_elite_utility, label="Best elite utility", linewidth=1.8)
    plt.plot(elapsed_seconds, min_utility, label="Min utility", linewidth=1.8)
    plt.plot(elapsed_seconds, min_elite_utility, label="Min elite utility", linewidth=1.8)
    plt.xlabel("Elapsed time (s)")
    plt.ylabel("Utility")
    plt.title("Convergence metrics by elapsed time")
    plt.grid(True, alpha=0.3)
    plt.legend()

    tick_count = min(8, len(elapsed_seconds))
    tick_indices = sorted({round(index * (len(elapsed_seconds) - 1) / max(1, tick_count - 1)) for index in range(tick_count)})
    tick_positions = [elapsed_seconds[index] for index in tick_indices]
    tick_labels = [str(iterations[index]) for index in tick_indices]
    top_axis = plt.gca().twiny()
    top_axis.set_xlim(plt.gca().get_xlim())
    top_axis.set_xticks(tick_positions)
    top_axis.set_xticklabels(tick_labels)
    top_axis.set_xlabel("Iteration")

    plt.tight_layout()
    plt.savefig(seed_dir / "convergence_metrics.png", dpi=160)
    plt.close()


def maybe_upload_artifact(
    artifact_store: FileSystemArtifactStore,
    owner: optuna.Study | optuna.Trial,
    file_path: Path,
) -> tuple[str, str] | None:
    if not file_path.exists():
        return None
    artifact_id = upload_artifact(
        artifact_store=artifact_store,
        file_path=str(file_path),
        study_or_trial=owner,
    )
    return artifact_id, get_artifact_path(owner, artifact_id)


def update_trial_dashboard_note(
    trial: optuna.Trial,
    trial_dir: Path,
    params: dict[str, Any],
    aggregated: dict[str, Any] | None,
    artifact_store: FileSystemArtifactStore,
) -> None:
    artifact_lines: list[str] = []

    for file_name in ["params.json", "summary.json" if aggregated is not None else "failure.json"]:
        uploaded = maybe_upload_artifact(artifact_store, trial, trial_dir / file_name)
        if uploaded is None:
            continue
        _, path = uploaded
        artifact_lines.append(f"- [{file_name}]({path})")

    uploaded = maybe_upload_artifact(artifact_store, trial, trial_dir / "convergence_topk_average.png")
    trial_plot_markdown = ""
    if uploaded is not None:
        _, path = uploaded
        artifact_lines.append(f"- [convergence_topk_average.png]({path})")
        trial_plot_markdown = f"\n## Trial Convergence\n\n![Trial convergence]({path})\n"

    for seed_dir in sorted(path for path in trial_dir.iterdir() if path.is_dir() and "_seed_" in path.name):
        uploaded = maybe_upload_artifact(artifact_store, trial, seed_dir / "convergence_metrics.png")
        if uploaded is None:
            continue
        _, path = uploaded
        artifact_lines.append(f"- [{seed_dir.name}_convergence_metrics.png]({path})")

    if aggregated is None:
        body = "\n".join([
            f"# Trial {trial.number}",
            "",
            "Execution failed.",
            "",
            "## Parameters",
            "```json",
            json.dumps(params, indent=2),
            "```",
            "",
            "## Artifacts",
            *artifact_lines,
        ])
        save_note(trial, body)
        return

    body = "\n".join([
        f"# Trial {trial.number}",
        "",
        "## Parameters",
        "```json",
        json.dumps(params, indent=2),
        "```",
        "",
        "## Aggregated Metrics",
        "```json",
        json.dumps({
            "mean_runtime_seconds": aggregated["mean_runtime_seconds"],
            "mean_average_utility": aggregated["mean_average_utility"],
            "mean_peak_rss_mb": aggregated["mean_peak_rss_mb"],
            "std_runtime_seconds": aggregated["std_runtime_seconds"],
            "std_average_utility": aggregated["std_average_utility"],
        }, indent=2),
        "```",
        trial_plot_markdown,
        "## Artifacts",
        *artifact_lines,
    ])
    save_note(trial, body)


def dominates(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return (a[0] <= b[0] and a[1] >= b[1]) and (a[0] < b[0] or a[1] > b[1])


def pareto_points(trials: list[optuna.trial.FrozenTrial]) -> list[tuple[float, float]]:
    values = [(float(t.values[0]), float(t.values[1])) for t in trials if t.values is not None]
    front: list[tuple[float, float]] = []
    for candidate in values:
        if any(dominates(other, candidate) for other in values if other != candidate):
            continue
        front.append(candidate)
    front.sort(key=lambda item: (item[0], -item[1]))
    return front


def compute_hypervolume_2d(
    trials: list[optuna.trial.FrozenTrial],
    runtime_ref: float,
    utility_ref: float,
) -> float:
    front = pareto_points(trials)
    if not front:
        return 0.0

    if math.isclose(runtime_ref, max(point[0] for point in front)):
        runtime_ref += 1e-9
    if math.isclose(utility_ref, min(point[1] for point in front)):
        utility_ref -= 1e-9

    area = 0.0
    previous_runtime = runtime_ref
    for runtime_value, utility_value in sorted(front, key=lambda item: item[0], reverse=True):
        area += max(0.0, previous_runtime - runtime_value) * max(0.0, utility_value - utility_ref)
        previous_runtime = min(previous_runtime, runtime_value)
    return area


def write_trials_csv(study: optuna.Study, output_path: Path) -> None:
    rows: list[dict[str, Any]] = []
    for trial in study.get_trials(deepcopy=False):
        row: dict[str, Any] = {
            "number": trial.number,
            "state": trial.state.name,
        }
        if trial.values is not None:
            row["runtime_seconds"] = trial.values[0]
            row["average_utility"] = trial.values[1]
        if "mean_peak_rss_mb" in trial.user_attrs:
            row["mean_peak_rss_mb"] = trial.user_attrs["mean_peak_rss_mb"]
        row.update(trial.params)
        row["artifact_dir"] = trial.user_attrs.get("artifact_dir")
        rows.append(row)

    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    with output_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def plot_study_outputs(study: optuna.Study, study_dir: Path) -> None:
    completed = [
        trial for trial in study.get_trials(deepcopy=False)
        if trial.state == TrialState.COMPLETE and trial.values is not None
    ]
    if not completed:
        return

    runtimes = [trial.values[0] for trial in completed]
    utilities = [trial.values[1] for trial in completed]
    plt.figure(figsize=(7, 5))
    plt.scatter(runtimes, utilities, alpha=0.6)
    plt.xlabel("Mean runtime (s)")
    plt.ylabel("Mean average utility")
    plt.title("Pareto search trials")
    plt.tight_layout()
    plt.savefig(study_dir / "pareto_scatter.png", dpi=160)
    plt.close()

    history = study.user_attrs.get("hypervolume_history", [])
    if history:
        plt.figure(figsize=(7, 4.5))
        plt.plot([item["trial_number"] for item in history], [item["hypervolume"] for item in history])
        plt.xlabel("Trial number")
        plt.ylabel("Hypervolume")
        plt.title("Pareto hypervolume history")
        plt.tight_layout()
        plt.savefig(study_dir / "hypervolume_history.png", dpi=160)
        plt.close()

    front = pareto_points(completed)
    with (study_dir / "pareto_front.csv").open("w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["runtime_seconds", "average_utility"])
        writer.writerows(front)


def update_study_dashboard_note(
    study: optuna.Study,
    study_dir: Path,
    summary: dict[str, Any] | None,
    artifact_store: FileSystemArtifactStore,
) -> None:
    artifact_lines: list[str] = []
    image_sections: list[str] = []
    for artifact_name, title in [
        ("pareto_scatter.png", "Pareto Scatter"),
        ("hypervolume_history.png", "Hypervolume History"),
    ]:
        uploaded = maybe_upload_artifact(artifact_store, study, study_dir / artifact_name)
        if uploaded is None:
            continue
        _, path = uploaded
        artifact_lines.append(f"- [{artifact_name}]({path})")
        image_sections.append(f"## {title}\n\n![{title}]({path})\n")

    for artifact_name in ["trials.csv", "pareto_front.csv", "study_summary.json"]:
        uploaded = maybe_upload_artifact(artifact_store, study, study_dir / artifact_name)
        if uploaded is None:
            continue
        _, path = uploaded
        artifact_lines.append(f"- [{artifact_name}]({path})")

    summary_block = "Study outputs are still being generated."
    if summary is not None:
        summary_block = json.dumps({
            "study_name": summary["study_name"],
            "completed_trials": summary["completed_trials"],
            "stop_reason": summary.get("stop_reason"),
            "hypervolume_reference": summary["hypervolume_reference"],
        }, indent=2)

    body = "\n".join([
        f"# {study.study_name}",
        "",
        "## Summary",
        "```json",
        summary_block,
        "```",
        "",
        *image_sections,
        "## Artifacts",
        *artifact_lines,
    ])
    save_note(study, body)


def write_study_bundle(study_dir: Path, summary: dict[str, Any]) -> Path:
    bundle_dir = Path("studies") / summary["study_name"]
    bundle_dir.mkdir(parents=True, exist_ok=True)

    copied_study_dir = bundle_dir / "study-files"
    if copied_study_dir.exists():
        shutil.rmtree(copied_study_dir)
    shutil.copytree(study_dir, copied_study_dir)

    readme = f"""# {summary["study_name"]}

This folder packages the study outputs for `{summary["study_name"]}`.

## Read This First

- `study-files/study_summary.json`
- `study-files/trials.csv`
- `study-files/pareto_front.csv`

## Summary

- Dataset(s): {", ".join(summary["datasets"])}
- `k`: {summary["k"]}
- Runner: `{summary["runner"].get("runner_resolved_tag", summary["runner"].get("runner_requested_spec", "unknown"))}` @ `{summary["runner"].get("runner_git_sha", "unknown")}`
- Completed trials: {summary["completed_trials"]}
- Stop reason: {summary.get("stop_reason")}
- Hypervolume reference: runtime=`{summary["hypervolume_reference"]["runtime_ref"]}`, utility=`{summary["hypervolume_reference"]["utility_ref"]}`

## Attached Artifacts

- `study-files/`
  - full copied study directory
"""
    (bundle_dir / "README.md").write_text(readme)
    return bundle_dir


def main() -> int:
    args = parse_args()
    artifacts_root = Path(args.artifacts_dir)
    study_dir = artifacts_root / args.study_name
    study_dir.mkdir(parents=True, exist_ok=True)
    artifact_store_dir = Path(args.artifact_store_dir) if args.artifact_store_dir else (artifacts_root / "_dashboard_artifacts")
    artifact_store_dir.mkdir(parents=True, exist_ok=True)
    artifact_store = FileSystemArtifactStore(artifact_store_dir)
    runner_jar = build_runner_jar(args, study_dir)
    runner_resolution_path = study_dir / "runner" / "resolution.json"
    runner_resolution = (
        json.loads(runner_resolution_path.read_text()) if runner_resolution_path.exists() else {"runner_output_jar": str(runner_jar)}
    )

    storage = args.storage or f"sqlite:///{(study_dir / 'study.sqlite3').resolve()}"
    sampler = optuna.samplers.NSGAIISampler(seed=42)
    stopper = HypervolumeStagnationStopper(
        min_trials=args.min_trials_before_stop,
        patience=args.stop_patience,
        min_improvement=args.stop_min_improvement,
        runtime_ref=args.hypervolume_runtime_ref,
        utility_ref=args.hypervolume_utility_ref,
        debug=args.hypervolume_debug,
        debug_log_path=study_dir / "hypervolume_debug_live.csv" if args.hypervolume_debug else None,
    )

    study = optuna.create_study(
        study_name=args.study_name,
        storage=storage,
        load_if_exists=True,
        directions=["minimize", "maximize"],
        sampler=sampler,
    )

    objective = lambda trial: trial_objective(trial, args, study_dir, runner_jar, artifact_store)
    started = time.monotonic()
    while completed_trial_count(study) < args.max_trials:
        remaining_timeout = None
        if args.timeout_seconds is not None:
            elapsed = time.monotonic() - started
            remaining_timeout = max(0.0, args.timeout_seconds - elapsed)
            if remaining_timeout <= 0.0:
                break

        study.optimize(
            objective,
            n_trials=1,
            timeout=remaining_timeout,
            callbacks=[stopper],
        )
        if study.user_attrs.get("stop_reason") is not None:
            break

    write_trials_csv(study, study_dir / "trials.csv")
    plot_study_outputs(study, study_dir)

    summary = {
        "study_name": args.study_name,
        "storage": storage,
        "datasets": args.dataset,
        "k": args.k,
        "runner": runner_resolution,
        "hypervolume_reference": {
            "runtime_ref": args.hypervolume_runtime_ref,
            "utility_ref": args.hypervolume_utility_ref,
        },
        "completed_trials": completed_trial_count(study),
        "stop_reason": study.user_attrs.get("stop_reason"),
        "best_trials": [
            {
                "number": trial.number,
                "values": trial.values,
                "params": trial.params,
                "artifact_dir": trial.user_attrs.get("artifact_dir"),
            }
            for trial in study.best_trials
        ],
    }
    (study_dir / "study_summary.json").write_text(json.dumps(summary, indent=2))
    update_study_dashboard_note(study, study_dir, summary, artifact_store)
    bundle_dir = write_study_bundle(study_dir, summary)
    study.set_user_attr("study_bundle_dir", str(bundle_dir))
    study.set_user_attr("artifact_store_dir", str(artifact_store_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
