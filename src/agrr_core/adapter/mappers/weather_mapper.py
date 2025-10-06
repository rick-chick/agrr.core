"""Weather data mappers."""

from typing import List
import pandas as pd

from agrr_core.entity import WeatherData
from agrr_core.usecase.dto.weather_data_response_dto import WeatherDataResponseDTO


class WeatherMapper:
    """Mapper for weather data transformations."""
    
    @staticmethod
    def entity_to_dto(weather_data: WeatherData) -> WeatherDataResponseDTO:
        """Convert WeatherData entity to DTO."""
        return WeatherDataResponseDTO(
            time=weather_data.time.isoformat(),
            temperature_2m_max=weather_data.temperature_2m_max,
            temperature_2m_min=weather_data.temperature_2m_min,
            temperature_2m_mean=weather_data.temperature_2m_mean,
            precipitation_sum=weather_data.precipitation_sum,
            sunshine_duration=weather_data.sunshine_duration,
            sunshine_hours=weather_data.sunshine_hours,
            wind_speed_10m=weather_data.wind_speed_10m,
            weather_code=weather_data.weather_code,
        )
    
