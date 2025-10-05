"""Weather exceptions package."""

from .weather_error import WeatherError
from .weather_data_not_found_error import WeatherDataNotFoundError
from .invalid_location_error import InvalidLocationError
from .invalid_date_range_error import InvalidDateRangeError
from .weather_api_error import WeatherAPIError
from .prediction_error import PredictionError
from .file_error import FileError

__all__ = [
    "WeatherError",
    "WeatherDataNotFoundError",
    "InvalidLocationError",
    "InvalidDateRangeError",
    "WeatherAPIError",
    "PredictionError",
    "FileError",
]
