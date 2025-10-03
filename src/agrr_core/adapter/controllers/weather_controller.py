"""Weather controller for handling weather-related requests."""

from typing import Dict, Any

from agrr_core.adapter.interfaces.weather_service_interface import WeatherServiceInterface
from agrr_core.adapter.interfaces.prediction_service_interface import PredictionServiceInterface


class WeatherController:
    """Controller for weather-related operations."""
    
    def __init__(
        self,
        weather_service: WeatherServiceInterface,
        prediction_service: PredictionServiceInterface
    ):
        self.weather_service = weather_service
        self.prediction_service = prediction_service
    
    async def get_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Get weather data for specified location and date range."""
        return await self.weather_service.get_weather_data(latitude, longitude, start_date, end_date)
    
    async def predict_weather(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        prediction_days: int = 365
    ) -> Dict[str, Any]:
        """Predict weather for specified location and date range."""
        return await self.prediction_service.predict_weather(latitude, longitude, start_date, end_date, prediction_days)
    
    def get_weather_data_sync(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Synchronous version of get_weather_data."""
        return self.weather_service.get_weather_data_sync(latitude, longitude, start_date, end_date)
    
    def predict_weather_sync(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        prediction_days: int = 365
    ) -> Dict[str, Any]:
        """Synchronous version of predict_weather."""
        return self.prediction_service.predict_weather_sync(latitude, longitude, start_date, end_date, prediction_days)
