"""Tests for WeatherDataListResponseDTO."""

import pytest

from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO


class TestWeatherDataListResponseDTO:
    """Test WeatherDataListResponseDTO."""
    
    def test_creation(self):
        """Test creating WeatherDataListResponseDTO."""
        data = [
            WeatherDataResponseDTO(
                time="2023-01-01T00:00:00",
                temperature_2m_mean=20.0
            ),
            WeatherDataResponseDTO(
                time="2023-01-02T00:00:00",
                temperature_2m_mean=21.0
            ),
        ]
        
        dto = WeatherDataListResponseDTO(data=data, total_count=2)
        
        assert len(dto.data) == 2
        assert dto.total_count == 2
        assert dto.data[0].time == "2023-01-01T00:00:00"
        assert dto.data[1].time == "2023-01-02T00:00:00"
