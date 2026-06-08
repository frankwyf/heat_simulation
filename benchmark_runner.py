import argparse
import json
import os
import random
import statistics
import time
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from GA import GA_Individual, GA_optimizer
from PSO import PSO
import SA as sa_module


DEFAULT_PROFILE_SETTINGS = {
    "quick": {
        "ga_population": 140,
        "ga_nochange_iter": 120,
        "pso_population": 120,
        "pso_iterations": 70,
        "sa_num_iter": 2500,
        "sa_t_max": 10,
        "sa_cooling_rate": 0.62,
        "sa_max_outer_iter": 320,
    },
    "standard": {
        "ga_population": 180,
        "ga_nochange_iter": 150,
        "pso_population": 220,
        "pso_iterations": 100,
        "sa_num_iter": 4500,
        "sa_t_max": 14,
        "sa_cooling_rate": 0.58,
        "sa_max_outer_iter": 420,
    },
}

REQUIRED_PROFILE_KEYS = [
    "ga_population",
    "ga_nochange_iter",
    "pso_population",
    "pso_iterations",
    "sa_num_iter",
    "sa_t_max",
    "sa_cooling_rate",
    "sa_max_outer_iter",
]


@dataclass
class RunResult:
    algorithm: str
    trial: int
    best_objective: float
    elapsed_seconds: float


def _safe_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)


