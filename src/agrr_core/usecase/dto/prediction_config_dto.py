"""Prediction configuration DTO."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


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


@dataclass
class MultiMetricPredictionRequestDTO:
    """DTO for multi-metric prediction request."""
    
    latitude: float
    longitude: float
    start_date: str
    end_date: str
    prediction_days: int
    metrics: List[str]  # ['temperature', 'precipitation', 'sunshine', 'humidity']
    config: PredictionConfigDTO
    location_name: Optional[str] = None
    timezone: Optional[str] = None


@dataclass
class ModelEvaluationRequestDTO:
    """DTO for model evaluation request."""
    
    model_type: str
    test_data_start_date: str
    test_data_end_date: str
    validation_split: float
    metrics: List[str]
    config: PredictionConfigDTO


@dataclass
class BatchPredictionRequestDTO:
    """DTO for batch prediction request."""
    
    locations: List[Dict[str, Any]]  # [{'lat': 35.6762, 'lon': 139.6503, 'name': 'Tokyo'}]
    start_date: str
    end_date: str
    prediction_days: int
    metrics: List[str]
    config: PredictionConfigDTO
