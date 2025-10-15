"""In-memory forecast gateway implementation."""

from typing import List
from datetime import datetime

from agrr_core.entity import Forecast
from agrr_core.usecase.gateways.forecast_gateway import ForecastGateway


class ForecastInMemoryGateway(ForecastGateway):
    """In-memory forecast gateway for testing and caching.
    
    This gateway stores forecasts in memory and provides basic
    CRUD operations for forecast data. Useful for:
    - Unit testing
    - In-memory caching
    - Temporary forecast storage
    
    Example:
        gateway = ForecastInMemoryGateway()
        await gateway.save_forecast(forecasts)
        results = await gateway.get_forecast_by_date_range('2024-01-01', '2024-01-31')
    """
    
    def __init__(self):
        """Initialize in-memory forecast storage."""
        self._forecasts: List[Forecast] = []
    
    async def save_forecast(self, forecasts: List[Forecast]) -> None:
        """Save forecast data to memory.
        
        Args:
            forecasts: List of forecast entities to save
        """
        self._forecasts.extend(forecasts)
    
    async def get_forecast_by_date_range(
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
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)
        
        return [
            forecast for forecast in self._forecasts
            if start_datetime <= forecast.date <= end_datetime
        ]
    
    def clear(self) -> None:
        """Clear all stored forecast data.
        
        Useful for:
        - Resetting test state
        - Clearing cache
        """
        self._forecasts.clear()

