"""Prediction configuration DTO."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PredictionConfigDTO:
    """DTO for prediction configuration."""
    
    model_type: str  # 'prophet', 'lstm', 'arima', 'linear_regression'
    seasonality: Dict[str, bool]  # {'yearly': True, 'weekly': False, 'daily': False}
    trend: str  # 'linear', 'logistic', 'flat'
    custom_params: Dict[str, Any]  # Model-specific parameters
    confidence_level: float = 0.95  # Confidence interval level
    prediction_horizon: int = 365  # Number of days to predict
    validation_split: float = 0.2  # Fraction of data for validation