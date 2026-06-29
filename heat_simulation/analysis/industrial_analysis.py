from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any, Dict, Iterable

import numpy as np
import pandas as pd

from heat_simulation.core.simulation_core import SimulationConfig, run_heat_simulation


def _safe_curve(curves: Dict[str, np.ndarray], key: str) -> np.ndarray:
    values = curves.get(key)
    if values is None:
        raise KeyError(f"curve '{key}' not found")
    return np.asarray(values, dtype=float)


def _config_to_dict(config: SimulationConfig) -> Dict[str, Any]:
    payload = asdict(config)
    if payload.get("irradiance_values") is not None:
        payload["irradiance_values"] = list(payload["irradiance_values"])
    return payload


def compute_industrial_kpis(sim_result: Dict[str, Any]) -> Dict[str, float]:
    time_seconds = np.asarray(sim_result["time_seconds"], dtype=float)
    if time_seconds.ndim != 1 or len(time_seconds) < 2:
        raise ValueError("time_seconds must be a one-dimensional array with at least two points")

    time_hours = time_seconds / 3600.0
    curves = sim_result["curves"]

    t_pv = _safe_curve(curves, "T_PV")
    t_glass = _safe_curve(curves, "T_g")
    t_fluid = _safe_curve(curves, "T_fluid")
    t_water = _safe_curve(curves, "T_water")

    stacked = np.vstack(
        [
            _safe_curve(curves, "T_g"),
            _safe_curve(curves, "T_PV"),
            _safe_curve(curves, "T_b"),
            _safe_curve(curves, "T_hp"),
            _safe_curve(curves, "T_fluid"),
            _safe_curve(curves, "T_tube"),
            _safe_curve(curves, "T_water"),
        ]
    )

    irradiance = np.asarray(sim_result["irradiance_values"], dtype=float)
    if len(irradiance) != len(time_hours):
        raise ValueError("irradiance_values length must match time axis")

    dt_hours = float(np.mean(np.diff(time_hours)))
    ramp_water = np.gradient(t_water, time_hours)

    thermal_spread = np.std(stacked, axis=0)
    spread_mean = float(np.mean(thermal_spread))

    kpis = {
        "peak_pv_temp_c": float(np.max(t_pv)),
        "peak_glass_temp_c": float(np.max(t_glass)),
        "mean_fluid_temp_c": float(np.mean(t_fluid)),
        "final_water_temp_c": float(t_water[-1]),
        "water_temperature_gain_c": float(t_water[-1] - t_water[0]),
        "mean_water_heating_rate_c_per_h": float(np.mean(ramp_water)),
        "max_water_heating_rate_c_per_h": float(np.max(ramp_water)),
        "temperature_stability_std_c": float(np.std(np.diff(t_water))),
        "thermal_uniformity_index": float(1.0 / (1.0 + spread_mean)),
        "temperature_risk_hours_above_60c": float(np.sum(t_pv > 60.0) * dt_hours),
        "energy_capture_proxy_wh_m2": float(np.sum(irradiance) * dt_hours),
    }
    return kpis


def _apply_parameter_delta(
    base_config: SimulationConfig,
    parameter: str,
    delta_ratio: float,
) -> SimulationConfig:
    if parameter == "ambient_temp_k":
        return replace(base_config, ambient_temp_k=base_config.ambient_temp_k * (1.0 + delta_ratio))
    if parameter == "wind_speed":
        return replace(base_config, wind_speed=max(0.0, base_config.wind_speed * (1.0 + delta_ratio)))
    if parameter == "initial_temp_k":
        return replace(base_config, initial_temp_k=base_config.initial_temp_k * (1.0 + delta_ratio))
    if parameter == "irradiance_scale":
        base_irr = list(base_config.irradiance_values) if base_config.irradiance_values is not None else None
        if base_irr is None:
            return replace(base_config)
        scaled = [max(0.0, float(v) * (1.0 + delta_ratio)) for v in base_irr]
        return replace(base_config, irradiance_values=scaled)
    raise ValueError(f"Unsupported sensitivity parameter: {parameter}")


