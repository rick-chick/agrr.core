"""Visualization data DTO."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .weather_data_response_dto import WeatherDataResponseDTO
from .forecast_response_dto import ForecastResponseDTO


@dataclass
class VisualizationDataDTO:
    """DTO for visualization data."""
    
    historical_data: List[WeatherDataResponseDTO]
    forecasts: Dict[str, List[ForecastResponseDTO]]
    confidence_intervals: Dict[str, List[Dict[str, float]]]
    trend_analysis: Optional[Dict[str, Any]] = None
    seasonality_analysis: Optional[Dict[str, Any]] = None
