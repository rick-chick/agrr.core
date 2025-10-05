"""Forecast entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Forecast:
    """Forecast entity."""
    
    date: datetime
    predicted_value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
