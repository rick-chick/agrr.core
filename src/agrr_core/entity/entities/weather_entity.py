"""Weather data entity."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class WeatherData:
    """Weather data entity."""
    
    time: datetime
    temperature_2m_max: Optional[float] = None
    temperature_2m_min: Optional[float] = None
    temperature_2m_mean: Optional[float] = None
    precipitation_sum: Optional[float] = None
    sunshine_duration: Optional[float] = None
    
    @property
    def sunshine_hours(self) -> Optional[float]:
        """Convert sunshine duration from seconds to hours."""
        if self.sunshine_duration is None:
            return None
        return self.sunshine_duration / 3600.0