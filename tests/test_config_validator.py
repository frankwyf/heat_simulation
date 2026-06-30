"""Tests for heat_simulation.validation.config_validator."""
import pytest

from heat_simulation.core.simulation_core import SimulationConfig
from heat_simulation.validation.config_validator import (
    ValidationIssue,
    ValidationResult,
    validate_config,
    format_validation_report,
    ABSOLUTE_ZERO_K,
    MAX_REASONABLE_TEMP_K,
    MAX_WIND_SPEED,
    MAX_IRRADIANCE,
    MIN_TIME_POINTS,
    MAX_TIME_POINTS,
)


class TestValidationIssue:
    def test_create_issue(self):
        issue = ValidationIssue(
            field="test_field",
            severity="error",
            message="bad value",
            value=42,
            constraint="> 0",
        )
        assert issue.field == "test_field"
        assert issue.severity == "error"


class TestValidationResult:
    def test_error_count(self):
        issues = [
            ValidationIssue("a", "error", "err1"),
            ValidationIssue("b", "warning", "warn1"),
            ValidationIssue("c", "error", "err2"),
        ]
        result = ValidationResult(is_valid=False, issues=issues, config_summary={})
        assert result.error_count == 2
        assert result.warning_count == 1


class TestValidateConfigValid:
    def test_default_config_valid(self):
        config = SimulationConfig()
        result = validate_config(config)
        assert result.is_valid is True
        assert result.error_count == 0

    def test_typical_config_valid(self):
        config = SimulationConfig(
            initial_temp_k=295.0,
            ambient_temp_k=303.0,
            wind_speed=2.5,
            start_hour=9,
            end_hour=16,
            time_points=8,
        )
        result = validate_config(config)
        assert result.is_valid is True


class TestValidateConfigTemperature:
    def test_zero_initial_temp_error(self):
        config = SimulationConfig(initial_temp_k=0.0)
        result = validate_config(config)
        assert not result.is_valid
        assert any("initial_temp_k" in i.field and i.severity == "error" for i in result.issues)

    def test_negative_initial_temp_error(self):
        config = SimulationConfig(initial_temp_k=-10.0)
        result = validate_config(config)
        assert not result.is_valid

    def test_very_high_initial_temp_warning(self):
        config = SimulationConfig(initial_temp_k=1500.0)
        result = validate_config(config)
        assert result.is_valid  # warning doesn't make invalid
        assert any("initial_temp_k" in i.field and i.severity == "warning" for i in result.issues)

    def test_zero_ambient_temp_error(self):
        config = SimulationConfig(ambient_temp_k=0.0)
        result = validate_config(config)
        assert not result.is_valid

    def test_very_high_ambient_temp_warning(self):
        config = SimulationConfig(ambient_temp_k=1100.0)
        result = validate_config(config)
        assert result.is_valid
        assert result.warning_count >= 1


class TestValidateConfigWindSpeed:
    def test_negative_wind_error(self):
        config = SimulationConfig(wind_speed=-1.0)
        result = validate_config(config)
        assert not result.is_valid
        assert any("wind_speed" in i.field for i in result.issues)

    def test_extreme_wind_warning(self):
        config = SimulationConfig(wind_speed=60.0)
        result = validate_config(config)
        assert result.is_valid
        assert any("wind_speed" in i.field and i.severity == "warning" for i in result.issues)

    def test_zero_wind_ok(self):
        config = SimulationConfig(wind_speed=0.0)
        result = validate_config(config)
        # wind_speed=0 is valid (no negative)
        wind_errors = [i for i in result.issues if "wind_speed" in i.field and i.severity == "error"]
        assert len(wind_errors) == 0


class TestValidateConfigTimeWindow:
    def test_start_after_end_error(self):
        config = SimulationConfig(start_hour=16, end_hour=9)
        result = validate_config(config)
        assert not result.is_valid
        assert any("start_hour" in i.field for i in result.issues)

    def test_start_equals_end_error(self):
        config = SimulationConfig(start_hour=12, end_hour=12)
        result = validate_config(config)
        assert not result.is_valid

    def test_invalid_start_hour(self):
        config = SimulationConfig(start_hour=-1, end_hour=16)
        result = validate_config(config)
        assert not result.is_valid

    def test_invalid_end_hour(self):
        config = SimulationConfig(start_hour=9, end_hour=25)
        result = validate_config(config)
        assert not result.is_valid


class TestValidateConfigTimePoints:
    def test_one_time_point_error(self):
        config = SimulationConfig(time_points=1)
        result = validate_config(config)
        assert not result.is_valid
        assert any("time_points" in i.field for i in result.issues)

    def test_very_large_time_points_warning(self):
        config = SimulationConfig(time_points=15000)
        result = validate_config(config)
        assert result.is_valid
        assert any("time_points" in i.field and i.severity == "warning" for i in result.issues)


class TestValidateConfigIrradiance:
    def test_length_mismatch_error(self):
        config = SimulationConfig(time_points=8, irradiance_values=[100, 200, 300])
        result = validate_config(config)
        assert not result.is_valid
        assert any("irradiance_values" in i.field for i in result.issues)

    def test_negative_irradiance_error(self):
        config = SimulationConfig(time_points=3, irradiance_values=[100, -50, 200])
        result = validate_config(config)
        assert not result.is_valid

    def test_extreme_irradiance_warning(self):
        config = SimulationConfig(time_points=3, irradiance_values=[100, 2000, 200])
        result = validate_config(config)
        assert result.is_valid
        assert result.warning_count >= 1

    def test_valid_irradiance(self):
        config = SimulationConfig(time_points=3, irradiance_values=[500, 700, 600])
        result = validate_config(config)
        irr_issues = [i for i in result.issues if "irradiance" in i.field]
        assert len(irr_issues) == 0


class TestValidateConfigCrossField:
    def test_large_temp_difference_info(self):
        config = SimulationConfig(initial_temp_k=200.0, ambient_temp_k=400.0)
        result = validate_config(config)
        assert any(i.severity == "info" for i in result.issues)

    def test_normal_difference_no_info(self):
        config = SimulationConfig(initial_temp_k=293.0, ambient_temp_k=300.0)
        result = validate_config(config)
        info_issues = [i for i in result.issues if i.severity == "info"]
        assert len(info_issues) == 0


class TestFormatValidationReport:
    def test_valid_report(self):
        config = SimulationConfig()
        result = validate_config(config)
        text = format_validation_report(result)
        assert "VALID" in text
        assert "Errors: 0" in text

    def test_invalid_report(self):
        config = SimulationConfig(initial_temp_k=-5.0)
        result = validate_config(config)
        text = format_validation_report(result)
        assert "INVALID" in text
        assert "[ERROR]" in text

    def test_warning_report(self):
        config = SimulationConfig(wind_speed=55.0)
        result = validate_config(config)
        text = format_validation_report(result)
        assert "[WARN]" in text

    def test_no_issues(self):
        config = SimulationConfig()
        result = validate_config(config)
        text = format_validation_report(result)
        assert "No issues found" in text
