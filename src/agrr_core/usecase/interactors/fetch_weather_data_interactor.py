"""Fetch weather data interactor."""

from agrr_core.entity import Location, DateRange
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
from agrr_core.entity.exceptions.invalid_date_range_error import InvalidDateRangeError
from agrr_core.usecase.ports.input.weather_data_input_port import WeatherDataInputPort
from agrr_core.usecase.ports.output.weather_presenter_output_port import WeatherPresenterOutputPort
from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO


class FetchWeatherDataInteractor:
    """Interactor for fetching weather data."""
    
    def __init__(
        self, 
        weather_data_input_port: WeatherDataInputPort,
        weather_presenter_output_port: WeatherPresenterOutputPort
    ):
        self.weather_data_input_port = weather_data_input_port
        self.weather_presenter_output_port = weather_presenter_output_port
    
    async def execute(self, request: WeatherDataRequestDTO) -> None:
        """Execute weather data fetching."""
        try:
            # Validate location
            location = Location(request.latitude, request.longitude)
            
            # Validate date range
            date_range = DateRange(request.start_date, request.end_date)
            
            # Get weather data
            weather_data_list, actual_location = await self.weather_data_input_port.get_weather_data_by_location_and_date_range(
                location.latitude,
                location.longitude,
                date_range.start_date,
                date_range.end_date
            )
            
            # Convert location to DTO
            location_dto = LocationResponseDTO(
                latitude=actual_location.latitude,
                longitude=actual_location.longitude,
                elevation=actual_location.elevation,
                timezone=actual_location.timezone
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
            
            response_dto = WeatherDataListResponseDTO(
                data=response_data,
                total_count=len(response_data),
                location=location_dto
            )
            
            # Use presenter to format response
            formatted_response = self.weather_presenter_output_port.format_weather_data_list_dto(response_dto)
            return self.weather_presenter_output_port.format_success(formatted_response)
            
        except (ValueError, InvalidLocationError, InvalidDateRangeError) as e:
            error_response = self.weather_presenter_output_port.format_error(f"Invalid request parameters: {e}")
            return error_response
        except Exception as e:
            error_response = self.weather_presenter_output_port.format_error(f"Weather data fetch failed: {e}")
            return error_response
