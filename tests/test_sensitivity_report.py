"""Tests for heat_simulation.analysis.sensitivity_report."""
import os

import numpy as np
import pandas as pd
import pytest

from heat_simulation.analysis.sensitivity_report import (
    compute_sensitivity_indices,
    build_tornado_chart,
    build_influence_ranking,
    generate_sensitivity_report,
    _categorize_impact,
)


@pytest.fixture
def sample_sensitivity_df():
    """Simulated one-factor sensitivity results."""
    rows = []
    for param in ["ambient_temp_k", "wind_speed", "irradiance_scale"]:
        for delta in [-0.2, -0.1, 0.0, 0.1, 0.2]:
            # Simulate different sensitivity strengths
            if param == "ambient_temp_k":
                value = 10.0 + delta * 5.0  # moderate sensitivity
            elif param == "wind_speed":
                value = 10.0 + delta * 1.0  # low sensitivity
            else:
                value = 10.0 + delta * 15.0  # high sensitivity
            rows.append({
                "parameter": param,
                "delta_ratio": delta,
                "metric_key": "water_temperature_gain_c",
                "metric_value": value,
                "peak_pv_temp_c": 55.0 + delta * 3,
            })
    return pd.DataFrame(rows)


class TestComputeSensitivityIndices:
    def test_basic_computation(self, sample_sensitivity_df):
        result = compute_sensitivity_indices(sample_sensitivity_df, baseline_value=10.0)
        assert len(result) == 3
        assert "sensitivity_index" in result.columns
        assert "direction" in result.columns
        assert "parameter" in result.columns

    def test_sorted_by_sensitivity_descending(self, sample_sensitivity_df):
        result = compute_sensitivity_indices(sample_sensitivity_df, baseline_value=10.0)
        indices = result["sensitivity_index"].tolist()
        assert indices == sorted(indices, reverse=True)

    def test_irradiance_most_sensitive(self, sample_sensitivity_df):
        result = compute_sensitivity_indices(sample_sensitivity_df, baseline_value=10.0)
        assert result.iloc[0]["parameter"] == "irradiance_scale"

    def test_wind_least_sensitive(self, sample_sensitivity_df):
        result = compute_sensitivity_indices(sample_sensitivity_df, baseline_value=10.0)
        assert result.iloc[-1]["parameter"] == "wind_speed"

    def test_symmetric_direction(self):
        rows = [
            {"parameter": "x", "delta_ratio": -0.1, "metric_value": 9.0},
            {"parameter": "x", "delta_ratio": 0.0, "metric_value": 10.0},
            {"parameter": "x", "delta_ratio": 0.1, "metric_value": 11.0},
        ]
        df = pd.DataFrame(rows)
        result = compute_sensitivity_indices(df, baseline_value=10.0)
        assert result.iloc[0]["direction"] == "symmetric"

    def test_positive_direction(self):
        rows = [
            {"parameter": "x", "delta_ratio": -0.1, "metric_value": 9.5},
            {"parameter": "x", "delta_ratio": 0.0, "metric_value": 10.0},
            {"parameter": "x", "delta_ratio": 0.1, "metric_value": 12.0},
        ]
        df = pd.DataFrame(rows)
        result = compute_sensitivity_indices(df, baseline_value=10.0)
        assert result.iloc[0]["direction"] == "positive"

    def test_empty_df_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            compute_sensitivity_indices(pd.DataFrame(), baseline_value=10.0)

    def test_zero_baseline(self):
        rows = [
            {"parameter": "x", "delta_ratio": -0.1, "metric_value": -1.0},
            {"parameter": "x", "delta_ratio": 0.0, "metric_value": 0.0},
            {"parameter": "x", "delta_ratio": 0.1, "metric_value": 1.0},
        ]
        df = pd.DataFrame(rows)
        result = compute_sensitivity_indices(df, baseline_value=0.0)
        # Should use raw range when baseline ~0
        assert result.iloc[0]["sensitivity_index"] == pytest.approx(2.0)


class TestBuildTornadoChart:
    def test_returns_figure(self, sample_sensitivity_df):
        indices = compute_sensitivity_indices(sample_sensitivity_df, baseline_value=10.0)
        fig = build_tornado_chart(indices)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_empty_df_returns_figure(self):
        fig = build_tornado_chart(pd.DataFrame(columns=["parameter", "sensitivity_index", "max_deviation", "min_deviation"]))
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_custom_title(self, sample_sensitivity_df):
        indices = compute_sensitivity_indices(sample_sensitivity_df, baseline_value=10.0)
        fig = build_tornado_chart(indices, title="Custom Title")
        ax = fig.axes[0]
        assert "Custom Title" in ax.get_title()
        import matplotlib.pyplot as plt
        plt.close(fig)


class TestBuildInfluenceRanking:
    def test_ranking_structure(self, sample_sensitivity_df):
        indices = compute_sensitivity_indices(sample_sensitivity_df, baseline_value=10.0)
        ranking = build_influence_ranking(indices)
        assert len(ranking) == 3
        assert ranking[0]["rank"] == 1
        assert ranking[1]["rank"] == 2
        assert "impact_category" in ranking[0]

    def test_ranking_order_matches_indices(self, sample_sensitivity_df):
        indices = compute_sensitivity_indices(sample_sensitivity_df, baseline_value=10.0)
        ranking = build_influence_ranking(indices)
        assert ranking[0]["parameter"] == "irradiance_scale"


class TestCategorizeImpact:
    def test_high(self):
        assert _categorize_impact(0.5) == "high"
        assert _categorize_impact(0.3) == "high"

    def test_medium(self):
        assert _categorize_impact(0.2) == "medium"
        assert _categorize_impact(0.1) == "medium"

    def test_low(self):
        assert _categorize_impact(0.05) == "low"
        assert _categorize_impact(0.0) == "low"


class TestGenerateSensitivityReport:
    def test_full_report_without_output(self, sample_sensitivity_df):
        result = generate_sensitivity_report(sample_sensitivity_df, baseline_value=10.0)
        assert "indices_df" in result
        assert "ranking" in result
        assert "summary_text" in result
        assert result["tornado_path"] is None
        assert "irradiance_scale" in result["summary_text"]

    def test_full_report_with_output(self, sample_sensitivity_df, tmp_path):
        result = generate_sensitivity_report(
            sample_sensitivity_df,
            baseline_value=10.0,
            output_dir=str(tmp_path),
        )
        assert result["tornado_path"] is not None
        assert os.path.exists(result["tornado_path"])
        assert result["tornado_path"].endswith(".png")

    def test_summary_mentions_top_parameter(self, sample_sensitivity_df):
        result = generate_sensitivity_report(sample_sensitivity_df, baseline_value=10.0)
        assert "irradiance_scale" in result["summary_text"]
        assert "3" in result["summary_text"]  # Total parameters
