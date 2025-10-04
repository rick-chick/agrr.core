"""Adapter layer interfaces package."""

from .weather_service_interface import WeatherServiceInterface
from .prediction_service_interface import PredictionServiceInterface

__all__ = [
    "WeatherServiceInterface",
    "PredictionServiceInterface",
]
