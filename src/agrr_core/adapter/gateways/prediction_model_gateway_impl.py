"""Prediction model gateway implementation (Adapter layer).

This gateway receives Framework layer services (via interface injection)
and provides prediction operations to UseCase layer.

NOTE: This gateway is currently not used in CLI commands.
      It is designed for future advanced prediction features:
      - MultiMetricPredictionInteractor (multi-metric forecasting)
      - ModelEvaluationInteractor (model accuracy evaluation)
      - BatchPredictionInteractor (batch processing)
      - ModelManagementInteractor (model information management)
      
      Current CLI uses PredictionGatewayImpl instead for simple file-based predictions.
      When implementing these advanced features, update agrr_core_container.py to use this gateway.
"""

from typing import List, Dict, Any, Optional

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.gateways.prediction_model_gateway import PredictionModelGateway
from agrr_core.adapter.interfaces.ml.prediction_service_interface import PredictionServiceInterface


class PredictionModelGatewayImpl(PredictionModelGateway):
    """
    Gateway implementation for prediction models (Adapter layer).
    
    Receives Framework layer services via dependency injection
    and provides unified prediction interface to UseCase layer.
    """
    
    def __init__(
        self,
        arima_service: Optional[PredictionServiceInterface] = None,
        lightgbm_service: Optional[PredictionServiceInterface] = None,
        default_model: str = 'arima'
    ):
        """
        Initialize prediction model gateway.
        
        Args:
            arima_service: ARIMA prediction service (Framework layer, injected)
            lightgbm_service: LightGBM prediction service (Framework layer, injected)
            default_model: Default model to use ('arima' or 'lightgbm')
        """
        self.models = {}
        
        if arima_service:
            self.models['arima'] = arima_service
        
        if lightgbm_service:
            self.models['lightgbm'] = lightgbm_service
        
        self.default_model = default_model
        
        if not self.models:
            raise ValueError("At least one prediction model service must be provided")
    
    async def predict(
        self,
        historical_data: List[WeatherData],
        metric: str,
        prediction_days: int,
        model_type: Optional[str] = None,
        model_config: Optional[Dict[str, Any]] = None
    ) -> List[Forecast]:
        """
        Predict future values using specified model.
        
        Args:
            historical_data: Historical weather data
            metric: Metric to predict
            prediction_days: Number of days to predict
            model_type: Model type ('arima', 'lightgbm', or None for default)
            model_config: Model-specific configuration
            
        Returns:
            List of forecasts
            
        Raises:
            PredictionError: If prediction fails or model not available
        """
        model_type = model_type or self.default_model
        model_config = model_config or {}
        
        if model_type not in self.models:
            available = ', '.join(self.models.keys())
            raise PredictionError(
                f"Model '{model_type}' not available. Available models: {available}"
            )
        
        model = self.models[model_type]
        
        # Check if sufficient data is available
        required_days = model.get_required_data_days()
        if len(historical_data) < required_days:
            raise PredictionError(
                f"Insufficient data for {model_type}. "
                f"Need at least {required_days} days, got {len(historical_data)} days."
            )
        
        # Delegate to model
        return await model.predict(
            historical_data=historical_data,
            metric=metric,
            prediction_days=prediction_days,
            model_config=model_config
        )
    
    async def evaluate(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str,
        model_type: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Evaluate prediction accuracy.
        
        Args:
            test_data: Actual weather data
            predictions: Model predictions
            metric: Metric being evaluated
            model_type: Model type used for predictions
            
        Returns:
            Dictionary with evaluation metrics
        """
        model_type = model_type or self.default_model
        
        if model_type not in self.models:
            raise PredictionError(f"Model '{model_type}' not available")
        
        model = self.models[model_type]
        return await model.evaluate(test_data, predictions, metric)
    
    def get_model_info(self, model_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about a specific model.
        
        Args:
            model_type: Model type ('arima', 'lightgbm', or None for all)
            
        Returns:
            Model information dictionary
        """
        if model_type:
            if model_type not in self.models:
                raise PredictionError(f"Model '{model_type}' not available")
            return self.models[model_type].get_model_info()
        else:
            # Return info for all available models
            return {
                model_name: model.get_model_info()
                for model_name, model in self.models.items()
            }
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available model types.
        
        Returns:
            List of available model names
        """
        return list(self.models.keys())
    
    async def predict_ensemble(
        self,
        historical_data: List[WeatherData],
        metric: str,
        prediction_days: int,
        model_types: List[str],
        weights: Optional[List[float]] = None,
        model_configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[Forecast]:
        """
        Predict using ensemble of multiple models.
        
        Args:
            historical_data: Historical weather data
            metric: Metric to predict
            prediction_days: Number of days to predict
            model_types: List of model types to ensemble
            weights: Weights for each model (default: equal weights)
            model_configs: Configuration for each model
            
        Returns:
            Ensemble forecasts
        """
        if not model_types:
            raise PredictionError("At least one model type must be specified for ensemble")
        
        # Default weights: equal
        if weights is None:
            weights = [1.0 / len(model_types)] * len(model_types)
        
        if len(weights) != len(model_types):
            raise PredictionError("Number of weights must match number of models")
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        model_configs = model_configs or {}
        
        # Get predictions from each model
        all_predictions = []
        for model_type in model_types:
            if model_type not in self.models:
                raise PredictionError(f"Model '{model_type}' not available for ensemble")
            
            config = model_configs.get(model_type, {})
            preds = await self.predict(
                historical_data, metric, prediction_days, model_type, config
            )
            all_predictions.append(preds)
        
        # Ensemble predictions (weighted average)
        ensemble_forecasts = []
        for i in range(prediction_days):
            # Weighted average of predicted values
            ensemble_value = sum(
                weight * preds[i].predicted_value
                for weight, preds in zip(weights, all_predictions)
            )
            
            # Weighted average of confidence intervals
            ensemble_lower = sum(
                weight * preds[i].confidence_lower
                for weight, preds in zip(weights, all_predictions)
                if preds[i].confidence_lower is not None
            )
            
            ensemble_upper = sum(
                weight * preds[i].confidence_upper
                for weight, preds in zip(weights, all_predictions)
                if preds[i].confidence_upper is not None
            )
            
            forecast = Forecast(
                date=all_predictions[0][i].date,
                predicted_value=ensemble_value,
                confidence_lower=ensemble_lower if ensemble_lower else None,
                confidence_upper=ensemble_upper if ensemble_upper else None
            )
            ensemble_forecasts.append(forecast)
        
        return ensemble_forecasts
    
    # Implement PredictionModelGateway interface methods
    
    async def predict_multiple_metrics(
        self, 
        historical_data: List[WeatherData], 
        metrics: List[str],
        model_config: Dict[str, Any]
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using specified model.
        
        Args:
            historical_data: Historical weather data
            metrics: List of metrics to predict
            model_config: Model configuration including 'model_type' and 'prediction_days'
            
        Returns:
            Dictionary mapping metric names to forecast lists
        """
        model_type = model_config.get('model_type', self.default_model)
        prediction_days = model_config.get('prediction_days', 30)
        
        results = {}
        for metric in metrics:
            forecasts = await self.predict(
                historical_data=historical_data,
                metric=metric,
                prediction_days=prediction_days,
                model_type=model_type,
                model_config=model_config
            )
            results[metric] = forecasts
        
        return results
    
    async def evaluate_model_accuracy(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """Evaluate model accuracy using test data.
        
        Args:
            test_data: Actual weather data
            predictions: Model predictions
            metric: Metric being evaluated
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Use default model for evaluation
        return await self.evaluate(
            test_data=test_data,
            predictions=predictions,
            metric=metric,
            model_type=self.default_model
        )
    
    async def train_model(
        self,
        training_data: List[WeatherData],
        model_config: Dict[str, Any],
        metric: str
    ) -> Dict[str, Any]:
        """Train prediction model with given configuration.
        
        Note: Current implementation uses pre-trained models,
        so this method returns model information.
        
        Args:
            training_data: Training data
            model_config: Model configuration
            metric: Metric to train for
            
        Returns:
            Model training information
        """
        model_type = model_config.get('model_type', self.default_model)
        
        return {
            'model_type': model_type,
            'metric': metric,
            'training_samples': len(training_data),
            'status': 'trained'
        }
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get information about specific model.
        
        Args:
            model_type: Model type to get info for
            
        Returns:
            Model information dictionary
        """
        if model_type not in self.models:
            raise PredictionError(f"Model '{model_type}' not available")
        
        return self.models[model_type].get_model_info()
    
    async def predict_with_confidence_intervals(
        self,
        historical_data: List[WeatherData],
        prediction_days: int,
        confidence_level: float,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict with custom confidence intervals.
        
        Args:
            historical_data: Historical weather data
            prediction_days: Number of days to predict
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            model_config: Model configuration
            
        Returns:
            List of forecasts with confidence intervals
        """
        model_type = model_config.get('model_type', self.default_model)
        metric = model_config.get('metric', 'temperature')
        
        # Add confidence level to config
        config = {**model_config, 'confidence_level': confidence_level}
        
        return await self.predict(
            historical_data=historical_data,
            metric=metric,
            prediction_days=prediction_days,
            model_type=model_type,
            model_config=config
        )
    
    async def batch_predict(
        self,
        historical_data_list: List[List[WeatherData]],
        model_config: Dict[str, Any],
        metrics: List[str]
    ) -> List[Dict[str, List[Forecast]]]:
        """Perform batch prediction for multiple datasets.
        
        Args:
            historical_data_list: List of historical data sets
            model_config: Model configuration
            metrics: Metrics to predict
            
        Returns:
            List of prediction results for each dataset
        """
        results = []
        
        for historical_data in historical_data_list:
            try:
                result = await self.predict_multiple_metrics(
                    historical_data, metrics, model_config
                )
                results.append(result)
            except Exception as e:
                # Add error result
                results.append({'error': str(e)})
        
        return results

