"""Batch prediction request DTO."""

from dataclasses import dataclass
from typing import List, Dict, Any

from .prediction_config_dto import PredictionConfigDTO


@dataclass
class BatchPredictionRequestDTO:
    """DTO for batch prediction request."""
    
    locations: List[Dict[str, Any]]  # [{'lat': 35.6762, 'lon': 139.6503, 'name': 'Tokyo'}]
    start_date: str
    end_date: str
    prediction_days: int
    metrics: List[str]
    config: PredictionConfigDTO
