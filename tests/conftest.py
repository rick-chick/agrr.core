"""Test configuration and fixtures."""

import pytest
from datetime import datetime

from agrr_core.entity import WeatherData
from agrr_core.adapter.repositories.in_memory_weather_repository import InMemoryWeatherRepository
from agrr_core.adapter.repositories.prediction_repository import InMemoryPredictionRepository


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing."""
    return [
        WeatherData(
            time=datetime(2023, 1, 1),
            temperature_2m_max=25.0,
            temperature_2m_min=15.0,
            temperature_2m_mean=20.0,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
        ),
        WeatherData(
            time=datetime(2023, 1, 2),
            temperature_2m_max=26.0,
            temperature_2m_min=16.0,
            temperature_2m_mean=21.0,
            precipitation_sum=3.0,
            sunshine_duration=25200.0,
        ),
        WeatherData(
            time=datetime(2023, 1, 3),
            temperature_2m_max=27.0,
            temperature_2m_min=17.0,
            temperature_2m_mean=22.0,
            precipitation_sum=2.0,
            sunshine_duration=21600.0,
        ),
    ]


@pytest.fixture
def sample_weather_data_with_none():
    """Sample weather data with None values for testing."""
    return [
        WeatherData(
            time=datetime(2023, 1, 1),
            temperature_2m_max=None,
            temperature_2m_min=15.0,
            temperature_2m_mean=20.0,
            precipitation_sum=None,
            sunshine_duration=None,
        ),
        WeatherData(
            time=datetime(2023, 1, 2),
            temperature_2m_max=26.0,
            temperature_2m_min=None,
            temperature_2m_mean=None,
            precipitation_sum=3.0,
            sunshine_duration=25200.0,
        ),
    ]


@pytest.fixture
def extended_weather_data():
    """Extended weather data for prediction testing."""
    data = []
    for i in range(30):  # 30 days of data
        data.append(
            WeatherData(
                time=datetime(2023, 1, i + 1),
                temperature_2m_mean=20.0 + i * 0.1,  # Slight trend
                temperature_2m_max=25.0 + i * 0.1,
                temperature_2m_min=15.0 + i * 0.1,
                precipitation_sum=5.0,
                sunshine_duration=28800.0,
            )
        )
    return data


@pytest.fixture
def empty_weather_repository():
    """Empty weather repository for testing."""
    return InMemoryWeatherRepository()


@pytest.fixture
def empty_prediction_repository():
    """Empty prediction repository for testing."""
    return InMemoryPredictionRepository()


@pytest.fixture
def populated_weather_repository(sample_weather_data):
    """Weather repository populated with sample data."""
    repo = InMemoryWeatherRepository()
    # Note: This fixture will be populated in tests that need it
    return repo


@pytest.fixture
async def async_populated_weather_repository(sample_weather_data):
    """Async populated weather repository for testing."""
    repo = InMemoryWeatherRepository()
    await repo.save_weather_data(sample_weather_data)
    return repo


# Skip e2e tests by default
def pytest_collection_modifyitems(config, items):
    """Skip e2e tests by default unless explicitly requested."""
    # If user explicitly specified "-m" option, respect it
    markexpr = config.getoption("-m", "")
    if markexpr and ("e2e" in markexpr or markexpr == ""):
        return
    
    # Otherwise, skip e2e tests by default
    skip_e2e = pytest.mark.skip(reason="E2E tests are skipped by default. Use '-m e2e' or '-m \"\"' to run them.")
    for item in items:
        if "e2e" in item.keywords:
            item.add_marker(skip_e2e)