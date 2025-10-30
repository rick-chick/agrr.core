"""Prediction model entity."""

from dataclasses import dataclass
from typing import Dict, Any, List

from .prediction_model_type_entity import ModelType
from .prediction_metric_type_entity import MetricType

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
