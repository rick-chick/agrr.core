"""Use case interactor for getting weather forecast."""

from agrr_core.entity import Location
from agrr_core.entity.exceptions.invalid_location_error import InvalidLocationError
from agrr_core.entity.validators.weather_validator import WeatherValidator
from agrr_core.usecase.gateways.weather_gateway import WeatherGateway
from agrr_core.usecase.ports.output.weather_presenter_output_port import WeatherPresenterOutputPort
from agrr_core.usecase.dto.weather_forecast_request_dto import WeatherForecastRequestDTO
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
from agrr_core.usecase.dto.location_response_dto import LocationResponseDTO


class WeatherGetForecastInteractor:
    """Use case interactor for getting weather forecast."""
    
    def __init__(
        self, 
        weather_gateway: WeatherGateway,
        weather_presenter_output_port: WeatherPresenterOutputPort
    ):
        """Initialize weather get forecast interactor."""
        self.weather_gateway = weather_gateway
        self.weather_presenter_output_port = weather_presenter_output_port
    
    def execute(self, request: WeatherForecastRequestDTO) -> dict:
        """
        Execute weather forecast retrieval.
        
        Args:
            request: Weather forecast request containing location
            
        Returns:
            Formatted response via presenter containing 16-day forecast
            
        Raises:
            ValueError: If validation fails
            InvalidLocationError: If location is invalid
        """
        # Validate location coordinates using WeatherValidator
        if not WeatherValidator.validate_coordinates(request.latitude, request.longitude):
            error_response = self.weather_presenter_output_port.format_error("Invalid location coordinates")
            return error_response
        
        try:
            # Create location object (validation happens in __post_init__)
            location = Location(request.latitude, request.longitude)
            
            # Get 16-day forecast starting from tomorrow
            weather_data_with_location = self.weather_gateway.get_forecast(
                location.latitude,
                location.longitude
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
            
        except (ValueError, InvalidLocationError) as e:
            error_response = self.weather_presenter_output_port.format_error(f"Invalid request parameters: {e}")
            return error_response
        except Exception as e:
            error_response = self.weather_presenter_output_port.format_error(f"Weather forecast fetch failed: {e}")
            return error_response

