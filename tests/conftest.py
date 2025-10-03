"""Test configuration and fixtures."""

import pytest
import asyncio
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


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Markers for different test types
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "entity: mark test as entity layer test")
    config.addinivalue_line("markers", "usecase: mark test as use case layer test")
    config.addinivalue_line("markers", "adapter: mark test as adapter layer test")
    config.addinivalue_line("markers", "framework: mark test as framework layer test")