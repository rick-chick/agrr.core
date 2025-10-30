"""Weather data gateway interface for usecase layer."""

from abc import ABC, abstractmethod
from typing import List, Tuple

from agrr_core.entity import WeatherData, Location

class WeatherDataGateway(ABC):
    """Gateway interface for weather data operations."""
    
    @abstractmethod
    def get_weather_data_by_location_and_date_range(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Tuple[List[WeatherData], Location]:
        """Get weather data for specified location and date range."""
        pass
