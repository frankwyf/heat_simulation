"""Tests for heat_simulation.analysis.industrial_analysis."""
import numpy as np
import pandas as pd
import pytest

from heat_simulation.core.simulation_core import DEFAULT_IRRADIANCE, SimulationConfig, run_heat_simulation
from heat_simulation.analysis.industrial_analysis import (
    compute_industrial_kpis,
    run_one_factor_sensitivity,
    run_monte_carlo_analysis,
    summarize_monte_carlo,
    build_industrial_analysis_bundle,
    _apply_parameter_delta,
    _safe_curve,
)


# ---------------------------------------------------------------------------
# Helper: minimal synthetic sim_result
# ---------------------------------------------------------------------------

def _make_sim_result(n=4):
    cfg = SimulationConfig(
        time_points=n,
        irradiance_values=DEFAULT_IRRADIANCE[:n],
    )
    return run_heat_simulation(cfg)


# ---------------------------------------------------------------------------
# compute_industrial_kpis
# ---------------------------------------------------------------------------

class TestComputeIndustrialKpis:
    def test_returns_dict(self, small_sim_result):
        kpis = compute_industrial_kpis(small_sim_result)
        assert isinstance(kpis, dict)

    def test_required_kpi_keys(self, typical_kpis):
        expected = {
            "peak_pv_temp_c",
            "peak_glass_temp_c",
            "mean_fluid_temp_c",
            "final_water_temp_c",
            "water_temperature_gain_c",
            "mean_water_heating_rate_c_per_h",
            "max_water_heating_rate_c_per_h",
            "temperature_stability_std_c",
            "thermal_uniformity_index",
            "temperature_risk_hours_above_60c",
            "energy_capture_proxy_wh_m2",
        }
        assert expected.issubset(set(typical_kpis.keys()))

    def test_all_values_are_float(self, typical_kpis):
        for k, v in typical_kpis.items():
            assert isinstance(v, float), f"{k} should be float, got {type(v)}"

    def test_thermal_uniformity_in_range(self, typical_kpis):
        tui = typical_kpis["thermal_uniformity_index"]
        assert 0.0 < tui <= 1.0

    def test_energy_capture_positive(self, typical_kpis):
        assert typical_kpis["energy_capture_proxy_wh_m2"] > 0

    def test_mismatched_irradiance_raises(self, small_sim_result):
        bad = dict(small_sim_result)
        bad["irradiance_values"] = [600.0]  # only 1 element
        with pytest.raises(ValueError, match="irradiance_values length"):
            compute_industrial_kpis(bad)

    def test_too_short_time_axis_raises(self, small_sim_result):
        bad = dict(small_sim_result)
        bad["time_seconds"] = np.array([0.0])  # only 1 point
        with pytest.raises(ValueError, match="one-dimensional array with at least two"):
            compute_industrial_kpis(bad)

    def test_missing_curve_key_raises(self, small_sim_result):
        bad = dict(small_sim_result)
        bad["curves"] = {k: v for k, v in small_sim_result["curves"].items() if k != "T_PV"}
        with pytest.raises(KeyError):
            compute_industrial_kpis(bad)


# ---------------------------------------------------------------------------
# _safe_curve
# ---------------------------------------------------------------------------

class TestSafeCurve:
    def test_returns_array(self):
        curves = {"T_PV": [20.0, 30.0, 40.0]}
        result = _safe_curve(curves, "T_PV")
        assert isinstance(result, np.ndarray)

    def test_missing_key_raises(self):
        with pytest.raises(KeyError, match="T_X"):
            _safe_curve({}, "T_X")


# ---------------------------------------------------------------------------
# _apply_parameter_delta
# ---------------------------------------------------------------------------

class TestApplyParameterDelta:
    def test_ambient_temp_increase(self):
        cfg = SimulationConfig(ambient_temp_k=300.0)
        new_cfg = _apply_parameter_delta(cfg, "ambient_temp_k", 0.1)
        assert new_cfg.ambient_temp_k == pytest.approx(330.0)

    def test_wind_speed_decrease(self):
        cfg = SimulationConfig(wind_speed=2.0)
        new_cfg = _apply_parameter_delta(cfg, "wind_speed", -0.5)
        assert new_cfg.wind_speed == pytest.approx(1.0)

    def test_wind_speed_clamps_to_zero(self):
        cfg = SimulationConfig(wind_speed=1.0)
        new_cfg = _apply_parameter_delta(cfg, "wind_speed", -2.0)
        assert new_cfg.wind_speed == pytest.approx(0.0)

    def test_irradiance_scale(self, small_config):
        new_cfg = _apply_parameter_delta(small_config, "irradiance_scale", 0.1)
        orig = list(small_config.irradiance_values)
        scaled = list(new_cfg.irradiance_values)
        for orig_v, scaled_v in zip(orig, scaled):
            assert scaled_v == pytest.approx(orig_v * 1.1, rel=1e-5)

    def test_irradiance_scale_no_base_values(self):
        cfg = SimulationConfig()  # irradiance_values is None
        new_cfg = _apply_parameter_delta(cfg, "irradiance_scale", 0.2)
        assert new_cfg.irradiance_values is None  # unchanged

    def test_unsupported_parameter_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            _apply_parameter_delta(SimulationConfig(), "unknown_param", 0.1)


