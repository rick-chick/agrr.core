"""Weather data list response DTO."""

from dataclasses import dataclass
from typing import List, Optional

from .weather_data_response_dto import WeatherDataResponseDTO
from .location_response_dto import LocationResponseDTO


@dataclass
class WeatherDataListResponseDTO:
    """DTO for weather data list response."""
    
    data: List[WeatherDataResponseDTO]
    total_count: int
    location: Optional[LocationResponseDTO] = None
