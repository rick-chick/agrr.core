"""Weather data response DTO."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class WeatherDataResponseDTO:
    """DTO for weather data response."""
    
    time: str
    temperature_2m_max: Optional[float] = None
    temperature_2m_min: Optional[float] = None
    temperature_2m_mean: Optional[float] = None
    precipitation_sum: Optional[float] = None
    sunshine_duration: Optional[float] = None
    sunshine_hours: Optional[float] = None
    wind_speed_10m: Optional[float] = None
    weather_code: Optional[int] = None
