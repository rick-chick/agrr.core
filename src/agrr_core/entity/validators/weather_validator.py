"""Weather data validation utilities."""

import re
from datetime import datetime
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
    
    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        """Validate location coordinates."""
        # Check latitude range (-90 to 90)
        if not (-90 <= latitude <= 90):
            return False
        
        # Check longitude range (-180 to 180)
        if not (-180 <= longitude <= 180):
            return False
        
        return True
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> bool:
        """Validate date range format and logic."""
        if not start_date or not end_date:
            return False
        
        # Check ISO date format (YYYY-MM-DD)
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not (re.match(date_pattern, start_date) and re.match(date_pattern, end_date)):
            return False
        
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            # Check if start date is before end date
            if start_dt >= end_dt:
                return False
            
            return True
        except ValueError:
            return False
