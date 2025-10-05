"""Location entity for weather data requests."""

from dataclasses import dataclass
from typing import Optional

from ..exceptions.invalid_location_error import InvalidLocationError


@dataclass
class Location:
    """Location entity for weather data requests."""
    
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    timezone: Optional[str] = None
    
    def __post_init__(self):
        """Validate latitude and longitude values."""
        if not -90 <= self.latitude <= 90:
            raise InvalidLocationError("Latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise InvalidLocationError("Longitude must be between -180 and 180")
