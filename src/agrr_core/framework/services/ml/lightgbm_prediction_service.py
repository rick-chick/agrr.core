"""LightGBM-based weather prediction service implementation (Framework layer)."""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.adapter.interfaces.ml.prediction_service_interface import PredictionServiceInterface
from agrr_core.framework.services.ml.feature_engineering_service import FeatureEngineeringService


class LightGBMPredictionService(PredictionServiceInterface):
    """LightGBM-based prediction service (Framework layer implementation)."""
    
    def __init__(self, model_params: Optional[Dict[str, Any]] = None):
        """
        Initialize LightGBM prediction service.
        
        Args:
            model_params: Optional LightGBM parameters (defaults to optimized params)
        """
        if not LIGHTGBM_AVAILABLE:
            raise ImportError(
                "LightGBM is not installed. Install with: pip install lightgbm"
            )
        
        # Default optimized parameters
        self.model_params = model_params or {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.01,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'n_estimators': 1000,
            'early_stopping_rounds': 50,
        }
        
        self.feature_engineering = FeatureEngineeringService()
        self.model = None
        self.feature_names = None
    
    async def predict(
        self,
        historical_data: List[WeatherData],
        metric: str,
        prediction_days: int,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict future values using LightGBM (implements PredictionModelInterface)."""
        config = {**model_config, 'prediction_days': prediction_days}
        return await self._predict_single_metric(historical_data, metric, config)
    
    async def evaluate(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """Evaluate model accuracy (implements PredictionModelInterface)."""
        return await self.evaluate_model_accuracy(test_data, predictions, metric)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get LightGBM model information (implements PredictionModelInterface)."""
        return {
            'model_type': 'lightgbm',
            'model_name': 'LightGBM',
            'description': 'Light Gradient Boosting Machine',
            'supports_confidence_intervals': True,
            'min_training_samples': 90,
            'recommended_prediction_days': 90,
            'max_prediction_days': 365,
        }
    
    def get_required_data_days(self) -> int:
        """Get minimum required data days (implements PredictionModelInterface)."""
        return 90
    
    async def predict_multiple_metrics(
        self, 
        historical_data: List[WeatherData], 
        metrics: List[str],
        model_config: Dict[str, Any]
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using LightGBM."""
        results = {}
        
        for metric in metrics:
            try:
                forecasts = await self._predict_single_metric(historical_data, metric, model_config)
                results[metric] = forecasts
            except Exception as e:
                raise PredictionError(f"Failed to predict {metric}: {e}")
        
        return results
    
    async def _predict_single_metric(
        self, 
        historical_data: List[WeatherData], 
        metric: str,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict single metric using LightGBM."""
        
        if len(historical_data) < 90:
            raise PredictionError(
                f"Insufficient data for LightGBM. Need at least 90 data points, got {len(historical_data)}."
            )
        
        # Extract lookback days from config
        lookback_days = model_config.get('lookback_days', [1, 7, 14, 30])
        
        # Create features from historical data
        features_df = self.feature_engineering.create_features(
            historical_data, metric, lookback_days
        )
        
        # Get target column
        target_col = self.feature_engineering._get_target_column(metric)
        
        # Get feature names (excluding date and target)
        feature_names = self.feature_engineering.get_feature_names(metric, lookback_days)
        
        # Filter to only available features
        available_features = [f for f in feature_names if f in features_df.columns]
        
        # Prepare training data
        X = features_df[available_features]
        y = features_df[target_col]
        
        # Split into train/validation (use last 20% for validation)
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Train LightGBM model
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        # Update model parameters from config
        params = self.model_params.copy()
        params.update(model_config.get('lgb_params', {}))
        
        # Train model
        model = lgb.train(
            params,
            train_data,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(params.get('early_stopping_rounds', 50))],
        )
        
        # Save model and feature names for feature importance
        self.model = model
        self.feature_names = available_features
        
        # Make direct predictions (non-autoregressive)
        # Use historical patterns for future lag features
        prediction_days = model_config.get('prediction_days', 30)
        
        # Create features for all future days at once using historical patterns
        future_df = self.feature_engineering.create_future_features(
            historical_data, metric, prediction_days, lookback_days
        )
        
        # Filter to available features
        X_future = future_df[available_features]
        
        # Predict all days at once
        predictions = model.predict(X_future, num_iteration=model.best_iteration)
        
        # Calculate confidence intervals using quantile regression (if enabled)
        confidence_lower = None
        confidence_upper = None
        
        if model_config.get('calculate_confidence_intervals', True):
            # Estimate uncertainty using validation residuals
            val_predictions = model.predict(X_val, num_iteration=model.best_iteration)
            residuals = y_val - val_predictions
            
            # Use 95% confidence interval
            std_error = np.std(residuals)
            predictions_array = np.array(predictions)
            confidence_lower = predictions_array - 1.96 * std_error
            confidence_upper = predictions_array + 1.96 * std_error
        
        # Create forecast entities
        forecasts = []
        start_date = historical_data[-1].time + timedelta(days=1)
        
        for i, prediction in enumerate(predictions):
            forecast_date = start_date + timedelta(days=i)
            
            lower = confidence_lower[i] if confidence_lower is not None else None
            upper = confidence_upper[i] if confidence_upper is not None else None
            
            forecast = Forecast(
                date=forecast_date,
                predicted_value=float(prediction),
                confidence_lower=float(lower) if lower is not None else None,
                confidence_upper=float(upper) if upper is not None else None
            )
            forecasts.append(forecast)
        
        return forecasts
    
    async def evaluate_model_accuracy(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """Evaluate LightGBM model accuracy."""
        # Extract target column
        target_col = self.feature_engineering._get_target_column(metric)
        
        # Extract actual values
        actual_values = []
        for weather_data in test_data:
            value = None
            if metric == 'temperature':
                value = weather_data.temperature_2m_mean
            elif metric == 'temperature_max':
                value = weather_data.temperature_2m_max
            elif metric == 'temperature_min':
                value = weather_data.temperature_2m_min
            elif metric == 'precipitation':
                value = weather_data.precipitation_sum
            elif metric == 'sunshine':
                value = weather_data.sunshine_duration
            
            actual_values.append(value)
        
        # Extract predicted values
        predicted_values = [f.predicted_value for f in predictions]
        
        # Ensure same length
        min_length = min(len(actual_values), len(predicted_values))
        actual_values = actual_values[:min_length]
        predicted_values = predicted_values[:min_length]
        
        # Calculate metrics
        mae = np.mean(np.abs(np.array(actual_values) - np.array(predicted_values)))
        mse = np.mean((np.array(actual_values) - np.array(predicted_values)) ** 2)
        rmse = np.sqrt(mse)
        
        # Calculate MAPE (avoid division by zero)
        mape = np.mean([
            abs((actual - pred) / actual) * 100 
            for actual, pred in zip(actual_values, predicted_values) 
            if actual != 0
        ])
        
        # Calculate R²
        ss_res = np.sum((np.array(actual_values) - np.array(predicted_values)) ** 2)
        ss_tot = np.sum((np.array(actual_values) - np.mean(actual_values)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape,
            'r2': r2
        }
    
    async def train_model(
        self,
        training_data: List[WeatherData],
        model_config: Dict[str, Any],
        metric: str
    ) -> Dict[str, Any]:
        """Train LightGBM model."""
        # This is handled in _predict_single_metric
        # Return model info
        return {
            'model_type': 'lightgbm',
            'metric': metric,
            'training_samples': len(training_data),
            'status': 'trained'
        }
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get LightGBM model information."""
        return {
            'model_type': 'lightgbm',
            'description': 'Light Gradient Boosting Machine',
            'supports_confidence_intervals': True,
            'min_training_samples': 90,
            'recommended_params': {
                'num_leaves': 31,
                'learning_rate': 0.01,
                'n_estimators': 1000,
            },
            'features': [
                'temporal_encoding',
                'lag_features',
                'rolling_statistics',
                'cross_metric_features',
            ]
        }
    
    async def predict_with_confidence_intervals(
        self,
        historical_data: List[WeatherData],
        prediction_days: int,
        confidence_level: float,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict with confidence intervals using LightGBM."""
        return await self._predict_single_metric(historical_data, 'temperature', {
            **model_config,
            'prediction_days': prediction_days,
            'calculate_confidence_intervals': True,
        })
    
    async def batch_predict(
        self,
        historical_data_list: List[List[WeatherData]],
        model_config: Dict[str, Any],
        metrics: List[str]
    ) -> List[Dict[str, List[Forecast]]]:
        """Perform batch prediction using LightGBM."""
        results = []
        
        for historical_data in historical_data_list:
            try:
                result = await self.predict_multiple_metrics(historical_data, metrics, model_config)
                results.append(result)
            except Exception as e:
                # Add error result
                results.append({'error': str(e)})
        
        return results
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """
        Get feature importance from trained model.
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.model is None or self.feature_names is None:
            return None
        
        importance = self.model.feature_importance(importance_type='gain')
        return dict(zip(self.feature_names, importance))

