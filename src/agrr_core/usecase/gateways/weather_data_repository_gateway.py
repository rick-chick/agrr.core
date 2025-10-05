"""Weather data repository gateway interface for usecase layer."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from agrr_core.entity import WeatherData, Location


class WeatherDataRepositoryGateway(ABC):
    """Gateway interface for weather data repository operations."""
    
    @abstractmethod
    async def save_prediction_config(self, config: Dict[str, Any]) -> None:
        """Save prediction configuration."""
        pass
    
    @abstractmethod
    async def get_model_performance(
        self, 
        model_type: str, 
        start_date: str, 
        end_date: str
    ) -> Dict[str, Any]:
        """Get model performance metrics."""
        pass
    
    @abstractmethod
    async def save_model_evaluation(
        self, 
        model_type: str, 
        evaluation_results: Dict[str, Any]
    ) -> None:
        """Save model evaluation results."""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Get list of available prediction models."""
        pass
    
    @abstractmethod
    async def save_forecast_with_metadata(
        self, 
        forecasts: List, 
        metadata: Dict[str, Any]
    ) -> None:
        """Save forecast data with additional metadata."""
        pass
