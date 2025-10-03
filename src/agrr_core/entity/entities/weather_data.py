"""Weather data entities."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..exceptions.weather_exceptions import InvalidLocationError, InvalidDateRangeError


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


@dataclass
class Location:
    """Location entity for weather data requests."""
    
    latitude: float
    longitude: float
    
    def __post_init__(self):
        """Validate latitude and longitude values."""
        if not -90 <= self.latitude <= 90:
            raise InvalidLocationError("Latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise InvalidLocationError("Longitude must be between -180 and 180")


@dataclass
class DateRange:
    """Date range entity for weather data requests."""
    
    start_date: str
    end_date: str
    
    def __post_init__(self):
        """Validate date format."""
        try:
            datetime.strptime(self.start_date, "%Y-%m-%d")
            datetime.strptime(self.end_date, "%Y-%m-%d")
        except ValueError as e:
            raise InvalidDateRangeError(f"Invalid date format. Use YYYY-MM-DD format: {e}")


@dataclass
class Forecast:
    """Forecast entity."""
    
    date: datetime
    predicted_value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None
