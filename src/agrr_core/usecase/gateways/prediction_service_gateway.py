"""Prediction service gateway interface for usecase layer."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from agrr_core.entity import WeatherData, Forecast


class PredictionServiceGateway(ABC):
    """Gateway interface for prediction service operations."""
    
    @abstractmethod
    async def predict_multiple_metrics(
        self, 
        historical_data: List[WeatherData], 
        metrics: List[str],
        model_config: Dict[str, Any]
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using specified model."""
        pass
    
    @abstractmethod
    async def evaluate_model_accuracy(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """Evaluate model accuracy using test data."""
        pass
    
    @abstractmethod
    async def train_model(
        self,
        training_data: List[WeatherData],
        model_config: Dict[str, Any],
        metric: str
    ) -> Dict[str, Any]:
        """Train prediction model with given configuration."""
        pass
    
    @abstractmethod
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get information about specific model."""
        pass
    
    @abstractmethod
    async def predict_with_confidence_intervals(
        self,
        historical_data: List[WeatherData],
        prediction_days: int,
        confidence_level: float,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict with custom confidence intervals."""
        pass
    
    @abstractmethod
    async def batch_predict(
        self,
        historical_data_list: List[List[WeatherData]],
        model_config: Dict[str, Any],
        metrics: List[str]
    ) -> List[Dict[str, List[Forecast]]]:
        """Perform batch prediction for multiple datasets."""
        pass
