"""Forecast gateway interface for usecase layer."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity import Forecast

class ForecastGateway(ABC):
    """Gateway interface for forecast storage and retrieval operations."""
    
    @abstractmethod
    def save_forecast(self, forecasts: List[Forecast]) -> None:
        """Save forecast data."""
        pass
    
    @abstractmethod
    def get_forecast_by_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> List[Forecast]:
        """Get forecast data by date range."""
        pass
