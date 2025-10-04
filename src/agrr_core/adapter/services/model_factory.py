"""Model factory for creating prediction models."""

from typing import Dict, Any, List
from agrr_core.entity.entities.prediction_model import ModelType, PredictionModel, MetricType


class ModelFactory:
    """Factory for creating prediction model configurations."""
    
    @staticmethod
    def get_available_models() -> List[PredictionModel]:
        """Get list of available prediction models."""
        return [
            PredictionModel(
                model_type=ModelType.PROPHET,
                name="Facebook Prophet",
                description="Additive regression model with seasonal components",
                supported_metrics=[
                    MetricType.TEMPERATURE, 
                    MetricType.PRECIPITATION, 
                    MetricType.SUNSHINE
                ],
                default_params={
                    "yearly_seasonality": True,
                    "weekly_seasonality": False,
                    "daily_seasonality": False,
                    "seasonality_mode": "additive",
                    "changepoint_prior_scale": 0.05
                },
                min_training_data_points=30,
                max_prediction_horizon=365,
                supports_confidence_intervals=True,
                supports_seasonality=True,
                supports_trend=True
            ),
            PredictionModel(
                model_type=ModelType.LSTM,
                name="Long Short-Term Memory",
                description="Deep learning model for time series prediction",
                supported_metrics=[
                    MetricType.TEMPERATURE, 
                    MetricType.PRECIPITATION, 
                    MetricType.SUNSHINE,
                    MetricType.HUMIDITY
                ],
                default_params={
                    "units": 50,
                    "dropout": 0.2,
                    "recurrent_dropout": 0.2,
                    "epochs": 100,
                    "batch_size": 32,
                    "sequence_length": 30
                },
                min_training_data_points=100,
                max_prediction_horizon=90,
                supports_confidence_intervals=False,
                supports_seasonality=True,
                supports_trend=True
            ),
            PredictionModel(
                model_type=ModelType.ARIMA,
                name="AutoRegressive Integrated Moving Average",
                description="Statistical model for time series forecasting",
                supported_metrics=[
                    MetricType.TEMPERATURE, 
                    MetricType.PRESSURE
                ],
                default_params={
                    "order": (1, 1, 1),
                    "seasonal_order": (1, 1, 1, 12),
                    "trend": "c"
                },
                min_training_data_points=50,
                max_prediction_horizon=30,
                supports_confidence_intervals=True,
                supports_seasonality=True,
                supports_trend=True
            ),
            PredictionModel(
                model_type=ModelType.LINEAR_REGRESSION,
                name="Linear Regression",
                description="Simple linear regression model",
                supported_metrics=[
                    MetricType.TEMPERATURE
                ],
                default_params={
                    "fit_intercept": True,
                    "normalize": False
                },
                min_training_data_points=10,
                max_prediction_horizon=7,
                supports_confidence_intervals=True,
                supports_seasonality=False,
                supports_trend=False
            ),
            PredictionModel(
                model_type=ModelType.RANDOM_FOREST,
                name="Random Forest Regressor",
                description="Ensemble learning method for regression",
                supported_metrics=[
                    MetricType.TEMPERATURE, 
                    MetricType.PRECIPITATION, 
                    MetricType.SUNSHINE
                ],
                default_params={
                    "n_estimators": 100,
                    "max_depth": 10,
                    "min_samples_split": 2,
                    "min_samples_leaf": 1,
                    "random_state": 42
                },
                min_training_data_points=50,
                max_prediction_horizon=30,
                supports_confidence_intervals=False,
                supports_seasonality=False,
                supports_trend=False
            )
        ]
    
    @staticmethod
    def get_model_by_type(model_type: ModelType) -> PredictionModel:
        """Get specific model configuration by type."""
        models = ModelFactory.get_available_models()
        for model in models:
            if model.model_type == model_type:
                return model
        raise ValueError(f"Model type {model_type} not found")
    
    @staticmethod
    def validate_config(model_type: ModelType, config: Dict[str, Any]) -> bool:
        """Validate model configuration."""
        model = ModelFactory.get_model_by_type(model_type)
        
        # Check required parameters
        for param, default_value in model.default_params.items():
            if param not in config:
                config[param] = default_value
        
        # Model-specific validation
        if model_type == ModelType.LSTM:
            if config.get("epochs", 100) < 10:
                return False
            if config.get("sequence_length", 30) < 7:
                return False
        
        elif model_type == ModelType.ARIMA:
            order = config.get("order", (1, 1, 1))
            if len(order) != 3:
                return False
        
        return True
