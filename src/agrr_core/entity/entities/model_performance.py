"""Model performance metrics entity."""

from dataclasses import dataclass
from typing import Dict, Optional

from .model_type import ModelType
from .metric_type import MetricType


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
