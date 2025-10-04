"""Weather service implementation for adapter layer."""

from typing import Dict, Any

from agrr_core.adapter.interfaces.weather_service_interface import WeatherServiceInterface
from agrr_core.usecase.interactors.fetch_weather_data_interactor import FetchWeatherDataInteractor
from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO
from agrr_core.entity.exceptions.weather_error import WeatherError
from agrr_core.entity.exceptions.weather_api_error import WeatherAPIError
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
from agrr_core.entity.exceptions.invalid_date_range_error import InvalidDateRangeError


class WeatherServiceImpl(WeatherServiceInterface):
    """Implementation of weather service for adapter layer."""
    
    def __init__(self, fetch_weather_interactor: FetchWeatherDataInteractor):
        self.fetch_weather_interactor = fetch_weather_interactor
    
    async def get_weather_data(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Get weather data for specified location and date range."""
        try:
            request = WeatherDataRequestDTO(
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date
            )
            
            result = await self.fetch_weather_interactor.execute(request)
            
            return {
                "success": True,
                "data": [
                    {
                        "time": item.time,
                        "temperature_2m_max": item.temperature_2m_max,
                        "temperature_2m_min": item.temperature_2m_min,
                        "temperature_2m_mean": item.temperature_2m_mean,
                        "precipitation_sum": item.precipitation_sum,
                        "sunshine_duration": item.sunshine_duration,
                        "sunshine_hours": item.sunshine_hours,
                    }
                    for item in result.data
                ],
                "total_count": result.total_count
            }
            
        except InvalidLocationError as e:
            return {
                "success": False,
                "error": "Invalid location parameters",
                "message": str(e)
            }
        except InvalidDateRangeError as e:
            return {
                "success": False,
                "error": "Invalid date range parameters", 
                "message": str(e)
            }
        except WeatherAPIError as e:
            return {
                "success": False,
                "error": "Weather API error",
                "message": str(e)
            }
        except WeatherError as e:
            return {
                "success": False,
                "error": "Weather service error",
                "message": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "Internal server error",
                "message": str(e)
            }
    
    def get_weather_data_sync(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Synchronous version of get_weather_data."""
        import asyncio
        return asyncio.run(self.get_weather_data(latitude, longitude, start_date, end_date))
