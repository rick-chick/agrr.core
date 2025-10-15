"""Machine learning service interfaces."""

from .prediction_service_interface import PredictionServiceInterface
from .time_series_service_interface import (
    TimeSeriesServiceInterface,
    TimeSeriesModelInterface,
    FittedTimeSeriesModelInterface,
)

__all__ = [
    'PredictionServiceInterface',
    'TimeSeriesServiceInterface',
    'TimeSeriesModelInterface',
    'FittedTimeSeriesModelInterface',
]

