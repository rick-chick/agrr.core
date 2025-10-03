"""Tests for weather repository."""

import pytest
from unittest.mock import Mock, patch
import requests
from datetime import datetime

from agrr_core.adapter.repositories.weather_repository import (
    OpenMeteoWeatherRepository,
    InMemoryWeatherRepository,
)
from agrr_core.entity import WeatherData
from agrr_core.entity.exceptions.weather_exceptions import (
    WeatherAPIError,
    WeatherDataNotFoundError,
)


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
        
        # Test
        with pytest.raises(WeatherAPIError, match="Failed to fetch weather data from API"):
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
        
        # Test
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
                # Missing other required fields
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test
        with pytest.raises(WeatherAPIError, match="Invalid API response format"):
            await self.repository.get_weather_data_by_location_and_date_range(
                35.7, 139.7, "2023-01-01", "2023-01-01"
            )
    
    @pytest.mark.asyncio
    async def test_safe_get_method(self):
        """Test _safe_get helper method."""
        # Test valid index
        data = [1, 2, 3]
        assert self.repository._safe_get(data, 0) == 1
        assert self.repository._safe_get(data, 2) == 3
        
        # Test out of bounds
        assert self.repository._safe_get(data, 5) is None
        
        # Test empty list
        assert self.repository._safe_get([], 0) is None
        
        # Test None list
        assert self.repository._safe_get(None, 0) is None


class TestInMemoryWeatherRepository:
    """Test InMemoryWeatherRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.repository = InMemoryWeatherRepository()
    
    @pytest.mark.asyncio
    async def test_save_and_get_weather_data(self):
        """Test saving and retrieving weather data."""
        # Create test data
        weather_data = [
            WeatherData(
                time=datetime(2023, 1, 1),
                temperature_2m_mean=20.0,
                temperature_2m_max=25.0,
                temperature_2m_min=15.0,
            ),
            WeatherData(
                time=datetime(2023, 1, 2),
                temperature_2m_mean=21.0,
                temperature_2m_max=26.0,
                temperature_2m_min=16.0,
            ),
            WeatherData(
                time=datetime(2023, 1, 15),  # Outside date range
                temperature_2m_mean=22.0,
                temperature_2m_max=27.0,
                temperature_2m_min=17.0,
            ),
        ]
        
        # Save data
        await self.repository.save_weather_data(weather_data)
        
        # Retrieve data within date range
        result = await self.repository.get_weather_data_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-10"
        )
        
        # Should return only data within date range
        assert len(result) == 2
        assert result[0].time == datetime(2023, 1, 1)
        assert result[1].time == datetime(2023, 1, 2)
    
    @pytest.mark.asyncio
    async def test_empty_repository(self):
        """Test retrieving from empty repository."""
        result = await self.repository.get_weather_data_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-01"
        )
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_clear_repository(self):
        """Test clearing repository."""
        # Add some data
        weather_data = [
            WeatherData(time=datetime(2023, 1, 1), temperature_2m_mean=20.0)
        ]
        await self.repository.save_weather_data(weather_data)
        
        # Clear repository
        self.repository.clear()
        
        # Verify it's empty
        result = await self.repository.get_weather_data_by_location_and_date_range(
            35.7, 139.7, "2023-01-01", "2023-01-01"
        )
        
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_date_range_filtering(self):
        """Test date range filtering."""
        # Create data spanning multiple months
        weather_data = []
        for day in range(1, 32):  # January has 31 days
            weather_data.append(
                WeatherData(
                    time=datetime(2023, 1, day),
                    temperature_2m_mean=20.0 + day * 0.1
                )
            )
        
        await self.repository.save_weather_data(weather_data)
        
        # Test specific date range
        result = await self.repository.get_weather_data_by_location_and_date_range(
            35.7, 139.7, "2023-01-10", "2023-01-20"
        )
        
        # Should return 11 days (10th to 20th inclusive)
        assert len(result) == 11
        assert result[0].time == datetime(2023, 1, 10)
        assert result[-1].time == datetime(2023, 1, 20)
