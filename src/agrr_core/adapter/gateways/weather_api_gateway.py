"""Weather API gateway implementation for Open-Meteo API.

This gateway directly implements WeatherGateway interface for Open-Meteo API access.
"""

from typing import List
from datetime import datetime

from agrr_core.entity import WeatherData, Location
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.weather_data_not_found_error import WeatherDataNotFoundError
from agrr_core.adapter.interfaces.clients.http_client_interface import HttpClientInterface
from agrr_core.usecase.dto.weather_data_with_location_dto import WeatherDataWithLocationDTO
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway


class WeatherAPIGateway(WeatherGateway):
    """Gateway for fetching weather data from Open-Meteo API.
    
    Directly implements WeatherGateway interface without intermediate layers.
    """
    
    def __init__(self, http_service: HttpClientInterface, forecast_http_service: HttpClientInterface = None):
        """Initialize weather API gateway.
        
        Args:
            http_service: HTTP service for historical weather data
            forecast_http_service: HTTP service for forecast data (optional, defaults to http_service)
        """
        self.http_service = http_service
        self.forecast_http_service = forecast_http_service or http_service
    
    async def get(self) -> List[WeatherData]:
        """Get weather data from configured source.
        
        Note: This method is not used for API-based weather data.
        Use get_by_location_and_date_range() or get_forecast() instead.
        
        Raises:
            NotImplementedError: API requires location and date range parameters
        """
        raise NotImplementedError(
            "API weather source requires location and date range. "
            "Use get_by_location_and_date_range() or get_forecast() instead."
        )
    
    async def create(self, weather_data: List[WeatherData], destination: str) -> None:
        """Create weather data at destination.
        
        Raises:
            NotImplementedError: Weather data creation not supported for API source
        """
        raise NotImplementedError(
            "Weather data creation not supported for API source"
        )
    
    async def get_by_location_and_date_range(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str
    ) -> WeatherDataWithLocationDTO:
        """Get weather data from Open-Meteo API.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            WeatherDataWithLocationDTO containing weather data and location info
            
        Raises:
            WeatherAPIError: If API request fails or response is invalid
            WeatherDataNotFoundError: If no weather data found in response
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
        """Safely get value from list, return None if index is out of bounds or value is None.
        
        Args:
            data_list: List to get value from
            index: Index to access
            
        Returns:
            Value at index or None if not available
        """
        try:
            return data_list[index] if data_list and index < len(data_list) else None
        except (IndexError, TypeError):
            return None
    
    async def get_forecast(
        self,
        latitude: float,
        longitude: float
    ) -> WeatherDataWithLocationDTO:
        """Get 16-day weather forecast starting from tomorrow.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            WeatherDataWithLocationDTO containing forecast data and location info
            
        Raises:
            WeatherAPIError: If API request fails or response is invalid
            WeatherDataNotFoundError: If no weather data found in response
        """
        try:
            from datetime import date, timedelta
            
            # Calculate tomorrow and 16 days ahead
            tomorrow = date.today() + timedelta(days=1)
            end_date = tomorrow + timedelta(days=15)  # 16 days total including tomorrow
            
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "forecast_days": 16,
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
            
            data = await self.forecast_http_service.get("", params)
            
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

