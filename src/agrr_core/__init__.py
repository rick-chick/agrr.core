"""Agrr Core - Weather prediction system."""

from .entity import WeatherData, Location, DateRange, Forecast
from .usecase import (
    FetchWeatherDataInteractor,
    WeatherPredictInteractor,
    WeatherPredictionOutputPort,
    WeatherPresenterOutputPort,
    PredictionPresenterOutputPort,
    WeatherDataRequestDTO,
    PredictionRequestDTO,
)
from .adapter import (
    WeatherAPIOpenMeteoRepository,
    PredictionStorageRepository,
    WeatherMapper,
    WeatherPresenter,
    PredictionPresenter,
)

__version__ = "0.1.0"

__all__ = [
    # Entities
    "WeatherData",
    "Location",
    "DateRange",
    "Forecast",
    # Use cases
    "FetchWeatherDataInteractor",
    "WeatherPredictInteractor",
    "WeatherPredictionOutputPort",
    "WeatherPresenterOutputPort",
    "PredictionPresenterOutputPort",
    "WeatherDataRequestDTO",
    "PredictionRequestDTO",
    # Adapters
    "WeatherAPIOpenMeteoRepository",
    "PredictionStorageRepository",
    "WeatherMapper",
    "WeatherPresenter",
    "PredictionPresenter",
    # Framework
]