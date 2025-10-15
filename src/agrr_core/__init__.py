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
    WeatherMapper,
    WeatherPresenter,
    PredictionPresenter,
)
from .adapter.gateways import (
    ForecastInMemoryGateway,
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
    "ForecastInMemoryGateway",
    "WeatherMapper",
    "WeatherPresenter",
    "PredictionPresenter",
    # Framework
]