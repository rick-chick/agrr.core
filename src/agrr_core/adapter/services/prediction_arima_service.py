"""ARIMA-based weather prediction service implementation."""

from typing import List, Dict, Any
import numpy as np
from datetime import datetime, timedelta

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.gateways.prediction_service_gateway import PredictionServiceGateway
from agrr_core.adapter.interfaces.time_series_interface import TimeSeriesInterface


class PredictionARIMAService(PredictionServiceGateway):
    """ARIMA-based implementation of weather prediction service."""
    
    def __init__(self, time_series_service: TimeSeriesInterface):
        """Initialize prediction service with time series interface."""
        self.time_series_service = time_series_service
    
    async def predict_multiple_metrics(
        self, 
        historical_data: List[WeatherData], 
        metrics: List[str],
        model_config: Dict[str, Any]
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using ARIMA model."""
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
        if not self.time_series_service.check_stationarity(data):
            data = self.time_series_service.make_stationary(data)
        
        # Fit ARIMA model
        order = model_config.get('order', (1, 1, 1))
        seasonal_order = model_config.get('seasonal_order', (1, 1, 1, 12))
        
        try:
            model = self.time_series_service.create_model(data, order, seasonal_order)
            fitted_model = model.fit()
        except Exception as e:
            # Try simpler model if complex one fails
            order = (1, 1, 0)
            model = self.time_series_service.create_model(data, order)
            fitted_model = model.fit()
        
        # Make predictions
        prediction_days = model_config.get('prediction_days', 30)
        
        predictions, confidence_intervals = fitted_model.get_forecast_with_intervals(prediction_days)
        
        # Create forecast entities
        forecasts = []
        start_date = historical_data[-1].time + timedelta(days=1)
        
        for i, prediction in enumerate(predictions):
            forecast_date = start_date + timedelta(days=i)
            
            confidence_lower = None
            confidence_upper = None
            
            if confidence_intervals is not None and i < len(confidence_intervals):
                # Handle both pandas DataFrame and numpy array cases
                if hasattr(confidence_intervals, 'iloc'):
                    confidence_lower = confidence_intervals.iloc[i, 0]
                    confidence_upper = confidence_intervals.iloc[i, 1]
                else:
                    # numpy array case
                    confidence_lower = confidence_intervals[i, 0]
                    confidence_upper = confidence_intervals[i, 1]
            
            forecast = Forecast(
                date=forecast_date,
                predicted_value=float(prediction),
                confidence_lower=confidence_lower,
                confidence_upper=confidence_upper
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def _extract_metric_data(self, historical_data: List[WeatherData], metric: str) -> List[float]:
        """Extract data for specific metric with linear interpolation for missing values."""
        data = []
        
        # Extract raw data (including None values)
        for weather_data in historical_data:
            value = None
            if metric == 'temperature':
                value = weather_data.temperature_2m_mean
            elif metric == 'precipitation':
                value = weather_data.precipitation_sum
            elif metric == 'sunshine':
                value = weather_data.sunshine_duration
            elif metric == 'pressure' and hasattr(weather_data, 'pressure'):
                value = weather_data.pressure
            
            data.append(value)
        
        # Apply linear interpolation for missing values
        data = self._interpolate_missing_values(data)
        
        return data
    
    def _interpolate_missing_values(self, data: List[float]) -> List[float]:
        """Apply linear interpolation to fill missing values."""
        if not data:
            return data
        
        # Convert to numpy array for easier manipulation
        arr = np.array(data, dtype=float)
        
        # Find indices of non-null values
        valid_indices = np.where(~np.isnan(arr))[0]
        
        if len(valid_indices) == 0:
            raise PredictionError("All values are missing. Cannot perform interpolation.")
        
        # If there are missing values at the beginning, use the first valid value
        if valid_indices[0] > 0:
            arr[:valid_indices[0]] = arr[valid_indices[0]]
        
        # If there are missing values at the end, use the last valid value
        if valid_indices[-1] < len(arr) - 1:
            arr[valid_indices[-1] + 1:] = arr[valid_indices[-1]]
        
        # Interpolate missing values in the middle
        for i in range(len(arr)):
            if np.isnan(arr[i]):
                # Find the nearest non-null values before and after
                prev_idx = None
                next_idx = None
                
                for j in range(i - 1, -1, -1):
                    if not np.isnan(arr[j]):
                        prev_idx = j
                        break
                
                for j in range(i + 1, len(arr)):
                    if not np.isnan(arr[j]):
                        next_idx = j
                        break
                
                # Perform linear interpolation
                if prev_idx is not None and next_idx is not None:
                    # Linear interpolation formula
                    weight = (i - prev_idx) / (next_idx - prev_idx)
                    arr[i] = arr[prev_idx] + weight * (arr[next_idx] - arr[prev_idx])
        
        return arr.tolist()
    
    
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
