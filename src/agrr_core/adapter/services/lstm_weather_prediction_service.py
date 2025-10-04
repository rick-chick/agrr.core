"""LSTM-based weather prediction service implementation."""

from typing import List, Dict, Any
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    from sklearn.preprocessing import MinMaxScaler
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    # Mock classes for testing when TensorFlow is not installed
    class Sequential:
        def __init__(self):
            pass
        def add(self, layer):
            pass
        def compile(self, **kwargs):
            pass
        def fit(self, **kwargs):
            pass
        def predict(self, x):
            return np.array([[20.0] * 10])  # Mock prediction
    
    class LSTM:
        def __init__(self, **kwargs):
            pass
    
    class Dense:
        def __init__(self, **kwargs):
            pass
    
    class Dropout:
        def __init__(self, **kwargs):
            pass
    
    class MinMaxScaler:
        def __init__(self):
            pass
        def fit_transform(self, data):
            return data
        def inverse_transform(self, data):
            return data

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.ports.output.advanced_prediction_output_port import AdvancedPredictionOutputPort


class LSTMWeatherPredictionService(AdvancedPredictionOutputPort):
    """LSTM-based implementation of weather prediction service."""
    
    def __init__(self):
        self.models: Dict[str, Sequential] = {}
        self.scalers: Dict[str, MinMaxScaler] = {}
        self.sequence_length = 30
    
    async def predict_multiple_metrics(
        self, 
        historical_data: List[WeatherData], 
        metrics: List[str],
        model_config: Dict[str, Any]
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using LSTM model."""
        if not TENSORFLOW_AVAILABLE:
            raise PredictionError("TensorFlow is not available. Please install tensorflow.")
        
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
        """Predict single metric using LSTM."""
        
        # Extract data for the metric
        data = self._extract_metric_data(historical_data, metric)
        if len(data) < self.sequence_length:
            raise PredictionError(f"Insufficient data for {metric}. Need at least {self.sequence_length} data points.")
        
        # Prepare data
        X, y = self._prepare_lstm_data(data, self.sequence_length)
        
        # Scale data
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)
        y_scaled = scaler.fit_transform(y.reshape(-1, 1))
        
        # Build model
        model = self._build_lstm_model(model_config)
        
        # Train model
        model.fit(
            X_scaled, 
            y_scaled, 
            epochs=model_config.get('epochs', 100),
            batch_size=model_config.get('batch_size', 32),
            validation_split=model_config.get('validation_split', 0.2),
            verbose=0
        )
        
        # Make predictions
        prediction_days = model_config.get('prediction_days', 30)
        forecasts = []
        
        # Use last sequence for prediction
        last_sequence = X_scaled[-1:].reshape(1, self.sequence_length, 1)
        
        for i in range(prediction_days):
            # Predict next value
            next_prediction = model.predict(last_sequence, verbose=0)
            next_value = scaler.inverse_transform(next_prediction)[0, 0]
            
            # Create forecast
            forecast_date = historical_data[-1].time + timedelta(days=i+1)
            forecast = Forecast(
                date=forecast_date,
                predicted_value=next_value,
                confidence_lower=None,  # LSTM doesn't provide confidence intervals easily
                confidence_upper=None
            )
            forecasts.append(forecast)
            
            # Update sequence for next prediction
            last_sequence = np.roll(last_sequence, -1, axis=1)
            last_sequence[0, -1, 0] = next_prediction[0, 0]
        
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
            elif metric == 'humidity' and hasattr(weather_data, 'humidity'):
                data.append(weather_data.humidity)
        
        return data
    
    def _prepare_lstm_data(self, data: List[float], sequence_length: int) -> tuple:
        """Prepare data for LSTM training."""
        X, y = [], []
        
        for i in range(sequence_length, len(data)):
            X.append(data[i-sequence_length:i])
            y.append(data[i])
        
        return np.array(X), np.array(y)
    
    def _build_lstm_model(self, config: Dict[str, Any]) -> Sequential:
        """Build LSTM model."""
        model = Sequential()
        
        # LSTM layer
        model.add(LSTM(
            units=config.get('units', 50),
            return_sequences=False,
            input_shape=(self.sequence_length, 1)
        ))
        
        # Dropout layer
        model.add(Dropout(config.get('dropout', 0.2)))
        
        # Dense layer
        model.add(Dense(1))
        
        # Compile model
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    async def evaluate_model_accuracy(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """Evaluate LSTM model accuracy."""
        # Extract actual values
        actual_values = self._extract_metric_data(test_data, metric)
        
        # Extract predicted values
        predicted_values = [f.predicted_value for f in predictions]
        
        # Calculate metrics
        mae = np.mean(np.abs(np.array(actual_values) - np.array(predicted_values)))
        mse = np.mean((np.array(actual_values) - np.array(predicted_values)) ** 2)
        rmse = np.sqrt(mse)
        
        # Calculate MAPE
        mape = np.mean(np.abs((np.array(actual_values) - np.array(predicted_values)) / np.array(actual_values))) * 100
        
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
        """Train LSTM model."""
        # This would be implemented for model training
        return {
            'model_type': 'lstm',
            'metric': metric,
            'training_samples': len(training_data),
            'status': 'trained'
        }
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get LSTM model information."""
        return {
            'model_type': 'lstm',
            'description': 'Long Short-Term Memory neural network',
            'supports_confidence_intervals': False,
            'min_training_samples': 100,
            'recommended_sequence_length': 30
        }
    
    async def predict_with_confidence_intervals(
        self,
        historical_data: List[WeatherData],
        prediction_days: int,
        confidence_level: float,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """LSTM doesn't easily support confidence intervals."""
        raise PredictionError("LSTM model does not support confidence intervals")
    
    async def batch_predict(
        self,
        historical_data_list: List[List[WeatherData]],
        model_config: Dict[str, Any],
        metrics: List[str]
    ) -> List[Dict[str, List[Forecast]]]:
        """Perform batch prediction using LSTM."""
        results = []
        
        for historical_data in historical_data_list:
            try:
                result = await self.predict_multiple_metrics(historical_data, metrics, model_config)
                results.append(result)
            except Exception as e:
                # Add error result
                results.append({'error': str(e)})
        
        return results
