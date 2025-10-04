"""Tests for WeatherDataRequestDTO."""

import pytest

from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO


class TestWeatherDataRequestDTO:
    """Test WeatherDataRequestDTO."""
    
    def test_creation(self):
        """Test creating WeatherDataRequestDTO."""
        dto = WeatherDataRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        
        assert dto.latitude == 35.7
        assert dto.longitude == 139.7
        assert dto.start_date == "2023-01-01"
        assert dto.end_date == "2023-12-31"
