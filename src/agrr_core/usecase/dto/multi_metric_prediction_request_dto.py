"""Multi-metric prediction request DTO."""

from dataclasses import dataclass
from typing import List, Optional

from .prediction_config_dto import PredictionConfigDTO


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
