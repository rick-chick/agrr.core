"""Open-Meteo weather service implementation."""

import requests
from datetime import datetime
from typing import List

from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.adapter.services.weather_service import WeatherService


class WeatherOpenMeteoService(WeatherService):
    """Open-Meteo weather service implementation."""
    
    def __init__(self, base_url: str = "https://archive-api.open-meteo.com/v1/archive"):
        """Initialize Open-Meteo service."""
        self.base_url = base_url
    
    async def get_by_location_and_date_range(
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
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "sunshine_duration"
                ]
            }
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Create location object
            location = Location(
                latitude=latitude,
                longitude=longitude,
                elevation=data.get("elevation", 0.0),
                timezone=data.get("timezone", "UTC")
            )
            
            # Parse daily data
            daily_data = data["daily"]
            weather_data_list = []
            
            for i, date_str in enumerate(daily_data["time"]):
                date = datetime.fromisoformat(date_str)
                weather_data = WeatherData(
                    time=date,
                    location=location,
                    temperature_max=self._safe_get(daily_data["temperature_2m_max"], i),
                    temperature_min=self._safe_get(daily_data["temperature_2m_min"], i),
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
