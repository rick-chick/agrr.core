"""Invalid date range exception."""

from .weather_error import WeatherError


class InvalidDateRangeError(WeatherError):
    """Raised when date range parameters are invalid."""
    pass
