"""Tests for heat_simulation.analysis.comparison_dashboard."""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from heat_simulation.core.simulation_core import DEFAULT_IRRADIANCE, SimulationConfig
from heat_simulation.analysis.comparison_dashboard import (
    compare_scenarios,
    build_kpi_comparison_df,
    rank_scenarios,
    build_temperature_comparison_chart,
    build_kpi_bar_chart,
    build_multi_kpi_heatmap,
    save_comparison_figure,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def two_scenarios():
    """Two minimal scenarios for fast tests."""
    return {
        "Low Wind": SimulationConfig(
            time_points=4,
            irradiance_values=DEFAULT_IRRADIANCE[:4],
            wind_speed=1.0,
        ),
        "High Wind": SimulationConfig(
            time_points=4,
            irradiance_values=DEFAULT_IRRADIANCE[:4],
            wind_speed=6.0,
        ),
    }


@pytest.fixture(scope="module")
def scenario_results(two_scenarios):
    return compare_scenarios(two_scenarios)


@pytest.fixture(scope="module")
def kpi_df(scenario_results):
    return build_kpi_comparison_df(scenario_results)


# ---------------------------------------------------------------------------
# compare_scenarios
# ---------------------------------------------------------------------------

class TestCompareScenarios:
    def test_returns_dict(self, scenario_results):
        assert isinstance(scenario_results, dict)

    def test_correct_keys(self, scenario_results, two_scenarios):
        assert set(scenario_results.keys()) == set(two_scenarios.keys())

    def test_each_result_has_curves(self, scenario_results):
        for name, res in scenario_results.items():
            assert "curves" in res, f"Missing 'curves' in result for {name}"

    def test_empty_input_raises(self):
        with pytest.raises(ValueError, match="at least one entry"):
            compare_scenarios({})

    def test_single_scenario(self):
        cfg = SimulationConfig(time_points=4, irradiance_values=DEFAULT_IRRADIANCE[:4])
        results = compare_scenarios({"only": cfg})
        assert "only" in results


# ---------------------------------------------------------------------------
# build_kpi_comparison_df
# ---------------------------------------------------------------------------

class TestBuildKpiComparisonDf:
    def test_returns_dataframe(self, kpi_df):
        assert isinstance(kpi_df, pd.DataFrame)

    def test_index_is_scenario_names(self, kpi_df, two_scenarios):
        assert set(kpi_df.index) == set(two_scenarios.keys())

    def test_all_kpi_columns_present(self, kpi_df):
        expected = {
            "peak_pv_temp_c",
            "water_temperature_gain_c",
            "thermal_uniformity_index",
            "energy_capture_proxy_wh_m2",
        }
        assert expected.issubset(set(kpi_df.columns))

    def test_kpi_keys_filter(self, scenario_results):
        keys = ["peak_pv_temp_c", "final_water_temp_c"]
        df = build_kpi_comparison_df(scenario_results, kpi_keys=keys)
        assert list(df.columns) == keys

    def test_invalid_kpi_key_raises(self, scenario_results):
        with pytest.raises(KeyError, match="not_a_kpi"):
            build_kpi_comparison_df(scenario_results, kpi_keys=["not_a_kpi"])

    def test_values_are_numeric(self, kpi_df):
        assert kpi_df.select_dtypes(include=[np.number]).shape == kpi_df.shape


# ---------------------------------------------------------------------------
# rank_scenarios
# ---------------------------------------------------------------------------

class TestRankScenarios:
    def test_returns_dataframe(self, kpi_df):
        ranked = rank_scenarios(kpi_df, "water_temperature_gain_c")
        assert isinstance(ranked, pd.DataFrame)

    def test_has_rank_column(self, kpi_df):
        ranked = rank_scenarios(kpi_df, "water_temperature_gain_c")
        assert "rank" in ranked.columns

    def test_rank_starts_at_one(self, kpi_df):
        ranked = rank_scenarios(kpi_df, "water_temperature_gain_c")
        assert ranked["rank"].iloc[0] == 1

    def test_ascending_sort(self, kpi_df):
        ranked = rank_scenarios(kpi_df, "peak_pv_temp_c", ascending=True)
        vals = ranked["peak_pv_temp_c"].values
        assert vals[0] <= vals[-1]

    def test_invalid_metric_raises(self, kpi_df):
        with pytest.raises(KeyError, match="not_exist"):
            rank_scenarios(kpi_df, "not_exist")


# ---------------------------------------------------------------------------
# build_temperature_comparison_chart
# ---------------------------------------------------------------------------

class TestBuildTemperatureComparisonChart:
    def test_returns_figure(self, scenario_results):
        fig = build_temperature_comparison_chart(scenario_results)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_custom_curve_key(self, scenario_results):
        fig = build_temperature_comparison_chart(scenario_results, curve_key="T_PV")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_invalid_curve_key_raises(self, scenario_results):
        with pytest.raises(ValueError, match="curve_key"):
            build_temperature_comparison_chart(scenario_results, curve_key="T_invalid")

    @pytest.mark.parametrize("curve_key", ["T_g", "T_PV", "T_water", "T_fluid"])
    def test_all_valid_curve_keys(self, scenario_results, curve_key):
        fig = build_temperature_comparison_chart(scenario_results, curve_key=curve_key)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# build_kpi_bar_chart
# ---------------------------------------------------------------------------

class TestBuildKpiBarChart:
    def test_returns_figure(self, kpi_df):
        fig = build_kpi_bar_chart(kpi_df, "water_temperature_gain_c")
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_invalid_metric_raises(self, kpi_df):
        with pytest.raises(KeyError, match="not_a_metric"):
            build_kpi_bar_chart(kpi_df, "not_a_metric")


# ---------------------------------------------------------------------------
# build_multi_kpi_heatmap
# ---------------------------------------------------------------------------

class TestBuildMultiKpiHeatmap:
    def test_returns_figure(self, kpi_df):
        fig = build_multi_kpi_heatmap(kpi_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_subset_kpi_keys(self, kpi_df):
        keys = ["peak_pv_temp_c", "water_temperature_gain_c"]
        fig = build_multi_kpi_heatmap(kpi_df, kpi_keys=keys)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# save_comparison_figure
# ---------------------------------------------------------------------------

class TestSaveComparisonFigure:
    def test_saves_png(self, scenario_results, tmp_path):
        fig = build_temperature_comparison_chart(scenario_results)
        out = str(tmp_path / "chart.png")
        returned_path = save_comparison_figure(fig, out)
        assert os.path.exists(out)
        assert returned_path == out

    def test_returns_path_string(self, scenario_results, tmp_path):
        fig = build_temperature_comparison_chart(scenario_results)
        path = str(tmp_path / "out.png")
        result = save_comparison_figure(fig, path)
        assert isinstance(result, str)
