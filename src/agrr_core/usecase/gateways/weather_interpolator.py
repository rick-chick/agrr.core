"""Weather data interpolation interface (UseCase layer).

This interface defines the contract for interpolating missing weather data.
Concrete implementations are provided in the Adapter layer.
"""

from abc import ABC, abstractmethod
from typing import Dict, List
from datetime import date

from agrr_core.entity.entities.weather_entity import WeatherData


class WeatherInterpolator(ABC):
    """Interface for interpolating missing weather data.
    
    This interface follows the Strategy pattern and allows different
    interpolation strategies to be injected into interactors.
    
    Clean Architecture:
    - Interface defined in UseCase layer (port)
    - Implementation in Adapter layer (adapter)
    """
    
    @abstractmethod
    def interpolate_temperature(
        self,
        weather_by_date: Dict[date, WeatherData],
        sorted_dates: List[date]
    ) -> Dict[date, WeatherData]:
        """Interpolate missing temperature values in weather data.
        
        Args:
            weather_by_date: Dictionary mapping dates to weather data
            sorted_dates: List of dates in chronological order
            
        Returns:
            Dictionary with interpolated weather data
            
        Note:
            This method should handle:
            - Missing dates (gaps in the sequence)
            - None values for temperature_2m_mean
            - Edge cases (beginning/end of sequence)
        """
        pass

