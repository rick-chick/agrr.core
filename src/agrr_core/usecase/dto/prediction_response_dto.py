"""Prediction response DTO."""

from dataclasses import dataclass
from typing import List, Optional

from .weather_data_response_dto import WeatherDataResponseDTO
from .forecast_response_dto import ForecastResponseDTO


@dataclass
class PredictionResponseDTO:
    """DTO for prediction response."""
    
    historical_data: List[WeatherDataResponseDTO]
    forecast: List[ForecastResponseDTO]
    model_metrics: Optional[dict] = None
