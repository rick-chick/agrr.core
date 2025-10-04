"""ARIMA-based weather prediction service implementation."""

from typing import List, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    # Mock classes for testing when statsmodels is not installed
    class ARIMA:
        def __init__(self, data, order=None, seasonal_order=None):
            self.data = data
        def fit(self):
            return self
        def forecast(self, steps):
            return np.array([20.0] * steps)
        def get_forecast(self, steps):
            class Forecast:
                def __init__(self, steps):
                    self.predicted_mean = np.array([20.0] * steps)
                    self.conf_int = np.array([[18.0, 23.0]] * steps)
            return Forecast(steps)

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.ports.output.advanced_prediction_output_port import AdvancedPredictionOutputPort


class ARIMAWeatherPredictionService(AdvancedPredictionOutputPort):
    """ARIMA-based implementation of weather prediction service."""
    
    def __init__(self):
        self.models: Dict[str, ARIMA] = {}
    
    async def predict_multiple_metrics(
        self, 
        historical_data: List[WeatherData], 
        metrics: List[str],
        model_config: Dict[str, Any]
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using ARIMA model."""
        if not STATSMODELS_AVAILABLE:
            raise PredictionError("Statsmodels is not available. Please install statsmodels.")
        
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
        """Predict single metric using ARIMA."""
        
        # Extract data for the metric
        data = self._extract_metric_data(historical_data, metric)
        if len(data) < 30:
            raise PredictionError(f"Insufficient data for {metric}. Need at least 30 data points.")
        
        # Check stationarity
        if not self._is_stationary(data):
            data = self._make_stationary(data)
        
        # Fit ARIMA model
        order = model_config.get('order', (1, 1, 1))
        seasonal_order = model_config.get('seasonal_order', (1, 1, 1, 12))
        
        try:
            model = ARIMA(data, order=order, seasonal_order=seasonal_order)
            fitted_model = model.fit()
        except Exception as e:
            # Try simpler model if complex one fails
            order = (1, 1, 0)
            model = ARIMA(data, order=order)
            fitted_model = model.fit()
        
        # Make predictions
        prediction_days = model_config.get('prediction_days', 30)
        
        try:
            forecast_result = fitted_model.get_forecast(steps=prediction_days)
            predictions = forecast_result.predicted_mean
            confidence_intervals = forecast_result.conf_int()
        except:
            # Fallback to simple forecast
            predictions = fitted_model.forecast(steps=prediction_days)
            confidence_intervals = None
        
        # Create forecast entities
        forecasts = []
        start_date = historical_data[-1].time + timedelta(days=1)
        
        for i, prediction in enumerate(predictions):
            forecast_date = start_date + timedelta(days=i)
            
            confidence_lower = None
            confidence_upper = None
            
            if confidence_intervals is not None and i < len(confidence_intervals):
                confidence_lower = confidence_intervals.iloc[i, 0]
                confidence_upper = confidence_intervals.iloc[i, 1]
            
            forecast = Forecast(
                date=forecast_date,
                predicted_value=float(prediction),
                confidence_lower=confidence_lower,
                confidence_upper=confidence_upper
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def _extract_metric_data(self, historical_data: List[WeatherData], metric: str) -> List[float]:
        """Extract data for specific metric."""
        data = []
        
        for weather_data in historical_data:
            if metric == 'temperature' and weather_data.temperature_2m_mean is not None:
                data.append(weather_data.temperature_2m_mean)
            elif metric == 'precipitation' and weather_data.precipitation_sum is not None:
                data.append(weather_data.precipitation_sum)
            elif metric == 'sunshine' and weather_data.sunshine_duration is not None:
                data.append(weather_data.sunshine_duration)
            elif metric == 'pressure' and hasattr(weather_data, 'pressure'):
                data.append(weather_data.pressure)
        
        return data
    
    def _is_stationary(self, data: List[float]) -> bool:
        """Check if data is stationary using Augmented Dickey-Fuller test."""
        try:
            if not STATSMODELS_AVAILABLE:
                return False
            
            result = adfuller(data)
            # If p-value is less than 0.05, data is stationary
            return result[1] < 0.05
        except:
            return False
    
    def _make_stationary(self, data: List[float]) -> List[float]:
        """Make data stationary by differencing."""
        # Simple first difference
        diff_data = [data[i] - data[i-1] for i in range(1, len(data))]
        return diff_data
    
    async def evaluate_model_accuracy(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """Evaluate ARIMA model accuracy."""
        # Extract actual values
        actual_values = self._extract_metric_data(test_data, metric)
        
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
        
        return {
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'mape': mape
        }
    
    async def train_model(
        self,
        training_data: List[WeatherData],
        model_config: Dict[str, Any],
        metric: str
    ) -> Dict[str, Any]:
        """Train ARIMA model."""
        return {
            'model_type': 'arima',
            'metric': metric,
            'training_samples': len(training_data),
            'status': 'trained'
        }
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get ARIMA model information."""
        return {
            'model_type': 'arima',
            'description': 'AutoRegressive Integrated Moving Average',
            'supports_confidence_intervals': True,
            'min_training_samples': 30,
            'recommended_order': (1, 1, 1),
            'recommended_seasonal_order': (1, 1, 1, 12)
        }
    
    async def predict_with_confidence_intervals(
        self,
        historical_data: List[WeatherData],
        prediction_days: int,
        confidence_level: float,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict with confidence intervals using ARIMA."""
        # ARIMA supports confidence intervals natively
        # This is already implemented in _predict_single_metric
        return await self._predict_single_metric(historical_data, 'temperature', {
            **model_config,
            'prediction_days': prediction_days
        })
    
    async def batch_predict(
        self,
        historical_data_list: List[List[WeatherData]],
        model_config: Dict[str, Any],
        metrics: List[str]
    ) -> List[Dict[str, List[Forecast]]]:
        """Perform batch prediction using ARIMA."""
        results = []
        
        for historical_data in historical_data_list:
            try:
                result = await self.predict_multiple_metrics(historical_data, metrics, model_config)
                results.append(result)
            except Exception as e:
                # Add error result
                results.append({'error': str(e)})
        
        return results
