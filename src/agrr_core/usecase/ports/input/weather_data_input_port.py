"""Weather data input port interface."""

from abc import ABC, abstractmethod
from typing import List, Tuple

from agrr_core.entity import WeatherData, Location


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
    ) -> Tuple[List[WeatherData], Location]:
        """Get weather data by location and date range.
        
        Returns:
            Tuple of (weather_data_list, location) where location contains
            the actual coordinates and metadata.
        """
        pass
