"""Prediction gateway interface for usecase layer."""

from abc import ABC, abstractmethod
from typing import List

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.prediction_forecast_entity import Forecast


class PredictionGateway(ABC):
    """Gateway interface for prediction domain operations."""
    
    @abstractmethod
    async def create(self, predictions: List[Forecast], destination: str) -> None:
        """Create predictions at destination."""
        pass
    
    @abstractmethod
    async def predict(
        self,
        historical_data: List[WeatherData],
        metric: str,
        config: dict
    ) -> List[Forecast]:
        """Predict weather metrics using historical data."""
        pass
