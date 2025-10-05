"""Weather service interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.weather_entity import WeatherData


class WeatherService(ABC):
    """Service interface for weather data operations."""
    
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
