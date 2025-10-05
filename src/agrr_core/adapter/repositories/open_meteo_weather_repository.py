"""Open-Meteo weather repository implementation."""

from typing import List, Tuple
import requests
from datetime import datetime

from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
from agrr_core.usecase.gateways.weather_repository_gateway import WeatherRepositoryGateway


class OpenMeteoWeatherRepository(WeatherRepositoryGateway):
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
    ) -> Tuple[List[WeatherData], Location]:
        """Get weather data from Open-Meteo API.
        
        Returns:
            Tuple of (weather_data_list, location) where location contains
            the actual coordinates and metadata from the API response.
        """
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
            
            # Extract location information from API response
            location = Location(
                latitude=data.get("latitude", latitude),
                longitude=data.get("longitude", longitude),
                elevation=data.get("elevation"),
                timezone=data.get("timezone")
            )
            
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
            
            return weather_data_list, location
            
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
