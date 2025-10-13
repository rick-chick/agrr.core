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


