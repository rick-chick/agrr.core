"""Weather presenter for formatting weather data responses."""

from typing import Dict, Any, List

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO
from agrr_core.usecase.ports.output.weather_presenter_output_port import WeatherPresenterOutputPort


class WeatherPresenter(WeatherPresenterOutputPort):
    """Presenter for formatting weather data responses."""
    
    def format_weather_data(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Format a single weather data entity to response format."""
        return {
            "location": {
                "latitude": weather_data.location.latitude,
                "longitude": weather_data.location.longitude,
            },
            "date": weather_data.date.isoformat(),
            "temperature": weather_data.temperature,
            "humidity": weather_data.humidity,
            "precipitation": weather_data.precipitation,
            "wind_speed": weather_data.wind_speed,
            "wind_direction": weather_data.wind_direction,
        }
    
    def format_weather_data_list(self, weather_data_list: List[WeatherData]) -> Dict[str, Any]:
        """Format a list of weather data entities to response format."""
        return {
            "weather_data": [self.format_weather_data(data) for data in weather_data_list],
            "count": len(weather_data_list),
        }
    
    def format_weather_data_dto(self, dto: WeatherDataResponseDTO) -> Dict[str, Any]:
        """Format weather data DTO to response format."""
        return {
            "time": dto.time,
            "temperature_2m_max": dto.temperature_2m_max,
            "temperature_2m_min": dto.temperature_2m_min,
            "temperature_2m_mean": dto.temperature_2m_mean,
            "precipitation_sum": dto.precipitation_sum,
            "sunshine_duration": dto.sunshine_duration,
            "sunshine_hours": dto.sunshine_hours,
        }
    
    def format_weather_data_list_dto(self, dto: WeatherDataListResponseDTO) -> Dict[str, Any]:
        """Format weather data list DTO to response format."""
        return {
            "data": [self.format_weather_data_dto(item) for item in dto.data],
            "total_count": dto.total_count,
        }
    
    def format_error(self, error_message: str, error_code: str = "WEATHER_ERROR") -> Dict[str, Any]:
        """Format error response."""
        return {
            "error": {
                "code": error_code,
                "message": error_message,
            },
            "success": False,
        }
    
    def format_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format success response with data."""
        return {
            "success": True,
            "data": data,
        }
