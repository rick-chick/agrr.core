"""Weather-related exceptions."""


class WeatherError(Exception):
    """Base weather exception."""
    pass


class WeatherDataNotFoundError(WeatherError):
    """Raised when weather data is not found."""
    pass


class InvalidLocationError(WeatherError):
    """Raised when location parameters are invalid."""
    pass


class InvalidDateRangeError(WeatherError):
    """Raised when date range parameters are invalid."""
    pass


class WeatherAPIError(WeatherError):
    """Raised when weather API request fails."""
    pass


class PredictionError(WeatherError):
    """Raised when weather prediction fails."""
    pass
