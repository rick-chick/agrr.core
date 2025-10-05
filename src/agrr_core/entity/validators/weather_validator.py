"""Weather data validation utilities."""

from typing import List
from agrr_core.entity.entities.weather_entity import WeatherData


class WeatherValidator:
    """Validator for weather data operations."""
    
    @staticmethod
    def validate_source_format(source: str) -> bool:
        """Validate input data source format."""
        if not source:
            return False
        
        # Check if it's a valid file path with supported extensions
        supported_extensions = ['.json', '.csv']
        return any(source.lower().endswith(ext) for ext in supported_extensions)
    
    @staticmethod
    def validate_destination_format(destination: str) -> bool:
        """Validate output destination format."""
        if not destination:
            return False
        
        # Check if it's a valid file path with supported extensions
        supported_extensions = ['.json', '.csv']
        return any(destination.lower().endswith(ext) for ext in supported_extensions)
    
    @staticmethod
    def validate_weather_data(weather_data: List[WeatherData]) -> bool:
        """Validate weather data quality."""
        if not weather_data:
            return False
        
        # Check if we have sufficient data for prediction
        if len(weather_data) < 30:
            return False
        
        # Check if all data points have valid temperature values
        for data in weather_data:
            if data.temperature_2m_mean is None:
                return False
        
        return True
