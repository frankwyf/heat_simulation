"""Parameter Sensitivity Analysis Report Generator.

Generates structured sensitivity reports with tornado charts and
parameter influence rankings for industrial decision-making.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def compute_sensitivity_indices(
    sensitivity_df: pd.DataFrame,
    baseline_value: float,
    metric_key: str = "metric_value",
) -> pd.DataFrame:
    """Compute normalized sensitivity indices from one-factor analysis results.

    Returns a DataFrame with columns: parameter, sensitivity_index, direction,
    max_deviation, min_deviation.
    """
    if sensitivity_df.empty:
        raise ValueError("sensitivity_df cannot be empty")

    parameters = sensitivity_df["parameter"].unique()
    rows: List[Dict[str, Any]] = []

    for param in parameters:
        subset = sensitivity_df[sensitivity_df["parameter"] == param]
        values = subset[metric_key].to_numpy(dtype=float)
        deltas = subset["delta_ratio"].to_numpy(dtype=float)

        max_val = float(np.max(values))
        min_val = float(np.min(values))
        max_dev = max_val - baseline_value
        min_dev = min_val - baseline_value

        # Sensitivity index = range / baseline (normalized)
        if abs(baseline_value) > 1e-12:
            sensitivity_index = (max_val - min_val) / abs(baseline_value)
        else:
            sensitivity_index = max_val - min_val

        # Determine dominant direction
        if abs(max_dev) > abs(min_dev):
            direction = "positive"
        elif abs(min_dev) > abs(max_dev):
            direction = "negative"
        else:
            direction = "symmetric"

        rows.append({
            "parameter": param,
            "sensitivity_index": sensitivity_index,
            "direction": direction,
            "max_deviation": max_dev,
            "min_deviation": min_dev,
            "baseline_value": baseline_value,
        })

    result = pd.DataFrame(rows).sort_values("sensitivity_index", ascending=False)
    return result.reset_index(drop=True)


def build_tornado_chart(
    indices_df: pd.DataFrame,
    title: str = "Parameter Sensitivity (Tornado Chart)",
) -> plt.Figure:
    """Build a tornado chart showing positive/negative deviations per parameter."""
    if indices_df.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.set_title(title)
        return fig

    df = indices_df.sort_values("sensitivity_index", ascending=True)
    params = df["parameter"].tolist()
    max_devs = df["max_deviation"].to_numpy(dtype=float)
    min_devs = df["min_deviation"].to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(10, max(4, len(params) * 0.8)))
    y_pos = np.arange(len(params))

    ax.barh(y_pos, max_devs, align="center", color="#2ca02c", alpha=0.8, label="Positive delta")
    ax.barh(y_pos, min_devs, align="center", color="#d62728", alpha=0.8, label="Negative delta")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(params)
    ax.axvline(x=0, color="black", linewidth=0.8)
    ax.set_xlabel("Deviation from Baseline")
    ax.set_title(title)
    ax.legend(loc="lower right")
    ax.grid(alpha=0.2, axis="x")

    plt.tight_layout()
    return fig


def build_influence_ranking(indices_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Return a ranked list of parameter influences for report embedding."""
    ranking = []
    for i, row in indices_df.iterrows():
        ranking.append({
            "rank": len(ranking) + 1,
            "parameter": row["parameter"],
            "sensitivity_index": round(float(row["sensitivity_index"]), 4),
            "direction": row["direction"],
            "impact_category": _categorize_impact(float(row["sensitivity_index"])),
        })
    return ranking


def _categorize_impact(index: float) -> str:
    if index >= 0.3:
        return "high"
    elif index >= 0.1:
        return "medium"
    else:
        return "low"


def generate_sensitivity_report(
    sensitivity_df: pd.DataFrame,
    baseline_value: float,
    metric_key: str = "metric_value",
    output_dir: str | None = None,
) -> Dict[str, Any]:
    """Generate a full sensitivity report package.

    Returns dict with keys: indices_df, ranking, tornado_path (if output_dir given),
    summary_text.
    """
    indices_df = compute_sensitivity_indices(sensitivity_df, baseline_value, metric_key)
    ranking = build_influence_ranking(indices_df)

    tornado_path = None
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        fig = build_tornado_chart(indices_df)
        tornado_path = os.path.join(output_dir, "sensitivity_tornado.png")
        fig.savefig(tornado_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

    # Build summary
    top_param = ranking[0] if ranking else None
    if top_param:
        summary = (
            f"Most influential parameter: {top_param['parameter']} "
            f"(index={top_param['sensitivity_index']}, impact={top_param['impact_category']}). "
            f"Total parameters analyzed: {len(ranking)}."
        )
    else:
        summary = "No parameters analyzed."

    return {
        "indices_df": indices_df,
        "ranking": ranking,
        "tornado_path": tornado_path,
        "summary_text": summary,
        "baseline_value": baseline_value,
    }
