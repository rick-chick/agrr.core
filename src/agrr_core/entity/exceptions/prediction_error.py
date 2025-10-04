"""Weather prediction exception."""

from .weather_error import WeatherError


class PredictionError(WeatherError):
    """Raised when weather prediction fails."""
    pass
