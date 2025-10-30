"""Prediction gateway interface for usecase layer."""

from abc import ABC, abstractmethod
from typing import List, Dict

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.prediction_forecast_entity import Forecast


class PredictionGateway(ABC):
    """Gateway interface for prediction domain operations."""
    
    @abstractmethod
    def read_historical_data(self, source: str) -> List[WeatherData]:
        """Read historical weather data from source.
        
        Args:
            source: Path to historical weather data file
            
        Returns:
            List of WeatherData entities
        """
        pass
    
    @abstractmethod
    def create(self, predictions: List[Forecast], destination: str) -> None:
        """Create predictions at destination."""
        pass
    
    @abstractmethod
    def predict(
        self,
        historical_data: List[WeatherData],
        metric: str,
        config: dict
    ) -> List[Forecast]:
        """Predict weather metrics using historical data."""
        pass
    
    @abstractmethod
    def predict_multiple_metrics(
        self,
        historical_data: List[WeatherData],
        metrics: List[str],
        config: dict
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using historical data.
        
        Args:
            historical_data: Historical weather data
            metrics: List of metrics to predict
            config: Prediction configuration
            
        Returns:
            Dictionary mapping metric names to forecast lists
        """
        pass
