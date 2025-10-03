"""In-memory weather repository implementation."""

from typing import List
from datetime import datetime

from agrr_core.entity import WeatherData
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
    ) -> List[WeatherData]:
        """Get weather data from memory (filtered by date range)."""
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)
        
        filtered_data = [
            data for data in self._weather_data
            if start_datetime <= data.time <= end_datetime
        ]
        
        return filtered_data
    
    def clear(self) -> None:
        """Clear all stored weather data."""
        self._weather_data.clear()
