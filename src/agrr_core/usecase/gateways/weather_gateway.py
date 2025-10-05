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