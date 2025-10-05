"""Weather gateway interface for usecase layer."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.weather_entity import WeatherData


class WeatherGateway(ABC):
    """Gateway interface for weather domain operations."""
    
    @abstractmethod
    async def get(self, source: str) -> List[WeatherData]:
        """Get weather data from source."""
        pass
    
    @abstractmethod
    async def create(self, weather_data: List[WeatherData], destination: str) -> None:
        """Create weather data at destination."""
        pass
    
    @abstractmethod
    async def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> List[WeatherData]:
        """Get weather data by location and date range."""
        pass