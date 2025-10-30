"""Prediction request DTO."""

from dataclasses import dataclass

@dataclass
class PredictionRequestDTO:
    """DTO for prediction request."""
    
    latitude: float
    longitude: float
    start_date: str
    end_date: str
    prediction_days: int = 365
