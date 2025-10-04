"""Forecast response DTO."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ForecastResponseDTO:
    """DTO for forecast response."""
    
    date: str
    predicted_value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
