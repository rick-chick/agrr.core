"""Weather data with location DTO."""

from dataclasses import dataclass
from typing import List, Optional

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.weather_location_entity import Location


@dataclass
class WeatherDataWithLocationDTO:
    """DTO for weather data with location information."""
    
    weather_data_list: List[WeatherData]
    location: Location
