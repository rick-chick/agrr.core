"""Tests for weather interactors."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from agrr_core.usecase.interactors.weather_interactor import (
    FetchWeatherDataInteractor,
    PredictWeatherInteractor,
)
from agrr_core.usecase.dto.weather_dto import (
    WeatherDataRequestDTO,
    PredictionRequestDTO,
)
from agrr_core.entity import WeatherData
from agrr_core.entity.exceptions.weather_exceptions import (
    InvalidLocationError,
    InvalidDateRangeError,
    PredictionError,
)


class TestFetchWeatherDataInteractor:
    """Test FetchWeatherDataInteractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_weather_output_port = AsyncMock()
        self.interactor = FetchWeatherDataInteractor(self.mock_weather_output_port)
    
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
        
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.return_value = mock_weather_data
        
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
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.assert_called_once_with(
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
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.assert_not_called()
    
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
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_empty_result(self):
        """Test execution with empty weather data."""
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.return_value = []
        
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


class TestPredictWeatherInteractor:
    """Test PredictWeatherInteractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_weather_output_port = AsyncMock()
        self.mock_prediction_output_port = AsyncMock()
        self.interactor = PredictWeatherInteractor(
            self.mock_weather_output_port,
            self.mock_prediction_output_port
        )
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful prediction execution."""
        # Setup mock historical data
        mock_historical_data = []
        for i in range(30):  # 30 days of data
            mock_historical_data.append(
                WeatherData(
                    time=datetime(2023, 1, i + 1),
                    temperature_2m_mean=20.0 + i * 0.1,  # Slight trend
                    temperature_2m_max=25.0 + i * 0.1,
                    temperature_2m_min=15.0 + i * 0.1,
                    precipitation_sum=5.0,
                    sunshine_duration=28800.0,
                )
            )
        
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.return_value = mock_historical_data
        self.mock_prediction_output_port.save_forecast.return_value = None
        
        # Execute
        request = PredictionRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-30",
            prediction_days=7
        )
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert len(result.historical_data) == 30
        assert len(result.forecast) == 7
        assert result.model_metrics is not None
        assert result.model_metrics["training_data_points"] == 30
        assert result.model_metrics["prediction_days"] == 7
        assert result.model_metrics["model_type"] == "Prophet"
        
        # Check historical data
        first_historical = result.historical_data[0]
        assert first_historical.time == "2023-01-01T00:00:00"
        assert first_historical.temperature_2m_mean == 20.0
        assert first_historical.sunshine_hours == 8.0
        
        # Check forecast data
        first_forecast = result.forecast[0]
        assert first_forecast.date.startswith("2023-01-31")  # Next day after historical data
        assert isinstance(first_forecast.predicted_value, float)
        assert first_forecast.confidence_lower is not None
        assert first_forecast.confidence_upper is not None
        
        # Verify mocks were called correctly
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.assert_called_once_with(
            35.7, 139.7, "2023-01-01", "2023-01-30"
        )
        self.mock_prediction_output_port.save_forecast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_no_historical_data(self):
        """Test execution with no historical data."""
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.return_value = []
        
        request = PredictionRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-30",
            prediction_days=7
        )
        
        with pytest.raises(PredictionError, match="No historical data available"):
            await self.interactor.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_no_valid_temperature_data(self):
        """Test execution with no valid temperature data."""
        # Historical data with None temperature values
        mock_historical_data = [
            WeatherData(
                time=datetime(2023, 1, 1),
                temperature_2m_mean=None,  # No valid temperature data
                temperature_2m_max=None,
                temperature_2m_min=None,
            ),
        ]
        
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.return_value = mock_historical_data
        
        request = PredictionRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-01",
            prediction_days=7
        )
        
        with pytest.raises(PredictionError, match="No valid temperature data"):
            await self.interactor.execute(request)
    
    @pytest.mark.asyncio
    async def test_execute_invalid_location(self):
        """Test execution with invalid location."""
        request = PredictionRequestDTO(
            latitude=91.0,  # Invalid latitude
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-30",
            prediction_days=7
        )
        
        with pytest.raises(InvalidLocationError):
            await self.interactor.execute(request)
        
        # Verify mocks were not called
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.assert_not_called()
        self.mock_prediction_output_port.save_forecast.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_invalid_date_range(self):
        """Test execution with invalid date range."""
        request = PredictionRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="invalid-date",  # Invalid date format
            end_date="2023-01-30",
            prediction_days=7
        )
        
        with pytest.raises(InvalidLocationError):  # Should be wrapped as InvalidLocationError
            await self.interactor.execute(request)
        
        # Verify mocks were not called
        self.mock_weather_output_port.get_weather_data_by_location_and_date_range.assert_not_called()
        self.mock_prediction_output_port.save_forecast.assert_not_called()
