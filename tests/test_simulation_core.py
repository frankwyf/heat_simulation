"""Tests for heat_simulation.core.simulation_core."""
import numpy as np
import pytest

from heat_simulation.core.simulation_core import (
    DEFAULT_IRRADIANCE,
    SimulationConfig,
    _build_time_axis,
    _format_time_labels,
    _to_display_curves,
    run_heat_simulation,
)


# ---------------------------------------------------------------------------
# SimulationConfig defaults
# ---------------------------------------------------------------------------

class TestSimulationConfig:
    def test_default_values(self):
        cfg = SimulationConfig()
        assert cfg.initial_temp_k == pytest.approx(293.15)
        assert cfg.ambient_temp_k == pytest.approx(300.15)
        assert cfg.wind_speed == pytest.approx(1.0)
        assert cfg.start_hour == 9
        assert cfg.end_hour == 16
        assert cfg.time_points == 8
        assert cfg.irradiance_values is None

    def test_custom_values(self):
        cfg = SimulationConfig(wind_speed=3.5, time_points=4)
        assert cfg.wind_speed == pytest.approx(3.5)
        assert cfg.time_points == 4


# ---------------------------------------------------------------------------
# _build_time_axis
# ---------------------------------------------------------------------------

class TestBuildTimeAxis:
    def test_length_matches_time_points(self, default_config):
        t = _build_time_axis(default_config)
        assert len(t) == default_config.time_points

    def test_starts_at_zero(self, default_config):
        t = _build_time_axis(default_config)
        assert t[0] == pytest.approx(0.0)

    def test_monotonically_increasing(self, default_config):
        t = _build_time_axis(default_config)
        assert np.all(np.diff(t) > 0)

    def test_small_config_duration(self, small_config):
        t = _build_time_axis(small_config)
        assert len(t) == small_config.time_points
        expected_duration = (small_config.end_hour - small_config.start_hour + 1) * 3600
        assert t[-1] == pytest.approx(expected_duration)


# ---------------------------------------------------------------------------
# _format_time_labels
# ---------------------------------------------------------------------------

class TestFormatTimeLabels:
    def test_count(self, default_config):
        labels = _format_time_labels(default_config)
        assert len(labels) == default_config.time_points

    def test_first_label(self, default_config):
        labels = _format_time_labels(default_config)
        assert labels[0] == f"{default_config.start_hour}:00"

    def test_labels_are_strings(self, default_config):
        labels = _format_time_labels(default_config)
        assert all(isinstance(l, str) for l in labels)


# ---------------------------------------------------------------------------
# _to_display_curves
# ---------------------------------------------------------------------------

class TestToDisplayCurves:
    def test_keys_present(self):
        fake_celsius = np.full((8, 7), 50.0)
        curves = _to_display_curves(fake_celsius)
        expected_keys = {"T_g", "T_PV", "T_b", "T_hp", "T_fluid", "T_tube", "T_water"}
        assert expected_keys == set(curves.keys())

    def test_water_temp_monotone_after_first(self):
        fake_celsius = np.linspace(40, 70, 8 * 7).reshape(8, 7)
        curves = _to_display_curves(fake_celsius)
        t_water = curves["T_water"]
        # water should be non-decreasing from index 1 onward
        assert np.all(np.diff(t_water[1:]) >= -1e-9)


# ---------------------------------------------------------------------------
# run_heat_simulation
# ---------------------------------------------------------------------------

class TestRunHeatSimulation:
    def test_default_run_returns_dict(self, base_sim_result):
        assert isinstance(base_sim_result, dict)

    def test_required_keys(self, base_sim_result):
        for key in ("time_seconds", "time_labels", "irradiance_values", "curves", "raw_celsius", "final_result"):
            assert key in base_sim_result

    def test_curves_shape(self, base_sim_result):
        cfg = base_sim_result["config"]
        for key, arr in base_sim_result["curves"].items():
            assert len(arr) == cfg.time_points, f"Curve {key} has wrong length"

    def test_final_result_keys(self, base_sim_result):
        for key in ("T_g", "T_PV", "T_b", "T_hp", "T_fluid", "T_tube", "T_water"):
            assert key in base_sim_result["final_result"]

    def test_water_temp_increases(self, base_sim_result):
        water_curve = base_sim_result["curves"]["T_water"]
        assert water_curve[-1] >= water_curve[1]  # should heat up over time

    def test_custom_config(self, small_config, small_sim_result):
        assert len(small_sim_result["time_seconds"]) == small_config.time_points

    def test_irradiance_length_mismatch_raises(self):
        bad_cfg = SimulationConfig(
            time_points=4,
            irradiance_values=[600, 700, 800],  # only 3, not 4
        )
        with pytest.raises(ValueError, match="irradiance_values length"):
            run_heat_simulation(bad_cfg)

    def test_none_config_uses_defaults(self):
        result = run_heat_simulation(None)
        assert result is not None
        assert len(result["irradiance_values"]) == 8

    @pytest.mark.parametrize("wind_speed", [0.0, 1.0, 5.0, 10.0])
    def test_various_wind_speeds_succeed(self, wind_speed):
        cfg = SimulationConfig(
            time_points=4,
            irradiance_values=DEFAULT_IRRADIANCE[:4],
            wind_speed=wind_speed,
        )
        result = run_heat_simulation(cfg)
        assert "final_result" in result

    @pytest.mark.parametrize("ambient_c", [15.0, 25.0, 35.0, 45.0])
    def test_various_ambient_temps(self, ambient_c):
        cfg = SimulationConfig(
            time_points=4,
            irradiance_values=DEFAULT_IRRADIANCE[:4],
            ambient_temp_k=ambient_c + 273.15,
        )
        result = run_heat_simulation(cfg)
        assert result["final_result"]["T_water"] > 0


# ---------------------------------------------------------------------------
# DEFAULT_IRRADIANCE constant
# ---------------------------------------------------------------------------

def test_default_irradiance_length():
    assert len(DEFAULT_IRRADIANCE) == 8

def test_default_irradiance_positive():
    assert all(v > 0 for v in DEFAULT_IRRADIANCE)
