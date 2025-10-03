"""Weather data input port interface."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity import WeatherData


class WeatherDataInputPort(ABC):
    """Interface for weather data input operations."""
    
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
