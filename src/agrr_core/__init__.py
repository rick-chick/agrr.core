"""Agrr Core - Weather prediction system."""

from .entity import WeatherData, Location, DateRange, Forecast
from .usecase import (
    FetchWeatherDataInteractor,
    PredictWeatherInteractor,
    WeatherDataOutputPort,
    WeatherPredictionOutputPort,
    WeatherDataRequestDTO,
    PredictionRequestDTO,
)
from .adapter import (
    OpenMeteoWeatherRepository,
    InMemoryWeatherRepository,
    InMemoryPredictionRepository,
    WeatherDataMapper,
)
from .framework import WeatherController

__version__ = "0.1.0"

__all__ = [
    # Entities
    "WeatherData",
    "Location",
    "DateRange",
    "Forecast",
    # Use cases
    "FetchWeatherDataInteractor",
    "PredictWeatherInteractor",
    "WeatherDataOutputPort",
    "WeatherPredictionOutputPort",
    "WeatherDataRequestDTO",
    "PredictionRequestDTO",
    # Adapters
    "OpenMeteoWeatherRepository",
    "InMemoryWeatherRepository",
    "InMemoryPredictionRepository",
    "WeatherDataMapper",
    # Framework
    "WeatherController",
]