def run_one_factor_sensitivity(
    base_config: SimulationConfig,
    deltas: Iterable[float] = (-0.2, -0.1, 0.0, 0.1, 0.2),
    metric_key: str = "water_temperature_gain_c",
) -> pd.DataFrame:
    parameters = ["ambient_temp_k", "wind_speed", "initial_temp_k", "irradiance_scale"]
    rows = []

    for parameter in parameters:
        for delta in deltas:
            cfg = _apply_parameter_delta(base_config, parameter, float(delta))
            sim_result = run_heat_simulation(cfg)
            kpis = compute_industrial_kpis(sim_result)
            rows.append(
                {
                    "parameter": parameter,
                    "delta_ratio": float(delta),
                    "metric_key": metric_key,
                    "metric_value": float(kpis[metric_key]),
                    "peak_pv_temp_c": float(kpis["peak_pv_temp_c"]),
                }
            )

    return pd.DataFrame(rows)


def run_monte_carlo_analysis(
    base_config: SimulationConfig,
    samples: int = 120,
    seed: int = 42,
    ambient_sigma_c: float = 1.8,
    wind_sigma: float = 0.6,
    irradiance_sigma_ratio: float = 0.08,
) -> pd.DataFrame:
    if samples <= 0:
        raise ValueError("samples must be > 0")

    rng = np.random.default_rng(seed)
    base_irr = np.array(
        list(base_config.irradiance_values) if base_config.irradiance_values is not None else [],
        dtype=float,
    )

    rows = []
    for sample_id in range(1, samples + 1):
        ambient_k = float(base_config.ambient_temp_k + rng.normal(0.0, ambient_sigma_c))
        wind_speed = float(max(0.0, base_config.wind_speed + rng.normal(0.0, wind_sigma)))

        if len(base_irr) > 0:
            noise = rng.normal(0.0, irradiance_sigma_ratio, size=len(base_irr))
            irr = np.maximum(base_irr * (1.0 + noise), 0.0).tolist()
            cfg = replace(base_config, ambient_temp_k=ambient_k, wind_speed=wind_speed, irradiance_values=irr)
        else:
            cfg = replace(base_config, ambient_temp_k=ambient_k, wind_speed=wind_speed)

        sim_result = run_heat_simulation(cfg)
        kpis = compute_industrial_kpis(sim_result)
        rows.append(
            {
                "sample_id": sample_id,
                "ambient_temp_k": ambient_k,
                "wind_speed": wind_speed,
                "peak_pv_temp_c": float(kpis["peak_pv_temp_c"]),
                "final_water_temp_c": float(kpis["final_water_temp_c"]),
                "water_temperature_gain_c": float(kpis["water_temperature_gain_c"]),
                "temperature_risk_hours_above_60c": float(kpis["temperature_risk_hours_above_60c"]),
                "thermal_uniformity_index": float(kpis["thermal_uniformity_index"]),
            }
        )

    return pd.DataFrame(rows)


def summarize_monte_carlo(monte_carlo_df: pd.DataFrame) -> Dict[str, float]:
    if monte_carlo_df.empty:
        raise ValueError("monte_carlo_df cannot be empty")

    final_water = monte_carlo_df["final_water_temp_c"].to_numpy(dtype=float)
    gain = monte_carlo_df["water_temperature_gain_c"].to_numpy(dtype=float)
    risk = monte_carlo_df["temperature_risk_hours_above_60c"].to_numpy(dtype=float)

    return {
        "samples": float(len(monte_carlo_df)),
        "final_water_temp_mean_c": float(np.mean(final_water)),
        "final_water_temp_p05_c": float(np.percentile(final_water, 5)),
        "final_water_temp_p95_c": float(np.percentile(final_water, 95)),
        "water_gain_mean_c": float(np.mean(gain)),
        "water_gain_std_c": float(np.std(gain)),
        "risk_hours_mean": float(np.mean(risk)),
        "risk_hours_p95": float(np.percentile(risk, 95)),
    }


def build_industrial_analysis_bundle(
    base_config: SimulationConfig,
    run_sensitivity: bool,
    monte_carlo_samples: int,
    monte_carlo_seed: int,
) -> Dict[str, Any]:
    baseline_result = run_heat_simulation(base_config)
    baseline_kpis = compute_industrial_kpis(baseline_result)

    payload: Dict[str, Any] = {
        "config": _config_to_dict(base_config),
        "baseline_kpis": baseline_kpis,
    }

    if run_sensitivity:
        sensitivity_df = run_one_factor_sensitivity(base_config)
        payload["sensitivity"] = sensitivity_df.to_dict(orient="records")

    if monte_carlo_samples > 0:
        mc_df = run_monte_carlo_analysis(base_config, samples=monte_carlo_samples, seed=monte_carlo_seed)
        payload["monte_carlo"] = {
            "summary": summarize_monte_carlo(mc_df),
            "records": mc_df.to_dict(orient="records"),
        }

    return payload
