"""Tests for WeatherDataResponseDTO."""

import pytest

from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO


class TestWeatherDataResponseDTO:
    """Test WeatherDataResponseDTO."""
    
    def test_creation(self):
        """Test creating WeatherDataResponseDTO."""
        dto = WeatherDataResponseDTO(
            time="2023-01-01T00:00:00",
            temperature_2m_max=25.0,
            temperature_2m_min=15.0,
            temperature_2m_mean=20.0,
            precipitation_sum=5.0,
            sunshine_duration=28800.0,
            sunshine_hours=8.0
        )
        
        assert dto.time == "2023-01-01T00:00:00"
        assert dto.temperature_2m_max == 25.0
        assert dto.temperature_2m_min == 15.0
        assert dto.temperature_2m_mean == 20.0
        assert dto.precipitation_sum == 5.0
        assert dto.sunshine_duration == 28800.0
        assert dto.sunshine_hours == 8.0
