"""Advanced prediction response DTO."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .weather_data_response_dto import WeatherDataResponseDTO
from .forecast_response_dto import ForecastResponseDTO
from .model_accuracy_dto import ModelAccuracyDTO

@dataclass
class AdvancedPredictionResponseDTO:
    """DTO for advanced prediction response."""
    
    historical_data: List[WeatherDataResponseDTO]
    forecasts: Dict[str, List[ForecastResponseDTO]]  # Key: metric name, Value: forecasts
    model_metrics: Dict[str, Any]
    model_accuracy: Optional[ModelAccuracyDTO] = None
    training_info: Optional[Dict[str, Any]] = None
    prediction_metadata: Optional[Dict[str, Any]] = None