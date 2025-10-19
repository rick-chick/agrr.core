"""Pytest configuration for adapter layer tests.

Adapter layer tests focus on:
- Controllers (Input port implementations)
- Presenters (Output port implementations)
- Gateway implementations
- Repository implementations
- Mapper implementations
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

from agrr_core.usecase.interactors.weather_fetch_interactor import FetchWeatherDataInteractor
from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
from agrr_core.adapter.controllers.weather_cli_controller import WeatherCliFetchController
from agrr_core.usecase.dto.optimization_config import OptimizationConfig


# ============================================================================
# Adapter Layer - Controller Fixtures
# ============================================================================

@pytest.fixture
def presenter_weather_cli():
    """Mock CLI presenter for weather data."""
    return MagicMock(spec=WeatherCLIPresenter)


@pytest.fixture
def controller_weather_cli_fetch(gateway_weather, presenter_weather_cli):
    """CLI weather fetch controller with mocked dependencies."""
    return WeatherCliFetchController(
        weather_gateway=gateway_weather,
        cli_presenter=presenter_weather_cli
    )


# ============================================================================
# UseCase Layer - Interactor Fixtures (for adapter tests)
# ============================================================================

@pytest.fixture
def interactor_fetch_weather():
    """Mock fetch weather interactor for controller tests."""
    return AsyncMock(spec=FetchWeatherDataInteractor)


# ============================================================================
# Optimization Configuration Fixtures
# ============================================================================

@pytest.fixture
def optimization_config_legacy():
    """Legacy candidate pool optimization config for backward compatibility."""
    return OptimizationConfig(
        candidate_generation_strategy="candidate_pool"
    )


