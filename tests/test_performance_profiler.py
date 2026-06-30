"""Tests for heat_simulation.analysis.performance_profiler."""
import pytest
import pandas as pd

from heat_simulation.core.simulation_core import SimulationConfig
from heat_simulation.analysis.performance_profiler import (
    ProfileResult,
    estimate_memory_kb,
    profile_single_run,
    profile_scaling,
    compute_scaling_metrics,
    generate_profiling_report,
)


@pytest.fixture
def small_config():
    return SimulationConfig(
        initial_temp_k=293.15,
        ambient_temp_k=300.15,
        wind_speed=1.0,
        start_hour=9,
        end_hour=16,
        time_points=8,
    )


class TestEstimateMemoryKb:
    def test_positive_result(self):
        result = estimate_memory_kb(100)
        assert result > 0

    def test_scales_with_points(self):
        small = estimate_memory_kb(10)
        large = estimate_memory_kb(100)
        assert large > small

    def test_known_value(self):
        # 7 * 8 * 8 * 3 / 1024 = 1.3125 KB
        result = estimate_memory_kb(8)
        assert result == pytest.approx(1.3125)


class TestProfileSingleRun:
    def test_returns_profile_result(self, small_config):
        result = profile_single_run(small_config, label="test")
        assert isinstance(result, ProfileResult)
        assert result.config_label == "test"
        assert result.time_points == 8
        assert result.elapsed_seconds > 0
        assert result.throughput_points_per_sec > 0
        assert result.peak_memory_estimate_kb > 0

    def test_default_label(self, small_config):
        result = profile_single_run(small_config)
        assert result.config_label == "default"


class TestProfileScaling:
    def test_returns_dataframe(self, small_config):
        df = profile_scaling(small_config, point_counts=[8, 16])
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "elapsed_seconds" in df.columns
        assert "throughput_points_per_sec" in df.columns

    def test_default_point_counts(self, small_config):
        df = profile_scaling(small_config)
        assert len(df) == 5  # default [8, 16, 32, 64, 128]

    def test_custom_point_counts(self, small_config):
        df = profile_scaling(small_config, point_counts=[4, 8, 12])
        assert len(df) == 3
        assert df.iloc[0]["time_points"] == 4
        assert df.iloc[2]["time_points"] == 12


class TestComputeScalingMetrics:
    def test_basic_metrics(self, small_config):
        df = profile_scaling(small_config, point_counts=[8, 16, 32])
        metrics = compute_scaling_metrics(df)
        assert "scaling_factor" in metrics
        assert "efficiency_score" in metrics
        assert "fastest_config" in metrics
        assert "slowest_config" in metrics
        assert metrics["scaling_factor"] > 0
        assert 0 < metrics["efficiency_score"] <= 1.0

    def test_empty_df(self):
        metrics = compute_scaling_metrics(pd.DataFrame())
        assert metrics["scaling_factor"] == 1.0
        assert metrics["efficiency_score"] == 1.0

    def test_single_row_df(self):
        df = pd.DataFrame([{
            "config_label": "n=8",
            "time_points": 8,
            "elapsed_seconds": 0.1,
            "throughput_points_per_sec": 80.0,
            "peak_memory_estimate_kb": 1.0,
        }])
        metrics = compute_scaling_metrics(df)
        assert metrics["scaling_factor"] == 1.0


class TestGenerateProfilingReport:
    def test_full_report(self, small_config):
        report = generate_profiling_report(small_config, point_counts=[8, 16])
        assert "profile_df" in report
        assert "scaling_metrics" in report
        assert "summary_text" in report
        assert len(report["profile_df"]) == 2
        assert "Profiled 2" in report["summary_text"]

    def test_summary_mentions_efficiency(self, small_config):
        report = generate_profiling_report(small_config, point_counts=[8, 16, 32])
        assert "Efficiency" in report["summary_text"]
        assert "Fastest" in report["summary_text"]
