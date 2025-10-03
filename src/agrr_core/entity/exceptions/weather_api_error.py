"""Weather API exception."""

from .weather_error import WeatherError


class WeatherAPIError(WeatherError):
    """Raised when weather API request fails."""
    pass
