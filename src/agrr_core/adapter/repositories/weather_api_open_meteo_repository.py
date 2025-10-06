"""Open-Meteo weather repository implementation."""

from typing import List
from datetime import datetime

from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
from agrr_core.adapter.interfaces.http_service_interface import HttpServiceInterface
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO


class WeatherAPIOpenMeteoRepository:
    """Repository for fetching weather data from Open-Meteo API."""
    
    def __init__(self, http_service: HttpServiceInterface):
        self.http_service = http_service
    
    
    async def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> WeatherDataWithLocationDTO:
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
                    "sunshine_duration",
                    "wind_speed_10m_max",
                    "weather_code"
                ]),
                "timezone": "Asia/Tokyo"
            }
            
            data = await self.http_service.get("", params)
            
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
                    wind_speed_10m=self._safe_get(daily_data["wind_speed_10m_max"], i),
                    weather_code=self._safe_get(daily_data["weather_code"], i),
                )
                weather_data_list.append(weather_data)
            
            return WeatherDataWithLocationDTO(
                weather_data_list=weather_data_list,
                location=location
            )
            
        except WeatherAPIError:
            raise
        except (KeyError, ValueError) as e:
            raise WeatherAPIError(f"Invalid API response format: {e}")
    
    
    def _safe_get(self, data_list: List, index: int):
        """Safely get value from list, return None if index is out of bounds or value is None."""
        try:
            return data_list[index] if data_list and index < len(data_list) else None
        except (IndexError, TypeError):
            return None
