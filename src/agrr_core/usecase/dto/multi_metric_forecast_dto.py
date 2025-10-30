"""Multi-metric forecast DTO."""

from dataclasses import dataclass
from typing import Dict

@dataclass
class MultiMetricForecastDTO:
    """DTO for multi-metric forecast results."""
    
    date: str
    metrics: Dict[str, Dict[str, float]]  # {'temperature': {'predicted': 20.5, 'lower': 18.0, 'upper': 23.0}}
