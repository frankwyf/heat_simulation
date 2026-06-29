"""Shared pytest fixtures for heat_simulation tests."""
import os
import sys
from unittest.mock import MagicMock

import matplotlib
matplotlib.use("Agg")  # non-interactive backend for all tests

# Mock streamlit before any test module imports app.py
_st_mock = MagicMock()
_st_mock.cache_data = lambda **kw: (lambda f: f)  # passthrough decorator
_st_mock.cache_resource = lambda **kw: (lambda f: f)
sys.modules.setdefault("streamlit", _st_mock)

import numpy as np
import pytest

from heat_simulation.core.simulation_core import DEFAULT_IRRADIANCE, SimulationConfig, run_heat_simulation


@pytest.fixture(scope="session")
def default_config() -> SimulationConfig:
    return SimulationConfig()


@pytest.fixture(scope="session")
def base_sim_result(default_config):
    return run_heat_simulation(default_config)


@pytest.fixture(scope="session")
def small_config() -> SimulationConfig:
    """Fast config: fewer time points for quick tests."""
    return SimulationConfig(
        initial_temp_k=293.15,
        ambient_temp_k=300.15,
        wind_speed=1.0,
        start_hour=9,
        end_hour=12,
        time_points=4,
        irradiance_values=[671.47, 780.65, 837.26, 846.57],
    )


@pytest.fixture(scope="session")
def small_sim_result(small_config):
    return run_heat_simulation(small_config)


@pytest.fixture(scope="session")
def typical_kpis(small_sim_result):
    from heat_simulation.analysis.industrial_analysis import compute_industrial_kpis
    return compute_industrial_kpis(small_sim_result)
