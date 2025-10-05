"""Tests for FetchWeatherDataInteractor."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from agrr_core.usecase.interactors.weather_fetch_interactor import FetchWeatherDataInteractor
from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO
from agrr_core.entity import WeatherData
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError


class TestFetchWeatherDataInteractor:
    """Test FetchWeatherDataInteractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_weather_input_port = AsyncMock()
        self.mock_weather_presenter_output_port = Mock()
        self.interactor = FetchWeatherDataInteractor(self.mock_weather_input_port, self.mock_weather_presenter_output_port)
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution."""
        # Setup mock data
        mock_weather_data = [
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
        ]
        
        # Mock return value should be tuple (weather_data, location)
        from agrr_core.entity import Location
        mock_location = Location(latitude=35.7, longitude=139.7, elevation=37.0, timezone="Asia/Tokyo")
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.return_value = (mock_weather_data, mock_location)
        
        # Setup presenter mock return values
        self.mock_weather_presenter_output_port.format_weather_data_list_dto.return_value = {"data": [], "total_count": 2}
        self.mock_weather_presenter_output_port.format_success.return_value = {"success": True, "data": {"data": [], "total_count": 2}}
        
        # Execute
        request = WeatherDataRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-02"
        )
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result["success"] is True
        assert result["data"]["total_count"] == 2
        
        # Check that presenter methods were called
        self.mock_weather_presenter_output_port.format_weather_data_list_dto.assert_called_once()
        self.mock_weather_presenter_output_port.format_success.assert_called_once()
        
        # Verify mock was called correctly
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.assert_called_once_with(
            35.7, 139.7, "2023-01-01", "2023-01-02"
        )
    
    @pytest.mark.asyncio
    async def test_execute_invalid_location(self):
        """Test execution with invalid location."""
        request = WeatherDataRequestDTO(
            latitude=91.0,  # Invalid latitude
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-02"
        )
        
        # Setup presenter mock for error response
        self.mock_weather_presenter_output_port.format_error.return_value = {"success": False, "error": {"message": "Invalid request parameters"}}
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result["success"] is False
        assert "Invalid request parameters" in result["error"]["message"]
        
        # Verify mock was not called
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.assert_not_called()
        self.mock_weather_presenter_output_port.format_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_invalid_date_range(self):
        """Test execution with invalid date range."""
        request = WeatherDataRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="invalid-date",  # Invalid date format
            end_date="2023-01-02"
        )
        
        # Setup presenter mock for error response
        self.mock_weather_presenter_output_port.format_error.return_value = {"success": False, "error": {"message": "Invalid request parameters"}}
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result["success"] is False
        assert "Invalid request parameters" in result["error"]["message"]
        
        # Verify mock was not called
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.assert_not_called()
        self.mock_weather_presenter_output_port.format_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_empty_result(self):
        """Test execution with empty weather data."""
        from agrr_core.entity import Location
        mock_location = Location(latitude=35.7, longitude=139.7)
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.return_value = ([], mock_location)
        
        request = WeatherDataRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-02"
        )
        
        # Setup presenter mock for empty result
        self.mock_weather_presenter_output_port.format_weather_data_list_dto.return_value = {"data": [], "total_count": 0}
        self.mock_weather_presenter_output_port.format_success.return_value = {"success": True, "data": {"data": [], "total_count": 0}}
        
        result = await self.interactor.execute(request)
        
        # Should return empty result
        assert result["success"] is True
        assert result["data"]["total_count"] == 0
