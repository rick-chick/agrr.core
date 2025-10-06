"""Tests for WeatherAPIOpenMeteoRepository."""

import pytest
from unittest.mock import Mock, patch
import requests
from datetime import datetime

from agrr_core.adapter.repositories.weather_api_open_meteo_repository import WeatherAPIOpenMeteoRepository
from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError


class TestWeatherAPIOpenMeteoRepository:
    """Test WeatherAPIOpenMeteoRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create mock HTTP service
        from unittest.mock import AsyncMock
        self.mock_http_service = AsyncMock()
        self.mock_http_service.get.return_value = {
            'latitude': 35.6762,
            'longitude': 139.6503,
            'elevation': 10.0,
            'timezone': 'Asia/Tokyo',
            'daily': {
                'time': ['2024-01-01', '2024-01-02'],
                'temperature_2m_max': [25.0, 26.0],
                'temperature_2m_min': [15.0, 16.0],
                'temperature_2m_mean': [20.0, 21.0],
                'precipitation_sum': [5.0, 3.0],
                'sunshine_duration': [28800.0, 30000.0],
                'wind_speed_10m_max': [5.5, 6.2],
                'weather_code': [0, 1]
            }
        }
        self.repository = WeatherAPIOpenMeteoRepository(self.mock_http_service)
    
    def test_init(self):
        """Test repository initialization."""
        assert self.repository.http_service == self.mock_http_service
    
    @pytest.mark.asyncio
    async def test_get_weather_data_success(self):
        """Test successful weather data retrieval."""
        # Mock HTTP service response
        mock_response = {
            "latitude": 35.6762,
            "longitude": 139.6911,
            "elevation": 37.0,
            "timezone": "Asia/Tokyo",
            "daily": {
                "time": ["2023-01-01", "2023-01-02"],
                "temperature_2m_max": [25.0, 26.0],
                "temperature_2m_min": [15.0, 16.0],
                "temperature_2m_mean": [20.0, 21.0],
                "precipitation_sum": [5.0, 3.0],
                "sunshine_duration": [28800.0, 25200.0],
                "wind_speed_10m_max": [5.5, 6.2],
                "weather_code": [0, 1]
            }
        }
        self.mock_http_service.get.return_value = mock_response
        
        # Test
        weather_data_list = await self.repository.get_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-02"
        )
        
        # Assertions for weather data
        assert len(weather_data_list) == 2
        assert isinstance(weather_data_list[0], WeatherData)
        assert weather_data_list[0].time == datetime(2023, 1, 1)
        assert weather_data_list[0].temperature_2m_max == 25.0
        assert weather_data_list[0].temperature_2m_mean == 20.0
        assert weather_data_list[0].sunshine_hours == 8.0
        assert weather_data_list[0].wind_speed_10m == 5.5
        assert weather_data_list[0].weather_code == 0
        
        assert weather_data_list[1].time == datetime(2023, 1, 2)
        assert weather_data_list[1].temperature_2m_max == 26.0
        assert weather_data_list[1].sunshine_hours == 7.0
        assert weather_data_list[1].wind_speed_10m == 6.2
        assert weather_data_list[1].weather_code == 1
        
        # Location information is embedded in WeatherData entities
        # No separate location object is returned
        
        # Verify API call
        self.mock_http_service.get.assert_called_once()
        call_args = self.mock_http_service.get.call_args
        assert call_args[0][1]["latitude"] == 35.7
        assert call_args[0][1]["longitude"] == 139.7
    
    @pytest.mark.asyncio
    async def test_get_weather_data_with_none_values(self):
        """Test weather data retrieval with None values."""
        # Mock API response with None values
        mock_response = {
            "latitude": 35.7,
            "longitude": 139.7,
            "daily": {
                "time": ["2023-01-01"],
                "temperature_2m_max": [None],
                "temperature_2m_min": [15.0],
                "temperature_2m_mean": [20.0],
                "precipitation_sum": [5.0],
                "sunshine_duration": [None],
                "wind_speed_10m_max": [None],
                "weather_code": [None],
            }
        }
        self.mock_http_service.get.return_value = mock_response
        
        # Test
        weather_data_list = await self.repository.get_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-01"
        )
        
        # Assertions
        assert len(weather_data_list) == 1
        assert weather_data_list[0].temperature_2m_max is None
        assert weather_data_list[0].temperature_2m_min == 15.0
        assert weather_data_list[0].sunshine_duration is None
        assert weather_data_list[0].sunshine_hours is None
        assert weather_data_list[0].wind_speed_10m is None
        assert weather_data_list[0].weather_code is None
        # Location information is embedded in WeatherData entities
    
    @pytest.mark.asyncio
    async def test_get_weather_data_api_error(self):
        """Test API error handling."""
        # Mock API error
        from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
        self.mock_http_service.get.side_effect = WeatherAPIError("API Error")
        
        with pytest.raises(WeatherAPIError, match="API Error"):
            await self.repository.get_by_location_and_date_range(
                35.7, 139.7, "2023-01-01", "2023-01-01"
            )
    
    @pytest.mark.asyncio
    async def test_get_weather_data_invalid_response(self):
        """Test invalid API response handling."""
        # Mock invalid response
        mock_response = {"invalid": "response"}
        self.mock_http_service.get.return_value = mock_response
        
        with pytest.raises(WeatherDataNotFoundError, match="No daily weather data found"):
            await self.repository.get_by_location_and_date_range(
                35.7, 139.7, "2023-01-01", "2023-01-01"
            )
    
    @pytest.mark.asyncio
    async def test_get_weather_data_malformed_response(self):
        """Test malformed API response handling."""
        # Mock malformed response
        mock_response = {
            "daily": {
                "time": ["2023-01-01"],
                # Missing required fields
            }
        }
        self.mock_http_service.get.return_value = mock_response
        
        with pytest.raises(WeatherAPIError, match="Invalid API response format"):
            await self.repository.get_by_location_and_date_range(
                35.7, 139.7, "2023-01-01", "2023-01-01"
            )
    
    def test_safe_get_method(self):
        """Test _safe_get helper method."""
        # Test with valid data
        data = [1, 2, 3]
        assert self.repository._safe_get(data, 0) == 1
        assert self.repository._safe_get(data, 2) == 3
        
        # Test with None data
        assert self.repository._safe_get(None, 0) is None
        
        # Test with empty data
        assert self.repository._safe_get([], 0) is None
