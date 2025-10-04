"""In-memory weather repository implementation."""

from typing import List, Tuple
from datetime import datetime

from agrr_core.entity import WeatherData, Location
from agrr_core.usecase.ports.input.weather_data_input_port import WeatherDataInputPort


class InMemoryWeatherRepository(WeatherDataInputPort):
    """In-memory repository for weather data (useful for testing)."""
    
    def __init__(self):
        self._weather_data: List[WeatherData] = []
    
    async def save_weather_data(self, weather_data: List[WeatherData]) -> None:
        """Save weather data to memory."""
        self._weather_data.extend(weather_data)
    
    async def get_weather_data_by_location_and_date_range(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Tuple[List[WeatherData], Location]:
        """Get weather data from memory (filtered by date range).
        
        Returns:
            Tuple of (weather_data_list, location) where location contains
            the requested coordinates.
        """
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)
        
        filtered_data = [
            data for data in self._weather_data
            if start_datetime <= data.time <= end_datetime
        ]
        
        # Return the requested location (no elevation/timezone for in-memory)
        location = Location(latitude=latitude, longitude=longitude)
        
        return filtered_data, location
    
    def clear(self) -> None:
        """Clear all stored weather data."""
        self._weather_data.clear()
