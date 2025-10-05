"""Model evaluation request DTO."""

from dataclasses import dataclass
from typing import List

from .prediction_config_dto import PredictionConfigDTO


@dataclass
class ModelEvaluationRequestDTO:
    """DTO for model evaluation request."""
    
    model_type: str
    test_data_start_date: str
    test_data_end_date: str
    validation_split: float
    metrics: List[str]
    config: PredictionConfigDTO
