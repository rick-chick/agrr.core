"""Pytest configuration for adapter layer tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from agrr_core.usecase.interactors.fetch_weather_data_interactor import FetchWeatherDataInteractor
from agrr_core.adapter.presenters.cli_weather_presenter import CLIWeatherPresenter
from agrr_core.adapter.controllers.cli_weather_controller import CLIWeatherController


@pytest.fixture
def mock_fetch_weather_interactor():
    """Mock fetch weather interactor."""
    return AsyncMock(spec=FetchWeatherDataInteractor)


@pytest.fixture
def mock_cli_presenter():
    """Mock CLI presenter."""
    return MagicMock(spec=CLIWeatherPresenter)


@pytest.fixture
def cli_weather_controller(mock_fetch_weather_interactor, mock_cli_presenter):
    """CLI weather controller with mocked dependencies."""
    return CLIWeatherController(
        fetch_weather_interactor=mock_fetch_weather_interactor,
        cli_presenter=mock_cli_presenter
    )
