"""Weather repository interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.weather_entity import WeatherData


class WeatherRepositoryInterface(ABC):
    """Abstract interface for weather data repository.
    
    Implementations can be:
    - WeatherFileRepository: Load from JSON/CSV files
    - WeatherSQLRepository: Load from SQL database
    - WeatherMemoryRepository: Load from in-memory storage
    - WeatherAPIRepository: Load from external API
    """
    
    @abstractmethod
    async def get(self) -> List[WeatherData]:
        """Get weather data from configured source.
        
        Returns:
            List of WeatherData entities
            
        Note:
            Source configuration (file path, connection string, etc.)
            is injected at repository initialization, not passed here.
        """
        pass

