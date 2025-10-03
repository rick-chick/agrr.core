"""Fetch weather data interactor."""

from agrr_core.entity import Location, DateRange
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
from agrr_core.entity.exceptions.invalid_date_range_error import InvalidDateRangeError
from agrr_core.usecase.ports.input.weather_data_input_port import WeatherDataInputPort
from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO


class FetchWeatherDataInteractor:
    """Interactor for fetching weather data."""
    
    def __init__(self, weather_data_input_port: WeatherDataInputPort):
        self.weather_data_input_port = weather_data_input_port
    
    async def execute(self, request: WeatherDataRequestDTO) -> WeatherDataListResponseDTO:
        """Execute weather data fetching."""
        try:
            # Validate location
            location = Location(request.latitude, request.longitude)
            
            # Validate date range
            date_range = DateRange(request.start_date, request.end_date)
            
            # Get weather data
            weather_data_list = await self.weather_data_input_port.get_weather_data_by_location_and_date_range(
                location.latitude,
                location.longitude,
                date_range.start_date,
                date_range.end_date
            )
            
            # Convert to response DTOs
            response_data = []
            for weather_data in weather_data_list:
                response_dto = WeatherDataResponseDTO(
                    time=weather_data.time.isoformat(),
                    temperature_2m_max=weather_data.temperature_2m_max,
                    temperature_2m_min=weather_data.temperature_2m_min,
                    temperature_2m_mean=weather_data.temperature_2m_mean,
                    precipitation_sum=weather_data.precipitation_sum,
                    sunshine_duration=weather_data.sunshine_duration,
                    sunshine_hours=weather_data.sunshine_hours,
                )
                response_data.append(response_dto)
            
            return WeatherDataListResponseDTO(
                data=response_data,
                total_count=len(response_data)
            )
            
        except (ValueError, InvalidLocationError, InvalidDateRangeError) as e:
            raise InvalidLocationError(f"Invalid request parameters: {e}")
