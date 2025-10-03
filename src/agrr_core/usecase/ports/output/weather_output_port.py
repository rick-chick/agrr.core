"""Weather output port interfaces."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity import WeatherData, Forecast


class WeatherDataOutputPort(ABC):
    """Interface for weather data output operations."""
    
    @abstractmethod
    async def save_weather_data(self, weather_data: List[WeatherData]) -> None:
        """Save weather data."""
        pass
    
    @abstractmethod
    async def get_weather_data_by_location_and_date_range(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> List[WeatherData]:
        """Get weather data by location and date range."""
        pass


class WeatherPredictionOutputPort(ABC):
    """Interface for weather prediction output operations."""
    
    @abstractmethod
    async def save_forecast(self, forecasts: List[Forecast]) -> None:
        """Save forecast data."""
        pass
    
    @abstractmethod
    async def get_forecast_by_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[Forecast]:
        """Get forecast data by date range."""
        pass
