"""Date range entity for weather data requests."""

from dataclasses import dataclass
from datetime import datetime

from ..exceptions.invalid_date_range_error import InvalidDateRangeError


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
