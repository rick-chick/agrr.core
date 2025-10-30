"""Tests for WeatherGatewayAdapter."""

import pytest
from unittest.mock import Mock
from datetime import datetime

from agrr_core.adapter.gateways.weather_gateway_adapter import WeatherGatewayAdapter
from agrr_core.entity import WeatherData, Location
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO

class TestWeatherGatewayAdapter:
    """Test WeatherGatewayAdapter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_file_gateway = Mock()
        self.mock_api_gateway = Mock()
        self.gateway = WeatherGatewayAdapter(
            self.mock_file_gateway,
            self.mock_api_gateway
        )

    def test_get_by_location_and_date_range(self):
        """Test get_by_location_and_date_range delegates to API repository."""
        # Mock response
        location = Location(
            latitude=35.6762,
            longitude=139.6911,
            elevation=37.0,
            timezone="Asia/Tokyo"
        )
        weather_data = [
            WeatherData(
                time=datetime(2023, 1, 1),
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
                temperature_2m_mean=20.0,
                precipitation_sum=5.0,
                sunshine_duration=28800.0,
                wind_speed_10m=5.5,
                weather_code=0
            )
        ]
        expected_dto = WeatherDataWithLocationDTO(
            weather_data_list=weather_data,
            location=location
        )
        self.mock_api_gateway.get_by_location_and_date_range.return_value = expected_dto
        
        # Test
        result = self.gateway.get_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-02"
        )
        
        # Assertions
        assert result == expected_dto
        self.mock_api_gateway.get_by_location_and_date_range.assert_called_once_with(
            35.7, 139.7, "2023-01-01", "2023-01-02"
        )

    def test_get_forecast(self):
        """Test get_forecast delegates to API repository."""
        # Mock response
        location = Location(
            latitude=35.6762,
            longitude=139.6911,
            elevation=37.0,
            timezone="Asia/Tokyo"
        )
        weather_data = [
            WeatherData(
                time=datetime(2023, 1, i + 1),
                temperature_2m_max=25.0 + i,
                temperature_2m_min=15.0 + i,
                temperature_2m_mean=20.0 + i,
                precipitation_sum=5.0,
                sunshine_duration=28800.0,
                wind_speed_10m=5.5,
                weather_code=0
            )
            for i in range(16)
        ]
        expected_dto = WeatherDataWithLocationDTO(
            weather_data_list=weather_data,
            location=location
        )
        self.mock_api_gateway.get_forecast.return_value = expected_dto
        
        # Test
        result = self.gateway.get_forecast(35.7, 139.7)
        
        # Assertions
        assert result == expected_dto
        assert len(result.weather_data_list) == 16
        self.mock_api_gateway.get_forecast.assert_called_once_with(35.7, 139.7)

