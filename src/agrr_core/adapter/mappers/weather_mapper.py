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
        )
    
    @staticmethod
    def entities_to_dtos(weather_data_list: List[WeatherData]) -> List[WeatherDataResponseDTO]:
        """Convert list of WeatherData entities to DTOs."""
        return [WeatherMapper.entity_to_dto(data) for data in weather_data_list]
    
    @staticmethod
    def entities_to_dataframe(weather_data_list: List[WeatherData]) -> pd.DataFrame:
        """Convert list of WeatherData entities to pandas DataFrame."""
        if not weather_data_list:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'time', 'temperature_2m_max', 'temperature_2m_min', 
                'temperature_2m_mean', 'precipitation_sum', 'sunshine_duration', 'sunshine_hours'
            ])
        
        data = []
        for weather_data in weather_data_list:
            data.append({
                'time': weather_data.time,
                'temperature_2m_max': weather_data.temperature_2m_max,
                'temperature_2m_min': weather_data.temperature_2m_min,
                'temperature_2m_mean': weather_data.temperature_2m_mean,
                'precipitation_sum': weather_data.precipitation_sum,
                'sunshine_duration': weather_data.sunshine_duration,
                'sunshine_hours': weather_data.sunshine_hours,
            })
        
        return pd.DataFrame(data)
    
    @staticmethod
    def dataframe_to_entities(df: pd.DataFrame) -> List[WeatherData]:
        """Convert pandas DataFrame to list of WeatherData entities."""
        weather_data_list = []
        for _, row in df.iterrows():
            weather_data = WeatherData(
                time=row['time'],
                temperature_2m_max=row.get('temperature_2m_max'),
                temperature_2m_min=row.get('temperature_2m_min'),
                temperature_2m_mean=row.get('temperature_2m_mean'),
                precipitation_sum=row.get('precipitation_sum'),
                sunshine_duration=row.get('sunshine_duration'),
            )
            weather_data_list.append(weather_data)
        
        return weather_data_list
