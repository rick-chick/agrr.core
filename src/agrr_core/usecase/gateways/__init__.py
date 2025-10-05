"""Gateway interfaces for usecase layer."""

from .weather_data_gateway import WeatherDataGateway
from .weather_data_repository_gateway import WeatherDataRepositoryGateway
from .prediction_service_gateway import PredictionServiceGateway
from .weather_repository_gateway import WeatherRepositoryGateway
from .prediction_repository_gateway import PredictionRepositoryGateway

__all__ = [
    "WeatherDataGateway",
    "WeatherDataRepositoryGateway", 
    "PredictionServiceGateway",
    "WeatherRepositoryGateway",
    "PredictionRepositoryGateway"
]
