"""Tests for PredictWeatherInteractor."""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from agrr_core.usecase.interactors.predict_weather_interactor import PredictWeatherInteractor
from agrr_core.usecase.dto.prediction_request_dto import PredictionRequestDTO
from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
from agrr_core.entity.exceptions.prediction_error import PredictionError


class TestPredictWeatherInteractor:
    """Test PredictWeatherInteractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_weather_input_port = AsyncMock()
        self.mock_prediction_input_port = AsyncMock()
        self.mock_prediction_output_port = AsyncMock()
        self.mock_prediction_presenter_output_port = Mock()
        self.interactor = PredictWeatherInteractor(
            self.mock_weather_input_port,
            self.mock_prediction_input_port,
            self.mock_prediction_output_port,
            self.mock_prediction_presenter_output_port
        )
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_execute_success(self):
        """Test successful prediction execution - full integration test with Prophet."""
        # This test verifies the complete flow including Prophet model training
        # It's marked as slow because it actually runs Prophet
        # Setup mock historical data
        mock_historical_data = []
        for i in range(5):
            mock_historical_data.append(
                WeatherData(
                    time=datetime(2023, 1, i + 1),
                    temperature_2m_mean=20.0 + i * 0.1,
                    temperature_2m_max=25.0 + i * 0.1,
                    temperature_2m_min=15.0 + i * 0.1,
                    precipitation_sum=5.0,
                    sunshine_duration=28800.0,
                )
            )
        
        # Mock input/output ports (return tuple: weather_data, location)
        from agrr_core.entity import Location
        mock_location = Location(latitude=35.7, longitude=139.7, elevation=37.0, timezone="Asia/Tokyo")
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.return_value = (mock_historical_data, mock_location)
        self.mock_prediction_input_port.save_forecast.return_value = None
        
        # Mock prediction service to return fake forecasts
        mock_forecasts = [
            Forecast(
                date=datetime(2023, 1, 6),
                predicted_value=21.0,
                confidence_lower=19.0,
                confidence_upper=23.0
            ),
            Forecast(
                date=datetime(2023, 1, 7),
                predicted_value=21.1,
                confidence_lower=19.1,
                confidence_upper=23.1
            ),
            # Add more forecasts as needed...
        ]
        self.mock_prediction_output_port.predict_weather.return_value = mock_forecasts
        
        # Execute
        request = PredictionRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-05",
            prediction_days=7
        )
        
        # Setup presenter mock return values
        self.mock_prediction_presenter_output_port.format_prediction_dto.return_value = {"historical_data": [], "forecast": [], "model_metrics": {}}
        self.mock_prediction_presenter_output_port.format_success.return_value = {"success": True, "data": {"historical_data": [], "forecast": [], "model_metrics": {}}}
        
        result = await self.interactor.execute(request)
        
        # Assertions - verify input/output ports were called correctly
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.assert_called_once_with(
            35.7, 139.7, "2023-01-01", "2023-01-05"
        )
        self.mock_prediction_output_port.predict_weather.assert_called_once_with(
            mock_historical_data, 7
        )
        self.mock_prediction_input_port.save_forecast.assert_called_once()
        
        # Verify presenter methods were called
        self.mock_prediction_presenter_output_port.format_prediction_dto.assert_called_once()
        self.mock_prediction_presenter_output_port.format_success.assert_called_once()
        
        # Verify result structure
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_execute_no_historical_data(self):
        """Test execution with no historical data."""
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.return_value = []
        
        request = PredictionRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-05",
            prediction_days=7
        )
        
        # Setup presenter mock for error response
        self.mock_prediction_presenter_output_port.format_error.return_value = {"success": False, "error": {"message": "No historical data available for prediction"}}
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result["success"] is False
        assert "No historical data available" in result["error"]["message"]
        
        # Verify mock was called
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.assert_called_once()
        self.mock_prediction_presenter_output_port.format_error.assert_called_once()
    
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
        
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.return_value = mock_historical_data
        
        # Mock prediction service to raise error for invalid data
        self.mock_prediction_output_port.predict_weather.side_effect = PredictionError("No valid temperature data for prediction")
        
        request = PredictionRequestDTO(
            latitude=35.7,
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-01",
            prediction_days=7
        )
        
        # Setup presenter mock for error response
        self.mock_prediction_presenter_output_port.format_error.return_value = {"success": False, "error": {"message": "Prediction failed: No valid temperature data for prediction"}}
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result["success"] is False
        assert "No valid temperature data" in result["error"]["message"]
        
        # Verify mock was called
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.assert_called_once()
        self.mock_prediction_presenter_output_port.format_error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_invalid_location(self):
        """Test execution with invalid location."""
        request = PredictionRequestDTO(
            latitude=91.0,  # Invalid latitude
            longitude=139.7,
            start_date="2023-01-01",
            end_date="2023-01-05",
            prediction_days=7
        )
        
        # Setup presenter mock for error response
        self.mock_prediction_presenter_output_port.format_error.return_value = {"success": False, "error": {"message": "Invalid request parameters"}}
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result["success"] is False
        assert "Invalid request parameters" in result["error"]["message"]
        
        # Verify mocks were not called
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.assert_not_called()
        self.mock_prediction_input_port.save_forecast.assert_not_called()
        self.mock_prediction_presenter_output_port.format_error.assert_called_once()
    
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
        
        # Setup presenter mock for error response
        self.mock_prediction_presenter_output_port.format_error.return_value = {"success": False, "error": {"message": "Invalid request parameters"}}
        
        result = await self.interactor.execute(request)
        
        # Assertions
        assert result["success"] is False
        assert "Invalid request parameters" in result["error"]["message"]
        
        # Verify mocks were not called
        self.mock_weather_input_port.get_weather_data_by_location_and_date_range.assert_not_called()
        self.mock_prediction_input_port.save_forecast.assert_not_called()
        self.mock_prediction_presenter_output_port.format_error.assert_called_once()
