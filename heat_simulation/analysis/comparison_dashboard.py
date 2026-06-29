"""Comparison dashboard: multi-scenario side-by-side analysis.

This module provides functions to compare multiple simulation scenarios,
build KPI comparison tables, and generate matplotlib comparison figures.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from heat_simulation.core.simulation_core import SimulationConfig, run_heat_simulation
from heat_simulation.analysis.industrial_analysis import compute_industrial_kpis


# ---------------------------------------------------------------------------
# Core comparison functions
# ---------------------------------------------------------------------------

def compare_scenarios(
    scenario_configs: Dict[str, SimulationConfig],
) -> Dict[str, dict]:
    """Run each named scenario and return a mapping of name -> result dict.

    Args:
        scenario_configs: Dict of scenario_name -> SimulationConfig.

    Returns:
        Dict of scenario_name -> run_heat_simulation result dict.

    Raises:
        ValueError: If scenario_configs is empty.
    """
    if not scenario_configs:
        raise ValueError("scenario_configs must contain at least one entry")

    results: Dict[str, dict] = {}
    for name, cfg in scenario_configs.items():
        results[name] = run_heat_simulation(cfg)
    return results


def build_kpi_comparison_df(
    scenario_results: Dict[str, dict],
    kpi_keys: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Build a DataFrame comparing KPIs across multiple scenarios.

    Args:
        scenario_results: Output of compare_scenarios().
        kpi_keys: KPI columns to include. Defaults to all available KPIs.

    Returns:
        DataFrame indexed by scenario name with KPI columns.
    """
    rows = []
    for name, sim_result in scenario_results.items():
        kpis = compute_industrial_kpis(sim_result)
        row = {"scenario": name}
        row.update(kpis)
        rows.append(row)

    df = pd.DataFrame(rows).set_index("scenario")

    if kpi_keys is not None:
        missing = [k for k in kpi_keys if k not in df.columns]
        if missing:
            raise KeyError(f"KPI keys not found: {missing}")
        df = df[kpi_keys]

    return df


def rank_scenarios(
    kpi_df: pd.DataFrame,
    metric: str,
    ascending: bool = False,
) -> pd.DataFrame:
    """Return a ranked copy of the KPI DataFrame sorted by the given metric.

    Args:
        kpi_df: Output of build_kpi_comparison_df().
        metric: Column name to sort by.
        ascending: Sort order (default False = best first for higher-is-better).

    Returns:
        Sorted DataFrame with an additional 'rank' column.
    """
    if metric not in kpi_df.columns:
        raise KeyError(f"Metric '{metric}' not found in DataFrame columns")
    ranked = kpi_df.sort_values(metric, ascending=ascending).copy()
    ranked.insert(0, "rank", range(1, len(ranked) + 1))
    return ranked


# ---------------------------------------------------------------------------
# Chart helpers
# ---------------------------------------------------------------------------

_TEMP_KEYS = ["T_g", "T_PV", "T_b", "T_hp", "T_fluid", "T_tube", "T_water"]


def build_temperature_comparison_chart(
    scenario_results: Dict[str, dict],
    curve_key: str = "T_water",
    figsize: tuple = (12, 5),
) -> plt.Figure:
    """Create a line chart overlaying one temperature curve across all scenarios.

    Args:
        scenario_results: Output of compare_scenarios().
        curve_key: Which temperature curve to overlay (e.g. "T_water").
        figsize: Matplotlib figure size.

    Returns:
        Matplotlib Figure.
    """
    if curve_key not in _TEMP_KEYS:
        raise ValueError(f"curve_key must be one of {_TEMP_KEYS}")

    fig, ax = plt.subplots(figsize=figsize)
    for name, sim_result in scenario_results.items():
        labels = sim_result["time_labels"]
        curve = sim_result["curves"][curve_key]
        ax.plot(labels, curve, marker="o", label=name, linewidth=2)

    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"Scenario Comparison — {curve_key}")
    ax.legend()
    ax.grid(alpha=0.2)
    plt.tight_layout()
    return fig


def build_kpi_bar_chart(
    kpi_df: pd.DataFrame,
    metric: str,
    figsize: tuple = (10, 4),
) -> plt.Figure:
    """Create a horizontal bar chart comparing one KPI across scenarios.

    Args:
        kpi_df: Output of build_kpi_comparison_df().
        metric: KPI column to visualise.
        figsize: Matplotlib figure size.

    Returns:
        Matplotlib Figure.
    """
    if metric not in kpi_df.columns:
        raise KeyError(f"Metric '{metric}' not found")

    fig, ax = plt.subplots(figsize=figsize)
    values = kpi_df[metric]
    colors = plt.cm.tab10(np.linspace(0, 0.8, len(values)))  # type: ignore[attr-defined]
    ax.barh(values.index.tolist(), values.values, color=colors)
    ax.set_xlabel(metric.replace("_", " "))
    ax.set_title(f"Scenario Comparison — {metric}")
    ax.invert_yaxis()
    plt.tight_layout()
    return fig


def build_multi_kpi_heatmap(
    kpi_df: pd.DataFrame,
    kpi_keys: Optional[List[str]] = None,
    figsize: tuple = (14, 5),
) -> plt.Figure:
    """Create a heatmap (normalised) of multiple KPIs across scenarios.

    Each column is min-max normalised so different scales are comparable.

    Args:
        kpi_df: Output of build_kpi_comparison_df().
        kpi_keys: Subset of KPI columns; defaults to all numeric columns.
        figsize: Matplotlib figure size.

    Returns:
        Matplotlib Figure.
    """
    numeric_df = kpi_df.select_dtypes(include=[np.number])
    if kpi_keys is not None:
        numeric_df = numeric_df[kpi_keys]

    if numeric_df.empty:
        raise ValueError("No numeric KPI columns available for heatmap")

    # Min-max normalisation per column
    col_min = numeric_df.min()
    col_max = numeric_df.max()
    denom = (col_max - col_min).replace(0, 1)
    normalised = (numeric_df - col_min) / denom

    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(normalised.values, aspect="auto", cmap="YlOrRd", vmin=0, vmax=1)
    ax.set_xticks(range(len(normalised.columns)))
    ax.set_xticklabels([c.replace("_", "\n") for c in normalised.columns], fontsize=8)
    ax.set_yticks(range(len(normalised.index)))
    ax.set_yticklabels(normalised.index.tolist())
    plt.colorbar(im, ax=ax, label="Normalised value")
    ax.set_title("KPI Heatmap (normalised per metric)")
    plt.tight_layout()
    return fig


def save_comparison_figure(fig: plt.Figure, path: str) -> str:
    """Save a matplotlib figure to disk and return the path."""
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
