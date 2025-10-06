"""Tests for weather mapper."""

import pytest
import pandas as pd
from datetime import datetime

from agrr_core.adapter.mappers.weather_mapper import WeatherMapper
from agrr_core.entity import WeatherData
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO


class TestWeatherMapper:
    """Test WeatherMapper."""
    
    def test_entity_to_dto(self):
        """Test converting WeatherData entity to DTO."""
        weather_data = WeatherData(
            time=datetime(2023, 1, 1),
            temperature_2m_max=25.0,
            temperature_2m_min=15.0,
            temperature_2m_mean=20.0,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
            wind_speed_10m=5.5,
            weather_code=0,
        )
        
        dto = WeatherMapper.entity_to_dto(weather_data)
        
        assert isinstance(dto, WeatherDataResponseDTO)
        assert dto.time == "2023-01-01T00:00:00"
        assert dto.temperature_2m_max == 25.0
        assert dto.temperature_2m_min == 15.0
        assert dto.temperature_2m_mean == 20.0
        assert dto.precipitation_sum == 5.0
        assert dto.sunshine_duration == 28800.0
        assert dto.sunshine_hours == 8.0
        assert dto.wind_speed_10m == 5.5
        assert dto.weather_code == 0
    
    def test_entity_to_dto_with_none_values(self):
        """Test converting WeatherData entity with None values to DTO."""
        weather_data = WeatherData(
            time=datetime(2023, 1, 1),
            temperature_2m_max=None,
            temperature_2m_min=15.0,
            temperature_2m_mean=20.0,
            precipitation_sum=None,
            sunshine_duration=None,
            wind_speed_10m=None,
            weather_code=None,
        )
        
        dto = WeatherMapper.entity_to_dto(weather_data)
        
        assert dto.time == "2023-01-01T00:00:00"
        assert dto.temperature_2m_max is None
        assert dto.temperature_2m_min == 15.0
        assert dto.temperature_2m_mean == 20.0
        assert dto.precipitation_sum is None
        assert dto.sunshine_duration is None
        assert dto.sunshine_hours is None
        assert dto.wind_speed_10m is None
        assert dto.weather_code is None
    
    
