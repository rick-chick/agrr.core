"""Weather prediction repository implementations.

NOTE: This repository is currently not used in the application.
      It was refactored to implement ForecastRepositoryInterface instead of ForecastGateway.
      Designed for future forecast storage features (in-memory caching, testing, etc.).
"""

from typing import List
from datetime import datetime

from agrr_core.entity import Forecast
from agrr_core.adapter.interfaces.forecast_repository_interface import ForecastRepositoryInterface


class PredictionStorageRepository(ForecastRepositoryInterface):
    """In-memory repository for weather predictions (useful for testing)."""
    
    def __init__(self):
        self._forecasts: List[Forecast] = []
    
    async def save(self, forecasts: List[Forecast]) -> None:
        """Save forecast data to memory.
        
        Args:
            forecasts: List of forecast entities to save
        """
        self._forecasts.extend(forecasts)
    
    async def get_by_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[Forecast]:
        """Get forecast data from memory (filtered by date range).
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            
        Returns:
            List of forecast entities within the date range
        """
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)
        
        filtered_forecasts = [
            forecast for forecast in self._forecasts
            if start_datetime <= forecast.date <= end_datetime
        ]
        
        return filtered_forecasts
    
    # Legacy methods (for backward compatibility)
    
    async def save_forecast(self, forecasts: List[Forecast]) -> None:
        """Save forecast data to memory.
        
        DEPRECATED: Use save() method instead.
        """
        await self.save(forecasts)
    
    async def get_forecast_by_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[Forecast]:
        """Get forecast data from memory (filtered by date range).
        
        DEPRECATED: Use get_by_date_range() method instead.
        """
        return await self.get_by_date_range(start_date, end_date)
    
    def clear(self) -> None:
        """Clear all stored forecast data."""
        self._forecasts.clear()
