"""Weather gateway interface for usecase layer."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO


class WeatherGateway(ABC):
    """Gateway interface for weather domain operations.
    
    Note: Data source (file path, URL, etc.) is injected at initialization via Repository,
    not passed as method arguments.
    """
    
    @abstractmethod
    async def get(self) -> List[WeatherData]:
        """Get weather data from configured source.
        
        Returns:
            List of WeatherData entities
        """
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
    ) -> WeatherDataWithLocationDTO:
        """Get weather data by location and date range."""
        pass
    
    @abstractmethod
    async def get_forecast(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherDataWithLocationDTO:
        """Get 16-day weather forecast starting from tomorrow."""
        pass