# ---------------------------------------------------------------------------
# run_one_factor_sensitivity
# ---------------------------------------------------------------------------

class TestRunOneFactorSensitivity:
    def test_returns_dataframe(self, small_config):
        df = run_one_factor_sensitivity(small_config, deltas=(-0.1, 0.0, 0.1))
        assert isinstance(df, pd.DataFrame)

    def test_has_expected_columns(self, small_config):
        df = run_one_factor_sensitivity(small_config, deltas=(0.0,))
        for col in ("parameter", "delta_ratio", "metric_key", "metric_value", "peak_pv_temp_c"):
            assert col in df.columns

    def test_row_count(self, small_config):
        deltas = (-0.1, 0.0, 0.1)
        df = run_one_factor_sensitivity(small_config, deltas=deltas)
        # 4 parameters × 3 deltas
        assert len(df) == 4 * len(deltas)

    def test_zero_delta_baseline(self, small_config, typical_kpis):
        df = run_one_factor_sensitivity(small_config, deltas=(0.0,), metric_key="water_temperature_gain_c")
        baseline_rows = df[df["delta_ratio"] == 0.0]
        assert not baseline_rows.empty
        for _, row in baseline_rows.iterrows():
            assert isinstance(row["metric_value"], float)


# ---------------------------------------------------------------------------
# run_monte_carlo_analysis
# ---------------------------------------------------------------------------

class TestRunMonteCarloAnalysis:
    def test_returns_dataframe(self, small_config):
        df = run_monte_carlo_analysis(small_config, samples=5, seed=0)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 5

    def test_columns_present(self, small_config):
        df = run_monte_carlo_analysis(small_config, samples=3, seed=1)
        for col in ("sample_id", "ambient_temp_k", "wind_speed", "final_water_temp_c"):
            assert col in df.columns

    def test_seed_reproducibility(self, small_config):
        df1 = run_monte_carlo_analysis(small_config, samples=5, seed=99)
        df2 = run_monte_carlo_analysis(small_config, samples=5, seed=99)
        pd.testing.assert_frame_equal(df1, df2)

    def test_invalid_samples_raises(self, small_config):
        with pytest.raises(ValueError, match="samples must be > 0"):
            run_monte_carlo_analysis(small_config, samples=0)


# ---------------------------------------------------------------------------
# summarize_monte_carlo
# ---------------------------------------------------------------------------

class TestSummarizeMonteCarlo:
    def test_returns_dict(self, small_config):
        df = run_monte_carlo_analysis(small_config, samples=10, seed=7)
        summary = summarize_monte_carlo(df)
        assert isinstance(summary, dict)

    def test_required_summary_keys(self, small_config):
        df = run_monte_carlo_analysis(small_config, samples=10, seed=7)
        summary = summarize_monte_carlo(df)
        for key in ("samples", "final_water_temp_mean_c", "final_water_temp_p05_c",
                    "final_water_temp_p95_c", "water_gain_mean_c", "water_gain_std_c",
                    "risk_hours_mean", "risk_hours_p95"):
            assert key in summary

    def test_p05_le_mean_le_p95(self, small_config):
        df = run_monte_carlo_analysis(small_config, samples=20, seed=3)
        s = summarize_monte_carlo(df)
        assert s["final_water_temp_p05_c"] <= s["final_water_temp_mean_c"] <= s["final_water_temp_p95_c"]

    def test_empty_df_raises(self):
        with pytest.raises(ValueError):
            summarize_monte_carlo(pd.DataFrame())


# ---------------------------------------------------------------------------
# build_industrial_analysis_bundle
# ---------------------------------------------------------------------------

class TestBuildIndustrialAnalysisBundle:
    def test_baseline_only(self, small_config):
        bundle = build_industrial_analysis_bundle(
            small_config, run_sensitivity=False, monte_carlo_samples=0, monte_carlo_seed=42
        )
        assert "config" in bundle
        assert "baseline_kpis" in bundle
        assert "sensitivity" not in bundle

    def test_with_sensitivity(self, small_config):
        bundle = build_industrial_analysis_bundle(
            small_config, run_sensitivity=True, monte_carlo_samples=0, monte_carlo_seed=42
        )
        assert "sensitivity" in bundle
        assert isinstance(bundle["sensitivity"], list)

    def test_with_monte_carlo(self, small_config):
        bundle = build_industrial_analysis_bundle(
            small_config, run_sensitivity=False, monte_carlo_samples=5, monte_carlo_seed=42
        )
        assert "monte_carlo" in bundle
        mc = bundle["monte_carlo"]
        assert "summary" in mc
        assert "records" in mc
