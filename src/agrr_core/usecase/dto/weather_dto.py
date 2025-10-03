"""Weather-related DTOs."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class WeatherDataRequestDTO:
    """DTO for weather data request."""
    
    latitude: float
    longitude: float
    start_date: str
    end_date: str


@dataclass
class WeatherDataResponseDTO:
    """DTO for weather data response."""
    
    time: str
    temperature_2m_max: Optional[float] = None
    temperature_2m_min: Optional[float] = None
    temperature_2m_mean: Optional[float] = None
    precipitation_sum: Optional[float] = None
    sunshine_duration: Optional[float] = None
    sunshine_hours: Optional[float] = None


@dataclass
class WeatherDataListResponseDTO:
    """DTO for weather data list response."""
    
    data: List[WeatherDataResponseDTO]
    total_count: int


@dataclass
class PredictionRequestDTO:
    """DTO for prediction request."""
    
    latitude: float
    longitude: float
    start_date: str
    end_date: str
    prediction_days: int = 365


@dataclass
class ForecastResponseDTO:
    """DTO for forecast response."""
    
    date: str
    predicted_value: float
    confidence_lower: Optional[float] = None
    confidence_upper: Optional[float] = None


@dataclass
class PredictionResponseDTO:
    """DTO for prediction response."""
    
    historical_data: List[WeatherDataResponseDTO]
    forecast: List[ForecastResponseDTO]
    model_metrics: Optional[dict] = None
