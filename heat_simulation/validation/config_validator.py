"""Simulation Configuration Validator.

Validates user-supplied configuration parameters against physical constraints
and operational limits. Produces structured validation reports with warnings
and errors for industrial safety compliance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from heat_simulation.core.simulation_core import SimulationConfig


@dataclass
class ValidationIssue:
    field: str
    severity: str  # "error", "warning", "info"
    message: str
    value: Any = None
    constraint: str = ""


@dataclass
class ValidationResult:
    is_valid: bool
    issues: List[ValidationIssue]
    config_summary: Dict[str, Any]

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


# Physical constraints
ABSOLUTE_ZERO_K = 0.0
MAX_REASONABLE_TEMP_K = 1000.0  # Well above any solar panel scenario
MIN_WIND_SPEED = 0.0
MAX_WIND_SPEED = 50.0  # m/s - hurricane force
MIN_IRRADIANCE = 0.0
MAX_IRRADIANCE = 1500.0  # W/m² - extreme solar
MIN_TIME_POINTS = 2
MAX_TIME_POINTS = 10000


def validate_config(config: SimulationConfig) -> ValidationResult:
    """Validate a simulation configuration against physical and operational constraints.

    Returns a ValidationResult indicating validity and any issues found.
    """
    issues: List[ValidationIssue] = []

    # Temperature checks
    if config.initial_temp_k <= ABSOLUTE_ZERO_K:
        issues.append(ValidationIssue(
            field="initial_temp_k",
            severity="error",
            message="Initial temperature must be above absolute zero",
            value=config.initial_temp_k,
            constraint=f"> {ABSOLUTE_ZERO_K} K",
        ))
    elif config.initial_temp_k > MAX_REASONABLE_TEMP_K:
        issues.append(ValidationIssue(
            field="initial_temp_k",
            severity="warning",
            message="Initial temperature unusually high for solar panel simulation",
            value=config.initial_temp_k,
            constraint=f"<= {MAX_REASONABLE_TEMP_K} K",
        ))

    if config.ambient_temp_k <= ABSOLUTE_ZERO_K:
        issues.append(ValidationIssue(
            field="ambient_temp_k",
            severity="error",
            message="Ambient temperature must be above absolute zero",
            value=config.ambient_temp_k,
            constraint=f"> {ABSOLUTE_ZERO_K} K",
        ))
    elif config.ambient_temp_k > MAX_REASONABLE_TEMP_K:
        issues.append(ValidationIssue(
            field="ambient_temp_k",
            severity="warning",
            message="Ambient temperature unusually high",
            value=config.ambient_temp_k,
            constraint=f"<= {MAX_REASONABLE_TEMP_K} K",
        ))

    # Wind speed
    if config.wind_speed < MIN_WIND_SPEED:
        issues.append(ValidationIssue(
            field="wind_speed",
            severity="error",
            message="Wind speed cannot be negative",
            value=config.wind_speed,
            constraint=f">= {MIN_WIND_SPEED}",
        ))
    elif config.wind_speed > MAX_WIND_SPEED:
        issues.append(ValidationIssue(
            field="wind_speed",
            severity="warning",
            message="Wind speed exceeds hurricane force - verify input",
            value=config.wind_speed,
            constraint=f"<= {MAX_WIND_SPEED} m/s",
        ))

    # Time window
    if config.start_hour >= config.end_hour:
        issues.append(ValidationIssue(
            field="start_hour/end_hour",
            severity="error",
            message="Start hour must be before end hour",
            value=f"{config.start_hour}-{config.end_hour}",
            constraint="start_hour < end_hour",
        ))

    if config.start_hour < 0 or config.start_hour > 23:
        issues.append(ValidationIssue(
            field="start_hour",
            severity="error",
            message="Start hour must be 0-23",
            value=config.start_hour,
            constraint="0 <= start_hour <= 23",
        ))

    if config.end_hour < 0 or config.end_hour > 23:
        issues.append(ValidationIssue(
            field="end_hour",
            severity="error",
            message="End hour must be 0-23",
            value=config.end_hour,
            constraint="0 <= end_hour <= 23",
        ))

    # Time points
    if config.time_points < MIN_TIME_POINTS:
        issues.append(ValidationIssue(
            field="time_points",
            severity="error",
            message=f"At least {MIN_TIME_POINTS} time points required for simulation",
            value=config.time_points,
            constraint=f">= {MIN_TIME_POINTS}",
        ))
    elif config.time_points > MAX_TIME_POINTS:
        issues.append(ValidationIssue(
            field="time_points",
            severity="warning",
            message="Very large time_points may cause slow simulation",
            value=config.time_points,
            constraint=f"<= {MAX_TIME_POINTS}",
        ))

    # Irradiance values
    if config.irradiance_values is not None:
        irr_list = list(config.irradiance_values)
        if len(irr_list) != config.time_points:
            issues.append(ValidationIssue(
                field="irradiance_values",
                severity="error",
                message="Irradiance array length must match time_points",
                value=f"len={len(irr_list)}",
                constraint=f"len == {config.time_points}",
            ))
        for i, val in enumerate(irr_list):
            if val < MIN_IRRADIANCE:
                issues.append(ValidationIssue(
                    field=f"irradiance_values[{i}]",
                    severity="error",
                    message="Irradiance cannot be negative",
                    value=val,
                    constraint=f">= {MIN_IRRADIANCE}",
                ))
                break  # Report first invalid only
            if val > MAX_IRRADIANCE:
                issues.append(ValidationIssue(
                    field=f"irradiance_values[{i}]",
                    severity="warning",
                    message="Irradiance exceeds typical maximum solar flux",
                    value=val,
                    constraint=f"<= {MAX_IRRADIANCE}",
                ))
                break

    # Cross-field: ambient vs initial
    if config.initial_temp_k > ABSOLUTE_ZERO_K and config.ambient_temp_k > ABSOLUTE_ZERO_K:
        diff = abs(config.initial_temp_k - config.ambient_temp_k)
        if diff > 100:
            issues.append(ValidationIssue(
                field="initial_temp_k vs ambient_temp_k",
                severity="info",
                message="Large temperature difference between initial and ambient",
                value=f"diff={diff:.1f} K",
                constraint="typically < 100 K",
            ))

    is_valid = all(i.severity != "error" for i in issues)

    return ValidationResult(
        is_valid=is_valid,
        issues=issues,
        config_summary={
            "initial_temp_k": config.initial_temp_k,
            "ambient_temp_k": config.ambient_temp_k,
            "wind_speed": config.wind_speed,
            "start_hour": config.start_hour,
            "end_hour": config.end_hour,
            "time_points": config.time_points,
            "has_irradiance": config.irradiance_values is not None,
        },
    )


def format_validation_report(result: ValidationResult) -> str:
    """Format validation result as human-readable text."""
    lines = ["Configuration Validation Report", "=" * 35, ""]

    if result.is_valid:
        lines.append("Status: VALID")
    else:
        lines.append("Status: INVALID")

    lines.append(f"Errors: {result.error_count}")
    lines.append(f"Warnings: {result.warning_count}")
    lines.append("")

    if result.issues:
        lines.append("Issues:")
        for issue in result.issues:
            icon = {"error": "[ERROR]", "warning": "[WARN]", "info": "[INFO]"}.get(issue.severity, "[?]")
            lines.append(f"  {icon} {issue.field}: {issue.message} (value={issue.value})")
    else:
        lines.append("No issues found.")

    return "\n".join(lines)
