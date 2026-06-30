"""Simulation Performance Profiler.

Measures execution time, memory footprint, and throughput across
different configuration sizes. Produces profiling reports for
industrial performance benchmarking and capacity planning.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from heat_simulation.core.simulation_core import SimulationConfig, run_heat_simulation


@dataclass
class ProfileResult:
    config_label: str
    time_points: int
    elapsed_seconds: float
    throughput_points_per_sec: float
    peak_memory_estimate_kb: float


def estimate_memory_kb(time_points: int) -> float:
    """Estimate memory usage based on simulation array sizes.

    The simulation produces ~7 curves of length time_points (float64 = 8 bytes each).
    Plus ODE solver intermediate arrays.
    """
    # 7 curves * time_points * 8 bytes, plus 3x overhead for ODE solver
    return (7 * time_points * 8 * 3) / 1024.0


def profile_single_run(config: SimulationConfig, label: str = "default") -> ProfileResult:
    """Profile a single simulation run."""
    t0 = time.perf_counter()
    _ = run_heat_simulation(config)
    elapsed = time.perf_counter() - t0

    throughput = config.time_points / elapsed if elapsed > 0 else float("inf")
    memory_est = estimate_memory_kb(config.time_points)

    return ProfileResult(
        config_label=label,
        time_points=config.time_points,
        elapsed_seconds=elapsed,
        throughput_points_per_sec=throughput,
        peak_memory_estimate_kb=memory_est,
    )


def profile_scaling(
    base_config: SimulationConfig,
    point_counts: List[int] = None,
) -> pd.DataFrame:
    """Profile simulation at different time_points to measure scaling behavior.

    Returns DataFrame with columns: config_label, time_points, elapsed_seconds,
    throughput_points_per_sec, peak_memory_estimate_kb.
    """
    if point_counts is None:
        point_counts = [8, 16, 32, 64, 128]

    results: List[Dict[str, Any]] = []
    for n in point_counts:
        from dataclasses import replace
        from heat_simulation.core.simulation_core import DEFAULT_IRRADIANCE
        # Interpolate irradiance to match new time_points
        base_irr = list(base_config.irradiance_values) if base_config.irradiance_values else list(DEFAULT_IRRADIANCE)
        if len(base_irr) != n:
            irr_arr = np.interp(
                np.linspace(0, 1, n),
                np.linspace(0, 1, len(base_irr)),
                base_irr,
            ).tolist()
        else:
            irr_arr = base_irr
        cfg = replace(base_config, time_points=n, irradiance_values=irr_arr)
        profile = profile_single_run(cfg, label=f"n={n}")
        results.append(asdict(profile))

    return pd.DataFrame(results)


def compute_scaling_metrics(profile_df: pd.DataFrame) -> Dict[str, Any]:
    """Compute scaling efficiency metrics from profiling data.

    Returns scaling_factor (time growth relative to linear) and
    efficiency_score (1.0 = perfect linear scaling).
    """
    if profile_df.empty or len(profile_df) < 2:
        return {
            "scaling_factor": 1.0,
            "efficiency_score": 1.0,
            "fastest_config": None,
            "slowest_config": None,
        }

    times = profile_df["elapsed_seconds"].to_numpy(dtype=float)
    points = profile_df["time_points"].to_numpy(dtype=float)

    # Linear scaling: time should grow proportionally with time_points
    # scaling_factor > 1 means worse-than-linear, < 1 means better
    normalized_times = times / times[0]
    normalized_points = points / points[0]

    # Average ratio of time growth to point growth
    ratios = normalized_times[1:] / normalized_points[1:]
    scaling_factor = float(np.mean(ratios))
    efficiency_score = float(1.0 / max(scaling_factor, 0.01))

    fastest_idx = int(np.argmax(profile_df["throughput_points_per_sec"].to_numpy()))
    slowest_idx = int(np.argmin(profile_df["throughput_points_per_sec"].to_numpy()))

    return {
        "scaling_factor": round(scaling_factor, 4),
        "efficiency_score": round(min(efficiency_score, 1.0), 4),
        "fastest_config": profile_df.iloc[fastest_idx]["config_label"],
        "slowest_config": profile_df.iloc[slowest_idx]["config_label"],
        "total_profiling_time_s": round(float(np.sum(times)), 3),
    }


def generate_profiling_report(
    base_config: SimulationConfig,
    point_counts: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Generate a complete profiling report.

    Returns dict with profile_df, scaling_metrics, and summary_text.
    """
    profile_df = profile_scaling(base_config, point_counts)
    metrics = compute_scaling_metrics(profile_df)

    summary = (
        f"Profiled {len(profile_df)} configurations. "
        f"Scaling factor: {metrics['scaling_factor']} "
        f"(1.0 = linear). Efficiency: {metrics['efficiency_score']}. "
        f"Fastest: {metrics['fastest_config']}."
    )

    return {
        "profile_df": profile_df,
        "scaling_metrics": metrics,
        "summary_text": summary,
    }
