"""Weather data repository implementations."""

from typing import List
import requests
from datetime import datetime

from agrr_core.entity import WeatherData
from agrr_core.entity.exceptions.weather_exceptions import WeatherAPIError, WeatherDataNotFoundError
from agrr_core.usecase.ports.output.weather_output_port import WeatherDataOutputPort


class OpenMeteoWeatherRepository(WeatherDataOutputPort):
    """Repository for fetching weather data from Open-Meteo API."""
    
    def __init__(self, base_url: str = "https://archive-api.open-meteo.com/v1/archive"):
        self.base_url = base_url
    
    async def save_weather_data(self, weather_data: List[WeatherData]) -> None:
        """Save weather data (not implemented for API-based repository)."""
        # This repository fetches data from API, so save operation is not applicable
        pass
    
    async def get_weather_data_by_location_and_date_range(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> List[WeatherData]:
        """Get weather data from Open-Meteo API."""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "daily": ",".join([
                    "temperature_2m_max",
                    "temperature_2m_min", 
                    "temperature_2m_mean",
                    "precipitation_sum",
                    "sunshine_duration"
                ]),
                "timezone": "Asia/Tokyo"
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if "daily" not in data:
                raise WeatherDataNotFoundError("No daily weather data found in API response")
            
            # Convert API response to WeatherData entities
            weather_data_list = []
            daily_data = data["daily"]
            
            for i, time_str in enumerate(daily_data["time"]):
                weather_data = WeatherData(
                    time=datetime.fromisoformat(time_str),
                    temperature_2m_max=self._safe_get(daily_data["temperature_2m_max"], i),
                    temperature_2m_min=self._safe_get(daily_data["temperature_2m_min"], i),
                    temperature_2m_mean=self._safe_get(daily_data["temperature_2m_mean"], i),
                    precipitation_sum=self._safe_get(daily_data["precipitation_sum"], i),
                    sunshine_duration=self._safe_get(daily_data["sunshine_duration"], i),
                )
                weather_data_list.append(weather_data)
            
            return weather_data_list
            
        except requests.RequestException as e:
            raise WeatherAPIError(f"Failed to fetch weather data from API: {e}")
        except (KeyError, ValueError) as e:
            raise WeatherAPIError(f"Invalid API response format: {e}")
    
    def _safe_get(self, data_list: List, index: int):
        """Safely get value from list, return None if index is out of bounds or value is None."""
        try:
            return data_list[index] if data_list and index < len(data_list) else None
        except (IndexError, TypeError):
            return None


class InMemoryWeatherRepository(WeatherDataOutputPort):
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
