"""Use case interactor for fetching weather data."""

from agrr_core.entity import Location, DateRange
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
from agrr_core.entity.exceptions.invalid_date_range_error import InvalidDateRangeError
from agrr_core.entity.validators.weather_validator import WeatherValidator
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.ports.output.weather_presenter_output_port import WeatherPresenterOutputPort
from agrr_core.usecase.dto.weather_data_request_dto import WeatherDataRequestDTO
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO


class FetchWeatherDataInteractor:
    """Use case interactor for fetching weather data."""
    
    def __init__(
        self, 
        weather_gateway: WeatherGateway,
        weather_presenter_output_port: WeatherPresenterOutputPort
    ):
        """Initialize weather fetch interactor."""
        self.weather_gateway = weather_gateway
        self.weather_presenter_output_port = weather_presenter_output_port
    
    async def execute(self, request: WeatherDataRequestDTO) -> dict:
        """
        Execute weather data fetching.
        
        Args:
            request: Weather data request containing location and date range
            
        Returns:
            Formatted response via presenter
            
        Raises:
            ValueError: If validation fails
            InvalidLocationError: If location is invalid
            InvalidDateRangeError: If date range is invalid
        """
        # Validate location coordinates using WeatherValidator
        if not WeatherValidator.validate_coordinates(request.latitude, request.longitude):
            error_response = self.weather_presenter_output_port.format_error("Invalid location coordinates")
            return error_response
        
        # Validate date range using WeatherValidator
        if not WeatherValidator.validate_date_range(request.start_date, request.end_date):
            error_response = self.weather_presenter_output_port.format_error("Invalid date range")
            return error_response
        
        try:
            # Create location object (validation happens in __post_init__)
            location = Location(request.latitude, request.longitude)
            
            # Create date range object (validation happens in __post_init__)
            date_range = DateRange(request.start_date, request.end_date)
            
            # Get weather data with location information
            weather_data_with_location = await self.weather_gateway.get_by_location_and_date_range(
                location.latitude,
                location.longitude,
                date_range.start_date,
                date_range.end_date
            )
            
            # Extract weather data and location from API response
            weather_data_list = weather_data_with_location.weather_data_list
            api_location = weather_data_with_location.location
            
            # Convert API location to DTO (preserving elevation and timezone from API)
            location_dto = LocationResponseDTO(
                latitude=api_location.latitude,
                longitude=api_location.longitude,
                elevation=api_location.elevation,
                timezone=api_location.timezone
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
                    wind_speed_10m=weather_data.wind_speed_10m,
                    weather_code=weather_data.weather_code,
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
