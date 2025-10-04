"""Weather service interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import Dict, Any


class WeatherServiceInterface(ABC):
    """Interface for weather service in adapter layer."""
    
    @abstractmethod
    async def get_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Get weather data for specified location and date range."""
        pass
    
    @abstractmethod
    def get_weather_data_sync(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Synchronous version of get_weather_data."""
        pass
