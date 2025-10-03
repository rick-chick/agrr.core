"""Weather data list response DTO."""

from dataclasses import dataclass
from typing import List

from .weather_data_response_dto import WeatherDataResponseDTO


@dataclass
class WeatherDataListResponseDTO:
    """DTO for weather data list response."""
    
    data: List[WeatherDataResponseDTO]
    total_count: int
