"""Model performance DTO."""

from dataclasses import dataclass
from typing import Dict, Optional

from .model_accuracy_dto import ModelAccuracyDTO


@dataclass
class ModelPerformanceDTO:
    """DTO for model performance comparison."""
    
    model_type: str
    metrics: Dict[str, ModelAccuracyDTO]  # Key: metric name, Value: accuracy
    training_time: float
    prediction_time: float
    model_size: Optional[str] = None
    memory_usage: Optional[str] = None
