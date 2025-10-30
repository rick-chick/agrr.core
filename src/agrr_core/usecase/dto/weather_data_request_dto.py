"""Weather data request DTO."""

from dataclasses import dataclass

@dataclass
class WeatherDataRequestDTO:
    """DTO for weather data request."""
    
    latitude: float
    longitude: float
    start_date: str
    end_date: str
