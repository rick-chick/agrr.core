"""Integration tests for weather controller."""

import pytest
from unittest.mock import Mock, AsyncMock

from agrr_core.adapter.controllers.weather_api_controller import WeatherAPIController
from agrr_core.adapter.repositories.weather_memory_repository import WeatherMemoryRepository
from agrr_core.adapter.services.prediction_integrated_service import PredictionIntegratedService
from agrr_core.entity import WeatherData
from datetime import datetime


class TestWeatherAPIControllerIntegration:
    """Integration tests for WeatherAPIController."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use real repositories for integration testing
        self.weather_repo = WeatherMemoryRepository()
        
        # Create real prediction service
        self.prediction_service = PredictionIntegratedService()
        
        # Create controller with new dependencies
        self.controller = WeatherAPIController(self.weather_repo, self.prediction_service)
    
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
        assert result["data"]["total_count"] == 2
        
        # Check that the response contains the expected structure
        assert "data" in result
    
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
        assert result["data"]["total_count"] == 1
    
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
        assert "data" in result
    
    def test_predict_weather_sync_integration(self):
        """Test synchronous weather prediction integration."""
        # Add historical data for prediction (need at least 30 days for Prophet)
        historical_data = []
        for i in range(30):  # 30 days of data
            historical_data.append(
                WeatherData(
                    time=datetime(2023, 1, i + 1),
                    temperature_2m_mean=20.0 + i * 0.1,
                    temperature_2m_max=25.0 + i * 0.1,
                    temperature_2m_min=15.0 + i * 0.1,
                    precipitation_sum=5.0,
                    sunshine_duration=28800.0,
                )
            )
        
        # Use async save in sync test
        import asyncio
        asyncio.run(self.weather_repo.save_weather_data(historical_data))
        
        # Test prediction
        result = self.controller.predict_weather_sync(
            35.7, 139.7, "2023-01-01", "2023-01-30", 7
        )
        
        # Assertions
        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_location(self):
        """Test error handling for invalid location."""
        result = await self.controller.get_weather_data(91.0, 139.7, "2023-01-01", "2023-01-02")
        
        assert result["success"] is False
        assert "error" in result
        # The error message may vary depending on the actual implementation
        assert "message" in result["error"]
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_date_range(self):
        """Test error handling for invalid date range."""
        result = await self.controller.get_weather_data(35.7, 139.7, "invalid-date", "2023-01-02")
        
        assert result["success"] is False
        assert "error" in result
        # The error message may vary depending on the actual implementation
        assert "message" in result["error"]
    
    @pytest.mark.asyncio
    async def test_error_handling_no_data(self):
        """Test error handling when no data is available."""
        # Test with empty repository
        result = await self.controller.get_weather_data(35.7, 139.7, "2023-01-01", "2023-01-02")
        
        # Should succeed but return empty data
        assert result["success"] is True
        assert result["data"]["total_count"] == 0
    
    @pytest.mark.asyncio
    async def test_prediction_error_handling_no_historical_data(self):
        """Test prediction error handling when no historical data is available."""
        result = await self.controller.predict_weather(
            35.7, 139.7, "2023-01-01", "2023-01-30", 7
        )
        
        assert result["success"] is False
        assert "error" in result
        # The error message may vary depending on the actual implementation
        assert "message" in result["error"]
    
    @pytest.mark.asyncio
    async def test_prediction_error_handling_invalid_location(self):
        """Test prediction error handling for invalid location."""
        result = await self.controller.predict_weather(
            91.0, 139.7, "2023-01-01", "2023-01-30", 7
        )
        
        assert result["success"] is False
        assert "error" in result
        # The error message may vary depending on the actual implementation
        assert "message" in result["error"]
    
    def test_controller_initialization(self):
        """Test controller initialization with different dependencies."""
        # Test with different repository instances
        weather_repo2 = WeatherMemoryRepository()
        prediction_service2 = PredictionIntegratedService()
        
        controller2 = WeatherAPIController(weather_repo2, prediction_service2)
        
        # Should initialize without error
        assert controller2.weather_repository == weather_repo2
        assert controller2.prediction_service == prediction_service2
