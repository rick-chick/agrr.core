"""Integration tests for weather controller."""

import pytest
from unittest.mock import Mock, AsyncMock

from agrr_core.adapter.controllers.weather_controller import WeatherController
from agrr_core.adapter.services.weather_service_impl import WeatherServiceImpl
from agrr_core.adapter.services.prediction_service_impl import PredictionServiceImpl
from agrr_core.usecase.interactors.fetch_weather_data_interactor import FetchWeatherDataInteractor
from agrr_core.usecase.interactors.predict_weather_interactor import PredictWeatherInteractor
from agrr_core.adapter.repositories.in_memory_weather_repository import InMemoryWeatherRepository
from agrr_core.adapter.repositories.prediction_repository import InMemoryPredictionRepository
from agrr_core.entity import WeatherData
from datetime import datetime


class TestWeatherControllerIntegration:
    """Integration tests for WeatherController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use real repositories for integration testing
        self.weather_repo = InMemoryWeatherRepository()
        self.prediction_repo = InMemoryPredictionRepository()
        
        # Create real prediction service
        from agrr_core.adapter.services.prophet_weather_prediction_service import ProphetWeatherPredictionService
        self.prediction_service = ProphetWeatherPredictionService()
        
        # Create real interactors
        self.fetch_interactor = FetchWeatherDataInteractor(self.weather_repo)
        self.predict_interactor = PredictWeatherInteractor(self.weather_repo, self.prediction_repo, self.prediction_service)
        
        # Create services
        self.weather_service = WeatherServiceImpl(self.fetch_interactor)
        self.prediction_service_impl = PredictionServiceImpl(self.predict_interactor)
        
        # Create controller
        self.controller = WeatherController(self.weather_service, self.prediction_service_impl)
    
    @pytest.mark.asyncio
    async def test_get_weather_data_integration(self):
        """Test weather data fetching integration."""
        # Add test data to repository
        test_data = [
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
        
        await self.weather_repo.save_weather_data(test_data)
        
        # Test controller method
        result = await self.controller.get_weather_data(35.7, 139.7, "2023-01-01", "2023-01-02")
        
        # Assertions
        assert result["success"] is True
        assert result["total_count"] == 2
        assert len(result["data"]) == 2
        
        # Check first record
        first_record = result["data"][0]
        assert first_record["time"] == "2023-01-01T00:00:00"
        assert first_record["temperature_2m_max"] == 25.0
        assert first_record["temperature_2m_min"] == 15.0
        assert first_record["temperature_2m_mean"] == 20.0
        assert first_record["precipitation_sum"] == 5.0
        assert first_record["sunshine_duration"] == 28800.0
        assert first_record["sunshine_hours"] == 8.0
    
    def test_get_weather_data_sync_integration(self):
        """Test synchronous weather data fetching integration."""
        # Add test data to repository
        test_data = [
            WeatherData(
                time=datetime(2023, 1, 1),
                temperature_2m_mean=20.0,
                sunshine_duration=28800.0,
            ),
        ]
        
        # Use async save in sync test (not ideal but works for testing)
        import asyncio
        asyncio.run(self.weather_repo.save_weather_data(test_data))
        
        # Test controller method
        result = self.controller.get_weather_data_sync(35.7, 139.7, "2023-01-01", "2023-01-01")
        
        # Assertions
        assert result["success"] is True
        assert result["total_count"] == 1
        assert len(result["data"]) == 1
        
        first_record = result["data"][0]
        assert first_record["time"] == "2023-01-01T00:00:00"
        assert first_record["temperature_2m_mean"] == 20.0
        assert first_record["sunshine_hours"] == 8.0
    
    @pytest.mark.asyncio
    async def test_predict_weather_integration(self):
        """Test weather prediction integration."""
        # Add historical data for prediction
        historical_data = []
        for i in range(30):  # 30 days of data
            historical_data.append(
                WeatherData(
                    time=datetime(2023, 1, i + 1),
                    temperature_2m_mean=20.0 + i * 0.1,  # Slight trend
                    temperature_2m_max=25.0 + i * 0.1,
                    temperature_2m_min=15.0 + i * 0.1,
                    precipitation_sum=5.0,
                    sunshine_duration=28800.0,
                )
            )
        
        await self.weather_repo.save_weather_data(historical_data)
        
        # Test prediction
        result = await self.controller.predict_weather(
            35.7, 139.7, "2023-01-01", "2023-01-30", 7
        )
        
        # Assertions
        assert result["success"] is True
        assert len(result["historical_data"]) == 30
        assert len(result["forecast"]) == 7
        assert result["model_metrics"] is not None
        assert result["model_metrics"]["training_data_points"] == 30
        assert result["model_metrics"]["prediction_days"] == 7
        assert result["model_metrics"]["model_type"] == "Prophet"
        
        # Check forecast data structure
        first_forecast = result["forecast"][0]
        assert "date" in first_forecast
        assert "predicted_value" in first_forecast
        assert "confidence_lower" in first_forecast
        assert "confidence_upper" in first_forecast
        assert isinstance(first_forecast["predicted_value"], float)
    
    def test_predict_weather_sync_integration(self):
        """Test synchronous weather prediction integration."""
        # Add historical data for prediction
        historical_data = []
        for i in range(10):  # 10 days of data
            historical_data.append(
                WeatherData(
                    time=datetime(2023, 1, i + 1),
                    temperature_2m_mean=20.0 + i * 0.1,
                )
            )
        
        # Use async save in sync test
        import asyncio
        asyncio.run(self.weather_repo.save_weather_data(historical_data))
        
        # Test prediction
        result = self.controller.predict_weather_sync(
            35.7, 139.7, "2023-01-01", "2023-01-10", 3
        )
        
        # Assertions
        assert result["success"] is True
        assert len(result["historical_data"]) == 10
        assert len(result["forecast"]) == 3
        assert result["model_metrics"] is not None
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_location(self):
        """Test error handling for invalid location."""
        result = await self.controller.get_weather_data(91.0, 139.7, "2023-01-01", "2023-01-02")
        
        assert result["success"] is False
        assert result["error"] == "Invalid location parameters"
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_date_range(self):
        """Test error handling for invalid date range."""
        result = await self.controller.get_weather_data(35.7, 139.7, "invalid-date", "2023-01-02")
        
        assert result["success"] is False
        assert result["error"] == "Invalid location parameters"
        assert "message" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_no_data(self):
        """Test error handling when no data is available."""
        # Test with empty repository
        result = await self.controller.get_weather_data(35.7, 139.7, "2023-01-01", "2023-01-02")
        
        # Should succeed but return empty data
        assert result["success"] is True
        assert result["total_count"] == 0
        assert len(result["data"]) == 0
    
    @pytest.mark.asyncio
    async def test_prediction_error_handling_no_historical_data(self):
        """Test prediction error handling when no historical data is available."""
        result = await self.controller.predict_weather(
            35.7, 139.7, "2023-01-01", "2023-01-30", 7
        )
        
        assert result["success"] is False
        assert result["error"] == "Prediction error"
        assert "No historical data available" in result["message"]
    
    @pytest.mark.asyncio
    async def test_prediction_error_handling_invalid_location(self):
        """Test prediction error handling for invalid location."""
        result = await self.controller.predict_weather(
            91.0, 139.7, "2023-01-01", "2023-01-30", 7
        )
        
        assert result["success"] is False
        assert result["error"] == "Invalid location parameters"
        assert "message" in result
    
    def test_controller_initialization(self):
        """Test controller initialization with different interactors."""
        # Test with different interactors
        weather_repo2 = InMemoryWeatherRepository()
        prediction_repo2 = InMemoryPredictionRepository()
        
        fetch_interactor2 = FetchWeatherDataInteractor(weather_repo2)
        predict_interactor2 = PredictWeatherInteractor(weather_repo2, prediction_repo2, self.prediction_service)
        
        weather_service2 = WeatherServiceImpl(fetch_interactor2)
        prediction_service_impl2 = PredictionServiceImpl(predict_interactor2)
        
        controller2 = WeatherController(weather_service2, prediction_service_impl2)
        
        # Should initialize without error
        assert controller2.weather_service == weather_service2
        assert controller2.prediction_service == prediction_service_impl2
