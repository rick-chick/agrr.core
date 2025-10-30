"""Weather forecast request DTO."""

from dataclasses import dataclass

@dataclass
class WeatherForecastRequestDTO:
    """DTO for weather forecast request."""
    
    latitude: float
    longitude: float

