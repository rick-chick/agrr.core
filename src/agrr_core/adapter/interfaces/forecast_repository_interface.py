"""Forecast repository interface for adapter layer.

NOTE: This interface is part of the architecture refactoring but not yet used in production.
      Created to properly separate Repository (storage) from Gateway (business interface).
      Implementation: PredictionStorageRepository
"""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity import Forecast


class ForecastRepositoryInterface(ABC):
    """Abstract interface for forecast data repository.
    
    Implementations can be:
    - PredictionStorageRepository: In-memory storage
    - PredictionFileRepository: File-based storage
    - PredictionSQLRepository: Database storage
    """
    
    @abstractmethod
    async def save(self, forecasts: List[Forecast]) -> None:
        """Save forecast data to storage.
        
        Args:
            forecasts: List of forecast entities to save
        """
        pass
    
    @abstractmethod
    async def get_by_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[Forecast]:
        """Get forecast data by date range.
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            List of forecast entities within the date range
        """
        pass

