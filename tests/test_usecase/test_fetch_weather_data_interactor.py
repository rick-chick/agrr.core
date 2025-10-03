"""Tests for FetchWeatherDataInteractor."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime

from agrr_core.usecase.interactors.fetch_weather_data_interactor import FetchWeatherDataInteractor
from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO
from agrr_core.entity import WeatherData
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError


class TestFetchWeatherDataInteractor:
    """Test FetchWeatherDataInteractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_weather_input_port = AsyncMock()
        self.interactor = FetchWeatherDataInteractor(self.mock_weather_input_port)
    
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
        
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.return_value = mock_weather_data
        
        # Execute
        request = WeatherDataRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-02"
        )
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result.total_count == 2
        assert len(result.data) == 2
        
        # Check first record
        first_record = result.data[0]
        assert first_record.time == "2023-01-01T00:00:00"
        assert first_record.temperature_2m_max == 25.0
        assert first_record.temperature_2m_min == 15.0
        assert first_record.temperature_2m_mean == 20.0
        assert first_record.precipitation_sum == 5.0
        assert first_record.sunshine_duration == 28800.0
        assert first_record.sunshine_hours == 8.0
        
        # Check second record
        second_record = result.data[1]
        assert second_record.time == "2023-01-02T00:00:00"
        assert second_record.temperature_2m_max == 26.0
        assert second_record.sunshine_hours == 7.0
        
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
        
        with pytest.raises(InvalidLocationError):
            await self.interactor.execute(request)
        
        # Verify mock was not called
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_invalid_date_range(self):
        """Test execution with invalid date range."""
        request = WeatherDataRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="invalid-date",  # Invalid date format
            end_date="2023-01-02"
        )
        
        with pytest.raises(InvalidLocationError):  # Should be wrapped as InvalidLocationError
            await self.interactor.execute(request)
        
        # Verify mock was not called
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_empty_result(self):
        """Test execution with empty weather data."""
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.return_value = []
        
        request = WeatherDataRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-02"
        )
        
        result = await self.interactor.execute(request)
        
        # Should return empty result
        assert result.total_count == 0
        assert len(result.data) == 0
