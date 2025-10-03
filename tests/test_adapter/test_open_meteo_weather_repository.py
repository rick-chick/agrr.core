"""Tests for OpenMeteoWeatherRepository."""

import pytest
from unittest.mock import Mock, patch
import requests
from datetime import datetime

from agrr_core.adapter.repositories.open_meteo_weather_repository import OpenMeteoWeatherRepository
from agrr_core.entity import WeatherData
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError


class TestOpenMeteoWeatherRepository:
    """Test OpenMeteoWeatherRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.repository = OpenMeteoWeatherRepository()
    
    def test_init(self):
        """Test repository initialization."""
        repo = OpenMeteoWeatherRepository()
        assert repo.base_url == "https://archive-api.open-meteo.com/v1/archive"
        
        custom_repo = OpenMeteoWeatherRepository("https://custom-api.com")
        assert custom_repo.base_url == "https://custom-api.com"
    
    @patch('requests.get')
    @pytest.mark.asyncio
    async def test_get_weather_data_success(self, mock_get):
        """Test successful weather data retrieval."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "daily": {
                "time": ["2023-01-01", "2023-01-02"],
                "temperature_2m_max": [25.0, 26.0],
                "temperature_2m_min": [15.0, 16.0],
                "temperature_2m_mean": [20.0, 21.0],
                "precipitation_sum": [5.0, 3.0],
                "sunshine_duration": [28800.0, 25200.0],
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        result = await self.repository.get_weather_data_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-02"
        )
        
        # Assertions
        assert len(result) == 2
        assert isinstance(result[0], WeatherData)
        assert result[0].time == datetime(2023, 1, 1)
        assert result[0].temperature_2m_max == 25.0
        assert result[0].temperature_2m_mean == 20.0
        assert result[0].sunshine_hours == 8.0
        
        assert result[1].time == datetime(2023, 1, 2)
        assert result[1].temperature_2m_max == 26.0
        assert result[1].sunshine_hours == 7.0
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "latitude" in call_args[1]["params"]
        assert "longitude" in call_args[1]["params"]
        assert call_args[1]["params"]["latitude"] == 35.7
        assert call_args[1]["params"]["longitude"] == 139.7
    
    @patch('requests.get')
    @pytest.mark.asyncio
    async def test_get_weather_data_with_none_values(self, mock_get):
        """Test weather data retrieval with None values."""
        # Mock API response with None values
        mock_response = Mock()
        mock_response.json.return_value = {
            "daily": {
                "time": ["2023-01-01"],
                "temperature_2m_max": [None],
                "temperature_2m_min": [15.0],
                "temperature_2m_mean": [20.0],
                "precipitation_sum": [5.0],
                "sunshine_duration": [None],
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        result = await self.repository.get_weather_data_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-01"
        )
        
        # Assertions
        assert len(result) == 1
        assert result[0].temperature_2m_max is None
        assert result[0].temperature_2m_min == 15.0
        assert result[0].sunshine_duration is None
        assert result[0].sunshine_hours is None
    
    @patch('requests.get')
    @pytest.mark.asyncio
    async def test_get_weather_data_api_error(self, mock_get):
        """Test API error handling."""
        # Mock API error
        mock_get.side_effect = requests.RequestException("API Error")
        
        with pytest.raises(WeatherAPIError, match="Failed to fetch weather data"):
            await self.repository.get_weather_data_by_location_and_date_range(
                35.7, 139.7, "2023-01-01", "2023-01-01"
            )
    
    @patch('requests.get')
    @pytest.mark.asyncio
    async def test_get_weather_data_invalid_response(self, mock_get):
        """Test invalid API response handling."""
        # Mock invalid response
        mock_response = Mock()
        mock_response.json.return_value = {"invalid": "response"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with pytest.raises(WeatherDataNotFoundError, match="No daily weather data found"):
            await self.repository.get_weather_data_by_location_and_date_range(
                35.7, 139.7, "2023-01-01", "2023-01-01"
            )
    
    @patch('requests.get')
    @pytest.mark.asyncio
    async def test_get_weather_data_malformed_response(self, mock_get):
        """Test malformed API response handling."""
        # Mock malformed response
        mock_response = Mock()
        mock_response.json.return_value = {
            "daily": {
                "time": ["2023-01-01"],
                # Missing required fields
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with pytest.raises(WeatherAPIError, match="Invalid API response format"):
            await self.repository.get_weather_data_by_location_and_date_range(
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