def _load_profiles(config_path: str) -> dict:
    if not os.path.exists(config_path):
        return DEFAULT_PROFILE_SETTINGS

    with open(config_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    merged = dict(DEFAULT_PROFILE_SETTINGS)
    for name, values in loaded.items():
        base = dict(DEFAULT_PROFILE_SETTINGS.get(name, {}))
        base.update(values)
        merged[name] = base
    return merged


def _validate_profile_cfg(profile_name: str, profile_cfg: dict):
    missing = [k for k in REQUIRED_PROFILE_KEYS if k not in profile_cfg]
    if missing:
        raise ValueError(
            f"Profile '{profile_name}' missing required keys: {', '.join(missing)}. "
            "Please update benchmark_profiles.json."
        )


def _run_ga_once(max_iteration: int, seed: int, profile_cfg: dict, max_runtime_s: float | None = None) -> RunResult:
    _safe_seed(seed)
    optimizer = GA_optimizer(
        GA_Individual,
        N=int(profile_cfg["ga_population"]),
        C=0.95,
        M=0.7,
        nochange_iter=int(profile_cfg["ga_nochange_iter"]),
        last_generation_left=0.5,
        history_convert=lambda x: x,
    )
    t0 = time.time()
    _, fitness_history = optimizer.optimize(max_iteration=max_iteration, verbose=False, max_wall_time_s=max_runtime_s)
    elapsed = time.time() - t0
    return RunResult("GA", 0, float(min(fitness_history)), elapsed)


def _run_pso_once(seed: int, profile_cfg: dict, max_runtime_s: float | None = None) -> RunResult:
    _safe_seed(seed)
    pop = int(profile_cfg["pso_population"])
    iterations = int(profile_cfg["pso_iterations"])
    pso = PSO(pop=pop, iterations=iterations, verbose=False, show_plot=False)
    t0 = time.time()
    elapsed = pso.run(max_wall_time_s=max_runtime_s)
    if elapsed <= 0:
        elapsed = time.time() - t0
    best = float(pso.gbest_hist[-1]) if pso.gbest_hist else float("inf")
    return RunResult("PSO", 0, best, float(elapsed))


def _run_sa_once(seed: int, profile_cfg: dict, max_runtime_s: float | None = None) -> RunResult:
    _safe_seed(seed)
    sa_kwargs = {
        "num_iter": int(profile_cfg["sa_num_iter"]),
        "t_max": float(profile_cfg["sa_t_max"]),
        "cooling_rate": float(profile_cfg["sa_cooling_rate"]),
        "max_outer_iter": int(profile_cfg["sa_max_outer_iter"]),
    }
    t0 = time.time()
    best, _, elapsed = sa_module.main(show_plot=False, verbose=False, max_wall_time_s=max_runtime_s, **sa_kwargs)
    if elapsed <= 0:
        elapsed = time.time() - t0
    return RunResult("SA", 0, float(best), float(elapsed))


def _summary_table(results: List[RunResult]) -> pd.DataFrame:
    grouped: Dict[str, List[RunResult]] = {}
    for r in results:
        grouped.setdefault(r.algorithm, []).append(r)

    rows = []
    for algo, rs in grouped.items():
        obj_values = [x.best_objective for x in rs]
        t_values = [x.elapsed_seconds for x in rs]
        rows.append(
            {
                "algorithm": algo,
                "runs": len(rs),
                "best_objective_min": min(obj_values),
                "best_objective_mean": statistics.mean(obj_values),
                "best_objective_std": statistics.pstdev(obj_values) if len(obj_values) > 1 else 0.0,
                "time_mean_s": statistics.mean(t_values),
                "time_max_s": max(t_values),
            }
        )
    return pd.DataFrame(rows).sort_values("best_objective_min", ascending=True)


def _plot_report(results_df: pd.DataFrame, out_png: str):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

    axes[0].bar(results_df["algorithm"], results_df["best_objective_min"], color=["#1f77b4", "#ff7f0e", "#2ca02c"])
    axes[0].set_title("Objective Comparison (Lower is Better)")
    axes[0].set_ylabel("Best Objective")
    axes[0].grid(alpha=0.2)

    axes[1].bar(results_df["algorithm"], results_df["time_mean_s"], color=["#1f77b4", "#ff7f0e", "#2ca02c"])
    axes[1].set_title("Runtime Comparison")
    axes[1].set_ylabel("Mean Time (s)")
    axes[1].grid(alpha=0.2)

    plt.tight_layout()
    plt.savefig(out_png, dpi=180, bbox_inches="tight")
    plt.close(fig)


def run_benchmark(
    runs_per_algo: int,
    max_iteration_ga: int,
    base_seed: int = 42,
    profile: str = "quick",
    max_runtime_s: float | None = None,
    profile_config_path: str = "benchmark_profiles.json",
) -> Dict[str, str]:
    os.makedirs("reports", exist_ok=True)

    warnings.filterwarnings("ignore", message="FigureCanvasAgg is non-interactive")
    profiles = _load_profiles(profile_config_path)
    if profile not in profiles:
        raise ValueError(f"Unknown profile '{profile}'. Available: {', '.join(sorted(profiles.keys()))}")
    profile_cfg = profiles[profile]
    _validate_profile_cfg(profile, profile_cfg)

    runners: Dict[str, Callable[[int], RunResult]] = {
        "GA": lambda seed: _run_ga_once(max_iteration=max_iteration_ga, seed=seed, profile_cfg=profile_cfg, max_runtime_s=max_runtime_s),
        "PSO": lambda seed: _run_pso_once(seed=seed, profile_cfg=profile_cfg, max_runtime_s=max_runtime_s),
        "SA": lambda seed: _run_sa_once(seed=seed, profile_cfg=profile_cfg, max_runtime_s=max_runtime_s),
    }

    all_results: List[RunResult] = []
    algo_seed_offset = {"GA": 1000, "PSO": 2000, "SA": 3000}
    for algo_name, runner in runners.items():
        for i in range(runs_per_algo):
            seed = base_seed + i + algo_seed_offset[algo_name]
            result = runner(seed)
            result.trial = i + 1
            all_results.append(result)

    details_df = pd.DataFrame([asdict(x) for x in all_results])
    summary_df = _summary_table(all_results)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    details_csv = f"reports/benchmark_details_{ts}.csv"
    summary_csv = f"reports/benchmark_summary_{ts}.csv"
    plot_png = f"reports/benchmark_chart_{ts}.png"
    meta_json = f"reports/benchmark_meta_{ts}.json"

    details_df.to_csv(details_csv, index=False)
    summary_df.to_csv(summary_csv, index=False)
    _plot_report(summary_df, plot_png)

    with open(meta_json, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.now().isoformat(),
                "runs_per_algo": runs_per_algo,
                "max_iteration_ga": max_iteration_ga,
                "profile": profile,
                "profile_settings": profile_cfg,
                "max_runtime_s": max_runtime_s,
                "best_algorithm": summary_df.iloc[0]["algorithm"] if not summary_df.empty else None,
                "artifacts": {
                    "details_csv": details_csv,
                    "summary_csv": summary_csv,
                    "plot_png": plot_png,
                },
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    return {
        "details_csv": details_csv,
        "summary_csv": summary_csv,
        "plot_png": plot_png,
        "meta_json": meta_json,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Run local benchmark for GA/PSO/SA and generate report artifacts.")
    parser.add_argument("--runs", type=int, default=2, help="Runs per algorithm.")
    parser.add_argument("--ga-iter", type=int, default=200, help="Max GA iterations for each run.")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed.")
    parser.add_argument("--profile", choices=["quick", "standard"], default="quick", help="quick for stable local checks, standard for heavier runs.")
    parser.add_argument("--max-runtime-s", type=float, default=12.0, help="Optional per-algorithm wall-time cap in seconds.")
    parser.add_argument("--profile-config", default="benchmark_profiles.json", help="Path to benchmark profile config file.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    artifacts = run_benchmark(
        runs_per_algo=max(1, args.runs),
        max_iteration_ga=max(50, args.ga_iter),
        base_seed=args.seed,
        profile=args.profile,
        max_runtime_s=args.max_runtime_s if args.max_runtime_s > 0 else None,
        profile_config_path=args.profile_config,
    )
    print("Benchmark finished. Artifacts:")
    for k, v in artifacts.items():
        print(f"- {k}: {v}")
