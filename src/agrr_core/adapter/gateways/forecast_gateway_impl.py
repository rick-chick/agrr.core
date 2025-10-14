"""Forecast gateway implementation (Adapter layer).

This gateway provides forecast storage and retrieval operations
to the UseCase layer.

NOTE: This gateway is currently not used in the application.
      It was created as part of architecture refactoring to properly separate
      concerns between Repository (data storage) and Gateway (business interface).
      
      Use case: Future forecast storage/retrieval features
      - Save prediction results to persistent storage
      - Query historical predictions by date range
      
      When implementing these features, inject this gateway into relevant Interactors.
"""

from typing import List

from agrr_core.entity import Forecast
from agrr_core.usecase.gateways.forecast_gateway import ForecastGateway
from agrr_core.adapter.interfaces.forecast_repository_interface import ForecastRepositoryInterface


class ForecastGatewayImpl(ForecastGateway):
    """
    Gateway implementation for forecast operations (Adapter layer).
    
    Receives Adapter layer repository via dependency injection
    and provides forecast interface to UseCase layer.
    """
    
    def __init__(self, forecast_repository: ForecastRepositoryInterface):
        """
        Initialize forecast gateway.
        
        Args:
            forecast_repository: Forecast repository implementation (injected)
        """
        self.forecast_repository = forecast_repository
    
    async def save_forecast(self, forecasts: List[Forecast]) -> None:
        """Save forecast data.
        
        Args:
            forecasts: List of forecast entities to save
        """
        await self.forecast_repository.save(forecasts)
    
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
        return await self.forecast_repository.get_by_date_range(start_date, end_date)

