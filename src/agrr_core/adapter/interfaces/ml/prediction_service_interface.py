"""Prediction service interface for weather forecasting (Adapter layer).

This interface defines the contract that Framework layer services must implement.
Framework layer services (ARIMA, LightGBM, Prophet, etc.) implement this interface.
Gateway implementations inject these services.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

from agrr_core.entity import WeatherData, Forecast


class PredictionServiceInterface(ABC):
    """Interface for prediction services (Framework layer implements this, Adapter layer defines)."""
    
    @abstractmethod
    async def predict(
        self,
        historical_data: List[WeatherData],
        metric: str,
        prediction_days: int,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """
        Predict future values for a specific metric.
        
        Args:
            historical_data: Historical weather data for training
            metric: Metric to predict ('temperature', 'precipitation', 'sunshine')
            prediction_days: Number of days to predict
            model_config: Model-specific configuration parameters
            
        Returns:
            List of forecasts with predictions and confidence intervals
            
        Raises:
            PredictionError: If prediction fails
        """
        pass
    
    @abstractmethod
    async def evaluate(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """
        Evaluate prediction accuracy against test data.
        
        Args:
            test_data: Actual weather data for comparison
            predictions: Model predictions
            metric: Metric being evaluated
            
        Returns:
            Dictionary with evaluation metrics (mae, rmse, mape, etc.)
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary with model metadata (type, requirements, capabilities, etc.)
        """
        pass
    
    @abstractmethod
    def get_required_data_days(self) -> int:
        """
        Get minimum number of historical data days required.
        
        Returns:
            Minimum days of historical data needed
        """
        pass

