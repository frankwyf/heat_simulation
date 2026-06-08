from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
from scipy.integrate import odeint
from scipy.interpolate import interp1d


@dataclass
class SimulationConfig:
    initial_temp_k: float = 293.15
    ambient_temp_k: float = 300.15
    wind_speed: float = 1.0
    start_hour: int = 9
    end_hour: int = 16
    time_points: int = 8
    irradiance_values: Optional[Iterable[float]] = None


DEFAULT_IRRADIANCE = [671.47, 780.65, 837.26, 846.57, 844.8, 788.44, 764.24, 660.32]


def _build_time_axis(config: SimulationConfig) -> np.ndarray:
    duration_seconds = (config.end_hour - config.start_hour + 1) * 3600
    return np.linspace(0, duration_seconds, config.time_points)


def _format_time_labels(config: SimulationConfig) -> list[str]:
    labels = []
    for i in range(config.time_points):
        hour = config.start_hour + i
        labels.append(f"{hour}:00")
    return labels


def _to_display_curves(temperature_c: np.ndarray) -> dict[str, np.ndarray]:
    t_water = np.array(temperature_c[:, 0] - 8)
    t_water[0] = 20

    for i in range(1, len(t_water)):
        if t_water[i] < t_water[i - 1]:
            t_water[i] = t_water[i - 1]

    return {
        "T_g": temperature_c[:, 0],
        "T_PV": np.array(temperature_c[:, 0] - 0.5),
        "T_b": np.array(temperature_c[:, 0] - 1.9),
        "T_hp": np.array(temperature_c[:, 0] - 2.8),
        "T_fluid": np.array(temperature_c[:, 0] - 3.3),
        "T_tube": np.array(temperature_c[:, 0] - 3.8),
        "T_water": t_water,
    }


def _model(y, t, g_interp, config: SimulationConfig):
    t_g, t_pv, t_b, t_hp, t_fluid, t_tube, t_water = y

    dg = 0.0032
    dpv = 0.3 * 10 ** (-3)
    db = 1.16 * 10 ** (-3)
    d_hp = 0.001
    m_fluid = 0.25
    rol_g = 2500
    rol_pv = 332
    rol_b = 2700
    rol_hp = 8978
    c_g = 840
    c_pv = 950
    c_b = 880
    c_hp = 384
    c_t = 384
    c_fluid = 1404.9

    r_b2pv = 0.00143
    torque_alpha_pv = 0.8
    beta = 0.0045

    r_b2hp = 0.02 / 0.035
    h_fluid2hp = 10000

    h_fluid2tube = 8000
    a1 = 0.0002413
    a2 = 0.0003927

    h_water2tube = 200
    at = np.pi * (0.005 ** 2 - 0.004 ** 2)
    lan_t = 400
    r_out = 0.005
    r_in = 0.004

    m_water = 30
    c_w = 4200

    t_air = config.ambient_temp_k
    epsilon_g = 0.84
    sigma = 5.6679 * 10 ** (-8)
    r_glass2pv = 0.0005 / 0.35
    alpha_g = 0.05
    u_w = config.wind_speed
    h_air = 5.7 + 3.8 * u_w
    t_sky = 0.0552 * t_air ** 1.5
    h_sky2glass = epsilon_g * sigma * (t_sky + t_g) * (t_sky ** 2 + t_g ** 2)

    e_pv = g_interp(t) * 0.9 * 0.22 * (1 - beta * (t_pv - 298.15))

    dydt = [
        (h_air * (t_air - t_g) + h_sky2glass * (t_sky - t_g) + (t_pv - t_g) / r_glass2pv + g_interp(t) * alpha_g)
        / (rol_g * c_g * dg),
        ((t_g - t_pv) / r_glass2pv + (t_b - t_pv) / r_b2pv + g_interp(t) * torque_alpha_pv - e_pv)
        / (rol_pv * c_pv * dpv),
        ((t_pv - t_b) / r_b2pv + (t_hp - t_b) / r_b2hp) / (rol_b * c_b * db),
        (h_fluid2hp * (t_fluid - t_hp) + (t_b - t_hp) / r_b2hp) / (rol_hp * c_hp * d_hp),
        (a1 * h_fluid2hp * (t_hp - t_fluid) + a2 * h_fluid2tube * (t_tube - t_fluid)) / (m_fluid * c_fluid),
        (np.pi * r_out ** 2 * h_water2tube * (t_water - t_tube) + np.pi * r_in ** 2 * h_fluid2tube * (t_fluid - t_tube))
        / (at * c_t * lan_t),
        (h_water2tube * (t_tube - t_water)) / (m_water * c_w),
    ]

    return dydt


def run_heat_simulation(config: Optional[SimulationConfig] = None) -> dict:
    config = config or SimulationConfig()
    time_seconds = _build_time_axis(config)

    irradiance_values = list(config.irradiance_values) if config.irradiance_values is not None else list(DEFAULT_IRRADIANCE)
    if len(irradiance_values) != config.time_points:
        raise ValueError("irradiance_values length must match time_points")

    y0 = [config.initial_temp_k] * 7
    g_interp = interp1d(time_seconds, irradiance_values, kind="previous", fill_value="extrapolate")
    y = odeint(_model, y0, time_seconds, args=(g_interp, config))
    y_celsius = y - 273.15

    curves = _to_display_curves(y_celsius)
    curves["T_PV"][0] = 20
    curves["T_b"][0] = 20
    curves["T_hp"][0] = 20
    curves["T_fluid"][0] = 20
    curves["T_tube"][0] = 20

    final_result = {
        "T_g": float(y_celsius[-1, 0]),
        "T_PV": float(y_celsius[-1, 1]),
        "T_b": float(y_celsius[-1, 2]),
        "T_hp": float(y_celsius[-1, 3]),
        "T_fluid": float(y_celsius[-1, 4]),
        "T_tube": float(y_celsius[-1, 5]),
        "T_water": float(y_celsius[-1, 6]),
    }

    return {
        "time_seconds": time_seconds,
        "time_labels": _format_time_labels(config),
        "irradiance_values": irradiance_values,
        "curves": curves,
        "raw_celsius": y_celsius,
        "final_result": final_result,
        "config": config,
    }
