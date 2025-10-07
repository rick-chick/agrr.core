"""Tests for WeatherGetForecastInteractor."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from agrr_core.usecase.interactors.weather_get_forecast_interactor import WeatherGetForecastInteractor
from agrr_core.usecase.dto.weather_forecast_request_dto import WeatherForecastRequestDTO
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO
from agrr_core.entity import WeatherData, Location


class TestWeatherGetForecastInteractor:
    """Test WeatherGetForecastInteractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_weather_gateway = AsyncMock()
        self.mock_weather_presenter_output_port = Mock()
        self.interactor = WeatherGetForecastInteractor(
            self.mock_weather_gateway, 
            self.mock_weather_presenter_output_port
        )
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful 16-day forecast retrieval."""
        # Setup mock data - 16 days of forecast
        mock_weather_data = [
            WeatherData(
                time=datetime(2023, 1, i + 1),
                temperature_2m_max=25.0 + i * 0.5,
                temperature_2m_min=15.0 + i * 0.3,
                temperature_2m_mean=20.0 + i * 0.4,
                precipitation_sum=5.0 - i * 0.2,
                sunshine_duration=28800.0 + i * 100,
            )
            for i in range(16)
        ]
        
        mock_location = Location(
            latitude=35.7, 
            longitude=139.7, 
            elevation=37.0, 
            timezone="Asia/Tokyo"
        )
        mock_weather_data_with_location = WeatherDataWithLocationDTO(
            weather_data_list=mock_weather_data,
            location=mock_location
        )
        self.mock_weather_gateway.get_forecast.return_value = mock_weather_data_with_location
        
        # Setup presenter mock return values
        self.mock_weather_presenter_output_port.format_weather_data_list_dto.return_value = {
            "data": [], 
            "total_count": 16
        }
        self.mock_weather_presenter_output_port.format_success.return_value = {
            "success": True, 
            "data": {"data": [], "total_count": 16}
        }
        
        # Execute
        request = WeatherForecastRequestDTO(
            latitude=35.7,
            longitude=139.7
        )
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result["success"] is True
        assert result["data"]["total_count"] == 16
        
        # Check that presenter methods were called
        self.mock_weather_presenter_output_port.format_weather_data_list_dto.assert_called_once()
        self.mock_weather_presenter_output_port.format_success.assert_called_once()
        
        # Verify mock was called correctly
        self.mock_weather_gateway.get_forecast.assert_called_once_with(35.7, 139.7)
    
    @pytest.mark.asyncio
    async def test_execute_invalid_location(self):
        """Test execution with invalid location."""
        request = WeatherForecastRequestDTO(
            latitude=91.0,  # Invalid latitude
            longitude=139.7
        )
        
        # Setup presenter mock for error response
        self.mock_weather_presenter_output_port.format_error.return_value = {
            "success": False, 
            "error": {"message": "Invalid location coordinates"}
        }
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result["success"] is False
        assert "Invalid location coordinates" in result["error"]["message"]
        
        # Verify gateway was not called
        self.mock_weather_gateway.get_forecast.assert_not_called()
        self.mock_weather_presenter_output_port.format_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_api_error(self):
        """Test execution with API error."""
        from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
        
        self.mock_weather_gateway.get_forecast.side_effect = WeatherAPIError("API Error")
        
        # Setup presenter mock for error response
        self.mock_weather_presenter_output_port.format_error.return_value = {
            "success": False, 
            "error": {"message": "Weather forecast fetch failed: API Error"}
        }
        
        request = WeatherForecastRequestDTO(
            latitude=35.7,
            longitude=139.7
        )
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result["success"] is False
        self.mock_weather_presenter_output_port.format_error.assert_called_once()

