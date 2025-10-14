"""Gateway interfaces for usecase layer."""

from .weather_data_gateway import WeatherDataGateway
from .model_config_gateway import ModelConfigGateway
from .prediction_model_gateway import PredictionModelGateway
from .forecast_gateway import ForecastGateway

__all__ = [
    "WeatherDataGateway",
    "ModelConfigGateway", 
    "PredictionModelGateway",
    "ForecastGateway"
]
