"""Weather presenter output port interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO
from agrr_core.usecase.dto.weather_data_list_response_dto import WeatherDataListResponseDTO

class WeatherPresenterOutputPort(ABC):
    """Interface for weather data presentation output operations."""
    
    @abstractmethod
    def format_weather_data(self, weather_data: WeatherData) -> Dict[str, Any]:
        """Format a single weather data entity to response format."""
        pass
    
    @abstractmethod
    def format_weather_data_dto(self, dto: WeatherDataResponseDTO) -> Dict[str, Any]:
        """Format weather data DTO to response format."""
        pass
    
    @abstractmethod
    def format_weather_data_list_dto(self, dto: WeatherDataListResponseDTO) -> Dict[str, Any]:
        """Format weather data list DTO to response format."""
        pass
    
    @abstractmethod
    def format_error(self, error_message: str, error_code: str = "WEATHER_ERROR") -> Dict[str, Any]:
        """Format error response."""
        pass
    
    @abstractmethod
    def format_success(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format success response with data."""
        pass
