"""Input ports package."""

from .weather_data_input_port import WeatherDataInputPort
from .weather_prediction_input_port import WeatherPredictionInputPort

__all__ = [
    "WeatherDataInputPort",
    "WeatherPredictionInputPort",
]
