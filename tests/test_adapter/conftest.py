"""Pytest configuration for adapter layer tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from agrr_core.usecase.interactors.weather_fetch_interactor import FetchWeatherDataInteractor
from agrr_core.adapter.presenters.weather_cli_presenter import WeatherCLIPresenter
from agrr_core.adapter.controllers.weather_cli_controller import WeatherCliFetchController


@pytest.fixture
def mock_fetch_weather_interactor():
    """Mock fetch weather interactor."""
    return AsyncMock(spec=FetchWeatherDataInteractor)


@pytest.fixture
def mock_cli_presenter():
    """Mock CLI presenter."""
    return MagicMock(spec=WeatherCLIPresenter)


@pytest.fixture
def mock_weather_gateway():
    """Mock weather gateway."""
    return AsyncMock()


@pytest.fixture
def cli_weather_controller(mock_weather_gateway, mock_cli_presenter):
    """CLI weather controller with mocked dependencies."""
    return WeatherCliFetchController(
        weather_gateway=mock_weather_gateway,
        cli_presenter=mock_cli_presenter
    )
