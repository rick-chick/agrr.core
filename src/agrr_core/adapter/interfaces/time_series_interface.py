"""Time series analysis interface for adapter layer."""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import numpy as np


class TimeSeriesInterface(ABC):
    """Interface for time series analysis operations."""
    
    @abstractmethod
    def create_model(self, data: List[float], order: Tuple[int, int, int], 
                    seasonal_order: Optional[Tuple[int, int, int, int]] = None) -> 'TimeSeriesModel':
        """Create time series model with given parameters."""
        pass
    
    @abstractmethod
    def check_stationarity(self, data: List[float]) -> bool:
        """Check if data is stationary using statistical test."""
        pass
    
    @abstractmethod
    def make_stationary(self, data: List[float]) -> List[float]:
        """Make data stationary by differencing."""
        pass


class TimeSeriesModel(ABC):
    """Interface for time series model operations."""
    
    @abstractmethod
    def fit(self) -> 'FittedTimeSeriesModel':
        """Fit the model to data."""
        pass


class FittedTimeSeriesModel(ABC):
    """Interface for fitted time series model operations."""
    
    @abstractmethod
    def forecast(self, steps: int) -> np.ndarray:
        """Generate point forecasts."""
        pass
    
    @abstractmethod
    def get_forecast_with_intervals(self, steps: int) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Generate forecasts with confidence intervals.
        
        Returns:
            Tuple of (predicted_values, confidence_intervals)
            confidence_intervals can be None if not available
        """
        pass
