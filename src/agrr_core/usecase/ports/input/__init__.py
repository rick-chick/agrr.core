"""Input ports package."""

from .fetch_weather_data_input_port import FetchWeatherDataInputPort
from .predict_weather_input_port import PredictWeatherInputPort
from .advanced_prediction_input_port import AdvancedPredictionInputPort

__all__ = [
    "FetchWeatherDataInputPort",
    "PredictWeatherInputPort",
    "AdvancedPredictionInputPort"
]
