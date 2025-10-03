"""Tests for WeatherData entity."""

import pytest
from datetime import datetime

from agrr_core.entity import WeatherData


class TestWeatherData:
    """Test WeatherData entity."""
    
    def test_weather_data_creation(self):
        """Test creating WeatherData entity."""
        time = datetime(2023, 1, 1)
        weather_data = WeatherData(
            time=time,
            temperature_2m_max=25.0,
            temperature_2m_min=15.0,
            temperature_2m_mean=20.0,
            precipitation_sum=5.0,
            sunshine_duration=28800.0  # 8 hours in seconds
        )
        
        assert weather_data.time == time
        assert weather_data.temperature_2m_max == 25.0
        assert weather_data.temperature_2m_min == 15.0
        assert weather_data.temperature_2m_mean == 20.0
        assert weather_data.precipitation_sum == 5.0
        assert weather_data.sunshine_duration == 28800.0
    
    def test_sunshine_hours_property(self):
        """Test sunshine_hours computed property."""
        weather_data = WeatherData(
            time=datetime(2023, 1, 1),
            sunshine_duration=28800.0  # 8 hours in seconds
        )
        
        assert weather_data.sunshine_hours == 8.0
    
    def test_sunshine_hours_none(self):
        """Test sunshine_hours when sunshine_duration is None."""
        weather_data = WeatherData(
            time=datetime(2023, 1, 1),
            sunshine_duration=None
        )
        
        assert weather_data.sunshine_hours is None
    
    def test_optional_fields(self):
        """Test creating WeatherData with only required fields."""
        time = datetime(2023, 1, 1)
        weather_data = WeatherData(time=time)
        
        assert weather_data.time == time
        assert weather_data.temperature_2m_max is None
        assert weather_data.temperature_2m_min is None
        assert weather_data.temperature_2m_mean is None
        assert weather_data.precipitation_sum is None
        assert weather_data.sunshine_duration is None
