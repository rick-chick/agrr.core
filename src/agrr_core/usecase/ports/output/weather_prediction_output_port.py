"""Weather prediction output port interface."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity import WeatherData, Forecast


class WeatherPredictionOutputPort(ABC):
    """Interface for weather prediction output operations."""
    
    @abstractmethod
    async def predict_weather(
        self, 
        historical_data: List[WeatherData], 
        prediction_days: int
    ) -> List[Forecast]:
        """Predict weather based on historical data."""
        pass