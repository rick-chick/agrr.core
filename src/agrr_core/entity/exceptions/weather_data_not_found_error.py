"""Weather data not found exception."""

from .weather_error import WeatherError

class WeatherDataNotFoundError(WeatherError):
    """Raised when weather data is not found."""
    pass
