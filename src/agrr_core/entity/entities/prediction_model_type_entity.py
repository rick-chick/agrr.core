"""Model type enumeration."""

from enum import Enum

class ModelType(Enum):
    """Supported prediction model types."""
    PROPHET = "prophet"
    LSTM = "lstm"
    ARIMA = "arima"
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
