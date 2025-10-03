"""Entity layer package."""

from .entities.weather_data import WeatherData, Location, DateRange, Forecast
from .exceptions.weather_exceptions import (
    WeatherError,
    WeatherDataNotFoundError,
    InvalidLocationError,
    InvalidDateRangeError,
    WeatherAPIError,
    PredictionError,
)

__all__ = [
    "WeatherData",
    "Location", 
    "DateRange",
    "Forecast",
    "WeatherError",
    "WeatherDataNotFoundError",
    "InvalidLocationError",
    "InvalidDateRangeError",
    "WeatherAPIError",
    "PredictionError",
]
