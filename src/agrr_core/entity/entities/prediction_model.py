"""Prediction model entity."""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List


class ModelType(Enum):
    """Supported prediction model types."""
    PROPHET = "prophet"
    LSTM = "lstm"
    ARIMA = "arima"
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"


class MetricType(Enum):
    """Supported weather metrics."""
    TEMPERATURE = "temperature"
    PRECIPITATION = "precipitation"
    SUNSHINE = "sunshine"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    WIND_SPEED = "wind_speed"


@dataclass
class PredictionModel:
    """Prediction model entity."""
    
    model_type: ModelType
    name: str
    description: str
    supported_metrics: List[MetricType]
    default_params: Dict[str, Any]
    min_training_data_points: int
    max_prediction_horizon: int
    supports_confidence_intervals: bool
    supports_seasonality: bool
    supports_trend: bool


@dataclass
class ModelPerformance:
    """Model performance metrics entity."""
    
    model_type: ModelType
    metric: MetricType
    accuracy_metrics: Dict[str, float]
    training_time: float
    prediction_time: float
    model_size: Optional[str] = None
    memory_usage: Optional[str] = None
