"""Invalid location exception."""

from .weather_error import WeatherError


class InvalidLocationError(WeatherError):
    """Raised when location parameters are invalid."""
    pass
