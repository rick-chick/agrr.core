"""Tests for WeatherPredictInteractor."""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from agrr_core.usecase.interactors.weather_predict_interactor import WeatherPredictInteractor
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.prediction_forecast_entity import Forecast
from agrr_core.entity.exceptions.file_error import FileError


class TestWeatherPredictInteractor:
    """Test cases for WeatherPredictInteractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_weather_gateway = Mock()
        self.mock_prediction_gateway = Mock()
        
        # Setup async mocks for weather gateway methods
        self.mock_weather_gateway.get = AsyncMock()
        self.mock_weather_gateway.create = AsyncMock()
        
        # Setup async mocks for prediction gateway methods
        self.mock_prediction_gateway.read_historical_data = AsyncMock()
        self.mock_prediction_gateway.predict = AsyncMock()
        self.mock_prediction_gateway.create = AsyncMock()
        
        self.interactor = WeatherPredictInteractor(
            weather_gateway=self.mock_weather_gateway,
            prediction_gateway=self.mock_prediction_gateway
        )
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful prediction execution."""
        # Setup mocks
        weather_data = [
            WeatherData(time=datetime(2024, 1, i), temperature_2m_mean=15.0) 
            for i in range(1, 31)  # 30 records
        ]
        self.mock_prediction_gateway.read_historical_data.return_value = weather_data
        
        predictions = [
            Forecast(date=datetime(2024, 2, 1), predicted_value=17.0)
        ]
        self.mock_prediction_gateway.predict.return_value = predictions
        
        # Execute
        result = await self.interactor.execute(
            input_source="input.json",
            output_destination="output.json",
            prediction_days=7
        )
        
        # Verify calls
        self.mock_prediction_gateway.read_historical_data.assert_called_once_with("input.json")
        self.mock_prediction_gateway.predict.assert_called_once_with(
            weather_data, 'temperature', {'prediction_days': 7}
        )
        self.mock_prediction_gateway.create.assert_called_once_with(predictions, "output.json")
        
        # Verify result
        assert result == predictions
    
    @pytest.mark.asyncio
    async def test_execute_invalid_input_format(self):
        """Test execute with invalid input format."""
        with pytest.raises(ValueError, match="Invalid input data source format"):
            await self.interactor.execute(
                input_source="input.txt",
                output_destination="output.json",
                prediction_days=7
            )
    
    @pytest.mark.asyncio
    async def test_execute_invalid_output_path(self):
        """Test execute with invalid output path."""
        with pytest.raises(ValueError, match="Invalid output destination format"):
            await self.interactor.execute(
                input_source="input.json",
                output_destination="output.xyz",
                prediction_days=7
            )
    
    @pytest.mark.asyncio
    async def test_execute_no_data(self):
        """Test execute with no weather data."""
        self.mock_prediction_gateway.read_historical_data.return_value = []
        
        with pytest.raises(ValueError, match="No weather data provided"):
            await self.interactor.execute(
                input_source="input.json",
                output_destination="output.json",
                prediction_days=7
            )
    
    @pytest.mark.asyncio
    async def test_execute_insufficient_data(self):
        """Test execute with insufficient data."""
        weather_data = [
            WeatherData(time=datetime(2024, 1, i), temperature_2m_mean=15.0) 
            for i in range(1, 10)  # Only 9 records
        ]
        self.mock_prediction_gateway.read_historical_data.return_value = weather_data
        
        with pytest.raises(ValueError, match="Insufficient data for prediction"):
            await self.interactor.execute(
                input_source="input.json",
                output_destination="output.json",
                prediction_days=7
            )
    
    @pytest.mark.asyncio
    async def test_execute_missing_temperature_data(self):
        """Test execute with missing temperature data."""
        # Create 30 records with some missing temperature_2m_mean
        weather_data = [
            WeatherData(time=datetime(2024, 1, i), temperature_2m_mean=15.0 if i <= 25 else None) 
            for i in range(1, 31)  # 30 records, last 5 have None temperature
        ]
        self.mock_prediction_gateway.read_historical_data.return_value = weather_data
        
        with pytest.raises(ValueError, match="Temperature data.*is missing"):
            await self.interactor.execute(
                input_source="input.json",
                output_destination="output.json",
                prediction_days=7
            )
    
    @pytest.mark.asyncio
    async def test_execute_optional_fields_can_be_none(self):
        """Test that optional fields (humidity, sunshine, weather_code) can be None."""
        # Create 30 records with required temperature but optional fields as None
        weather_data = [
            WeatherData(
                time=datetime(2024, 1, i), 
                temperature_2m_mean=15.0,
                sunshine_duration=None,  # Optional field
                weather_code=None  # Optional field
            ) 
            for i in range(1, 31)  # 30 records
        ]
        self.mock_prediction_gateway.read_historical_data.return_value = weather_data
        
        predictions = [
            Forecast(date=datetime(2024, 2, 1), predicted_value=17.0)
        ]
        self.mock_prediction_gateway.predict.return_value = predictions
        
        # Should succeed because temperature is present and optional fields can be None
        result = await self.interactor.execute(
            input_source="input.json",
            output_destination="output.json",
            prediction_days=7
        )
        
        assert result == predictions
    
    @pytest.mark.asyncio
    async def test_execute_file_error(self):
        """Test execute with file error."""
        self.mock_prediction_gateway.read_historical_data.side_effect = FileError("File not found")
        
        with pytest.raises(FileError, match="File not found"):
            await self.interactor.execute(
                input_source="input.json",
                output_destination="output.json",
                prediction_days=7
            )
