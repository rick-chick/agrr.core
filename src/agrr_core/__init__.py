"""Agrr Core - Weather prediction system."""

from .entity import WeatherData, Location, DateRange, Forecast
from .usecase import (
    FetchWeatherDataInteractor,
    PredictWeatherInteractor,
    WeatherPredictionOutputPort,
    WeatherPresenterOutputPort,
    PredictionPresenterOutputPort,
    WeatherDataRequestDTO,
    PredictionRequestDTO,
)
from .adapter import (
    OpenMeteoWeatherRepository,
    InMemoryWeatherRepository,
    InMemoryPredictionRepository,
    WeatherDataMapper,
    WeatherPresenter,
    PredictionPresenter,
)
from .adapter.controllers.weather_api_controller import WeatherController

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
    "WeatherPredictionOutputPort",
    "WeatherPresenterOutputPort",
    "PredictionPresenterOutputPort",
    "WeatherDataRequestDTO",
    "PredictionRequestDTO",
    # Adapters
    "OpenMeteoWeatherRepository",
    "InMemoryWeatherRepository",
    "InMemoryPredictionRepository",
    "WeatherDataMapper",
    "WeatherPresenter",
    "PredictionPresenter",
    # Framework
    "WeatherController",
]