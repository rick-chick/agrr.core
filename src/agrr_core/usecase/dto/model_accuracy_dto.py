"""Model accuracy DTO."""

from dataclasses import dataclass

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
