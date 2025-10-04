"""Location response DTO."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LocationResponseDTO:
    """DTO for location information in weather data response."""
    
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    timezone: Optional[str] = None


