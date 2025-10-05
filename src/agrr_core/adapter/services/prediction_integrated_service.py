"""Integrated prediction service that manages multiple models."""

from typing import List, Dict, Any, Optional
from datetime import datetime

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.entities.prediction_entity import ModelType
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.gateways.prediction_service_gateway import PredictionServiceGateway
from agrr_core.adapter.services.prediction_model_factory_service import ModelFactory
from agrr_core.adapter.services.prediction_prophet_service import ProphetWeatherPredictionService
from agrr_core.adapter.services.prediction_lstm_service import LSTMWeatherPredictionService
from agrr_core.adapter.services.prediction_arima_service import ARIMAWeatherPredictionService


class IntegratedPredictionService(PredictionServiceGateway):
    """Integrated service that manages multiple prediction models."""
    
    def __init__(self):
        self.model_services = {
            ModelType.PROPHET: ProphetWeatherPredictionService(),
            ModelType.LSTM: LSTMWeatherPredictionService(),
            ModelType.ARIMA: ARIMAWeatherPredictionService()
        }
        self.model_factory = ModelFactory()
    
    async def predict_multiple_metrics(
        self, 
        historical_data: List[WeatherData], 
        metrics: List[str],
        model_config: Dict[str, Any]
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using specified model."""
        
        model_type_str = model_config.get('model_type', 'prophet')
        try:
            model_type = ModelType(model_type_str)
        except ValueError:
            raise PredictionError(f"Unsupported model type: {model_type_str}")
        
        # Validate configuration
        if not self.model_factory.validate_config(model_type, model_config):
            raise PredictionError(f"Invalid configuration for {model_type.value} model")
        
        # Get model service
        if model_type not in self.model_services:
            raise PredictionError(f"Model service not available for {model_type.value}")
        
        service = self.model_services[model_type]
        
        # Check if model supports requested metrics
        model_info = self.model_factory.get_model_by_type(model_type)
        supported_metrics = [m.value for m in model_info.supported_metrics]
        
        unsupported_metrics = [m for m in metrics if m not in supported_metrics]
        if unsupported_metrics:
            raise PredictionError(
                f"Model {model_type.value} does not support metrics: {unsupported_metrics}"
            )
        
        # Check minimum training data requirements
        if len(historical_data) < model_info.min_training_data_points:
            raise PredictionError(
                f"Insufficient training data. {model_type.value} requires at least "
                f"{model_info.min_training_data_points} data points, got {len(historical_data)}"
            )
        
        # Check prediction horizon
        prediction_days = model_config.get('prediction_days', 30)
        if prediction_days > model_info.max_prediction_horizon:
            raise PredictionError(
                f"Prediction horizon too large. {model_type.value} supports maximum "
                f"{model_info.max_prediction_horizon} days, requested {prediction_days}"
            )
        
        # Perform prediction
        return await service.predict_multiple_metrics(historical_data, metrics, model_config)
    
    async def evaluate_model_accuracy(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """Evaluate model accuracy."""
        
        # Determine model type from predictions (this is a simplified approach)
        # In a real implementation, you'd store model metadata with predictions
        model_type = ModelType.PROPHET  # Default fallback
        
        service = self.model_services[model_type]
        return await service.evaluate_model_accuracy(test_data, predictions, metric)
    
    async def train_model(
        self,
        training_data: List[WeatherData],
        model_config: Dict[str, Any],
        metric: str
    ) -> Dict[str, Any]:
        """Train model with given configuration."""
        
        model_type_str = model_config.get('model_type', 'prophet')
        try:
            model_type = ModelType(model_type_str)
        except ValueError:
            raise PredictionError(f"Unsupported model type: {model_type_str}")
        
        if model_type not in self.model_services:
            raise PredictionError(f"Model service not available for {model_type.value}")
        
        service = self.model_services[model_type]
        return await service.train_model(training_data, model_config, metric)
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get model information."""
        try:
            model_type_enum = ModelType(model_type)
            model_info = self.model_factory.get_model_by_type(model_type_enum)
            
            return {
                'model_type': model_type,
                'name': model_info.name,
                'description': model_info.description,
                'supported_metrics': [m.value for m in model_info.supported_metrics],
                'min_training_data_points': model_info.min_training_data_points,
                'max_prediction_horizon': model_info.max_prediction_horizon,
                'supports_confidence_intervals': model_info.supports_confidence_intervals,
                'supports_seasonality': model_info.supports_seasonality,
                'supports_trend': model_info.supports_trend,
                'default_params': model_info.default_params
            }
        except ValueError:
            raise PredictionError(f"Unsupported model type: {model_type}")
    
    async def predict_with_confidence_intervals(
        self,
        historical_data: List[WeatherData],
        prediction_days: int,
        confidence_level: float,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict with confidence intervals."""
        
        model_type_str = model_config.get('model_type', 'prophet')
        try:
            model_type = ModelType(model_type_str)
        except ValueError:
            raise PredictionError(f"Unsupported model type: {model_type_str}")
        
        model_info = self.model_factory.get_model_by_type(model_type)
        
        if not model_info.supports_confidence_intervals:
            raise PredictionError(
                f"Model {model_type.value} does not support confidence intervals"
            )
        
        if model_type not in self.model_services:
            raise PredictionError(f"Model service not available for {model_type.value}")
        
        service = self.model_services[model_type]
        return await service.predict_with_confidence_intervals(
            historical_data, prediction_days, confidence_level, model_config
        )
    
    async def batch_predict(
        self,
        historical_data_list: List[List[WeatherData]],
        model_config: Dict[str, Any],
        metrics: List[str]
    ) -> List[Dict[str, List[Forecast]]]:
        """Perform batch prediction."""
        
        model_type_str = model_config.get('model_type', 'prophet')
        try:
            model_type = ModelType(model_type_str)
        except ValueError:
            raise PredictionError(f"Unsupported model type: {model_type_str}")
        
        if model_type not in self.model_services:
            raise PredictionError(f"Model service not available for {model_type.value}")
        
        service = self.model_services[model_type]
        return await service.batch_predict(historical_data_list, model_config, metrics)
    
    async def compare_models(
        self,
        historical_data: List[WeatherData],
        test_data: List[WeatherData],
        metrics: List[str],
        model_configs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compare performance of different models."""
        
        comparison_results = {}
        
        for config in model_configs:
            model_type = config.get('model_type', 'prophet')
            
            try:
                # Make predictions
                predictions = await self.predict_multiple_metrics(
                    historical_data, metrics, config
                )
                
                # Evaluate accuracy
                accuracy_results = {}
                for metric in metrics:
                    if metric in predictions:
                        metric_predictions = predictions[metric]
                        accuracy = await self.evaluate_model_accuracy(
                            test_data, metric_predictions, metric
                        )
                        accuracy_results[metric] = accuracy
                
                comparison_results[model_type] = {
                    'predictions': predictions,
                    'accuracy': accuracy_results,
                    'config': config
                }
                
            except Exception as e:
                comparison_results[model_type] = {
                    'error': str(e),
                    'config': config
                }
        
        return comparison_results
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with their information."""
        models = self.model_factory.get_available_models()
        
        result = []
        for model in models:
            result.append({
                'model_type': model.model_type.value,
                'name': model.name,
                'description': model.description,
                'supported_metrics': [m.value for m in model.supported_metrics],
                'min_training_data_points': model.min_training_data_points,
                'max_prediction_horizon': model.max_prediction_horizon,
                'supports_confidence_intervals': model.supports_confidence_intervals,
                'supports_seasonality': model.supports_seasonality,
                'supports_trend': model.supports_trend
            })
        
        return result
