"""
Basic tests for agrr_core package.
"""
import pytest
from agrr_core import __version__


def test_version():
    """Test that version is defined."""
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_import():
    """Test that package can be imported."""
    import agrr_core
    assert hasattr(agrr_core, "__version__")


def test_import_weather_entities():
    """Test importing weather entities."""
    from agrr_core.entity import WeatherData, Location, DateRange, Forecast
    
    assert WeatherData is not None
    assert Location is not None
    assert DateRange is not None
    assert Forecast is not None


def test_import_weather_interactors():
    """Test importing weather interactors."""
    from agrr_core.usecase import (
        FetchWeatherDataInteractor,
        PredictWeatherInteractor,
        WeatherPredictionOutputPort,
    )
    
    assert FetchWeatherDataInteractor is not None
    assert PredictWeatherInteractor is not None
    assert WeatherPredictionOutputPort is not None


def test_import_weather_repositories():
    """Test importing weather repositories."""
    from agrr_core.adapter import (
        WeatherAPIOpenMeteoRepository,
        WeatherMemoryRepository,
        PredictionStorageRepository,
        WeatherMapper,
    )
    
    assert WeatherAPIOpenMeteoRepository is not None
    assert WeatherMemoryRepository is not None
    assert PredictionStorageRepository is not None
    assert WeatherMapper is not None


def test_import_dtos():
    """Test importing DTOs."""
    from agrr_core.usecase import (
        WeatherDataRequestDTO,
        WeatherDataResponseDTO,
        WeatherDataListResponseDTO,
        PredictionRequestDTO,
        PredictionResponseDTO,
        ForecastResponseDTO,
    )
    
    assert WeatherDataRequestDTO is not None
    assert WeatherDataResponseDTO is not None
    assert WeatherDataListResponseDTO is not None
    assert PredictionRequestDTO is not None
    assert PredictionResponseDTO is not None
    assert ForecastResponseDTO is not None


def test_import_exceptions():
    """Test importing exceptions."""
    from agrr_core.entity.exceptions.weather_error import WeatherError
    from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
    from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
    from agrr_core.entity.exceptions.invalid_date_range_error import InvalidDateRangeError
    from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
    from agrr_core.entity.exceptions.prediction_error import PredictionError

    assert WeatherError is not None
    assert WeatherDataNotFoundError is not None
    assert InvalidLocationError is not None
    assert InvalidDateRangeError is not None
    assert WeatherAPIError is not None
    assert PredictionError is not None


@pytest.mark.parametrize("test_input,expected", [
    (1, 1),
    (2, 2),
    (3, 3),
])
def test_parametrized(test_input, expected):
    """Example parametrized test."""
    assert test_input == expected


@pytest.mark.slow
def test_slow_operation():
    """Example slow test that can be skipped."""
    import time
    time.sleep(0.1)  # Simulate slow operation
    assert True
