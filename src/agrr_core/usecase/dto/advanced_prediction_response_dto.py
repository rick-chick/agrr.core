"""Advanced prediction response DTOs."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from .weather_data_response_dto import WeatherDataResponseDTO
from .forecast_response_dto import ForecastResponseDTO


@dataclass
class ModelAccuracyDTO:
    """DTO for model accuracy metrics."""
    
    model_type: str
    metric: str
    mae: float  # Mean Absolute Error
    mse: float  # Mean Squared Error
    rmse: float  # Root Mean Squared Error
    mape: float  # Mean Absolute Percentage Error
    r2_score: float
    evaluation_date: str
    test_data_points: int


@dataclass
class MultiMetricForecastDTO:
    """DTO for multi-metric forecast results."""
    
    date: str
    metrics: Dict[str, Dict[str, float]]  # {'temperature': {'predicted': 20.5, 'lower': 18.0, 'upper': 23.0}}


@dataclass
class AdvancedPredictionResponseDTO:
    """DTO for advanced prediction response."""
    
    historical_data: List[WeatherDataResponseDTO]
    forecasts: Dict[str, List[ForecastResponseDTO]]  # Key: metric name, Value: forecasts
    model_metrics: Dict[str, Any]
    model_accuracy: Optional[ModelAccuracyDTO] = None
    training_info: Optional[Dict[str, Any]] = None
    prediction_metadata: Optional[Dict[str, Any]] = None


@dataclass
class ModelPerformanceDTO:
    """DTO for model performance comparison."""
    
    model_type: str
    metrics: Dict[str, ModelAccuracyDTO]  # Key: metric name, Value: accuracy
    training_time: float
    prediction_time: float
    model_size: Optional[str] = None
    memory_usage: Optional[str] = None


@dataclass
class BatchPredictionResponseDTO:
    """DTO for batch prediction response."""
    
    results: List[Dict[str, Any]]  # Results for each location
    summary: Dict[str, Any]  # Overall summary statistics
    errors: List[Dict[str, Any]]  # Any errors encountered
    processing_time: float


@dataclass
class VisualizationDataDTO:
    """DTO for visualization data."""
    
    historical_data: List[WeatherDataResponseDTO]
    forecasts: Dict[str, List[ForecastResponseDTO]]
    confidence_intervals: Dict[str, List[Dict[str, float]]]
    trend_analysis: Optional[Dict[str, Any]] = None
    seasonality_analysis: Optional[Dict[str, Any]] = None
