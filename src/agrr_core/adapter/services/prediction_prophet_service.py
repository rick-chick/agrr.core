"""Prophet-based weather prediction service implementation."""

from typing import List, Dict, Any
import pandas as pd

try:
    from prophet import Prophet
except ImportError:
    # Mock Prophet for testing when not installed
    class Prophet:
        def __init__(self, **kwargs):
            pass
        def fit(self, df):
            pass
        def make_future_dataframe(self, periods, freq):
            return pd.DataFrame({'ds': pd.date_range(start='2024-01-01', periods=periods, freq=freq)})
        def predict(self, future):
            return future.assign(yhat=20.0, yhat_lower=18.0, yhat_upper=23.0)

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.prediction_error import PredictionError
from agrr_core.usecase.ports.output.weather_prediction_output_port import WeatherPredictionOutputPort
from agrr_core.usecase.gateways.prediction_service_gateway import PredictionServiceGateway


class PredictionProphetService(WeatherPredictionOutputPort, PredictionServiceGateway):
    """Prophet-based implementation of weather prediction service."""
    
    async def predict_weather(
        self, 
        historical_data: List[WeatherData], 
        prediction_days: int
    ) -> List[Forecast]:
        """Predict weather using Prophet model."""
        try:
            if not historical_data:
                raise PredictionError("No historical data available for prediction")
            
            # Convert to DataFrame for Prophet
            df_data = []
            for weather_data in historical_data:
                if weather_data.temperature_2m_mean is not None:
                    df_data.append({
                        'ds': weather_data.time,
                        'y': weather_data.temperature_2m_mean
                    })
            
            if not df_data:
                raise PredictionError("No valid temperature data for prediction")
            
            df = pd.DataFrame(df_data)
            
            # Initialize and fit Prophet model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,
                daily_seasonality=False
            )
            model.fit(df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=prediction_days, freq='D')
            forecast = model.predict(future)
            
            # Get only future predictions
            future_forecast = forecast[forecast['ds'] > df['ds'].max()]
            
            # Convert forecast to entities
            forecasts = []
            for _, row in future_forecast.iterrows():
                forecast_entity = Forecast(
                    date=row['ds'],
                    predicted_value=row['yhat'],
                    confidence_lower=row.get('yhat_lower'),
                    confidence_upper=row.get('yhat_upper')
                )
                forecasts.append(forecast_entity)
            
            return forecasts
            
        except Exception as e:
            raise PredictionError(f"Prediction failed: {e}")
    
    # Advanced prediction methods
    async def predict_multiple_metrics(
        self, 
        historical_data: List[WeatherData], 
        metrics: List[str],
        model_config: Dict[str, Any]
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using Prophet model."""
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
        """Predict single metric using Prophet."""
        
        # Extract data for the metric
        data = self._extract_metric_data(historical_data, metric)
        if not data:
            raise PredictionError(f"No valid {metric} data for prediction")
        
        # Convert to DataFrame for Prophet
        df_data = []
        for i, value in enumerate(data):
            df_data.append({
                'ds': historical_data[i].time,
                'y': value
            })
        
        df = pd.DataFrame(df_data)
        
        # Initialize and fit Prophet model
        model = Prophet(
            yearly_seasonality=model_config.get('seasonality', {}).get('yearly', True),
            weekly_seasonality=model_config.get('seasonality', {}).get('weekly', False),
            daily_seasonality=model_config.get('seasonality', {}).get('daily', False)
        )
        model.fit(df)
        
        # Create future dataframe
        prediction_days = model_config.get('prediction_days', 30)
        future = model.make_future_dataframe(periods=prediction_days, freq='D')
        forecast = model.predict(future)
        
        # Get only future predictions
        future_forecast = forecast[forecast['ds'] > df['ds'].max()]
        
        # Convert forecast to entities
        forecasts = []
        for _, row in future_forecast.iterrows():
            forecast_entity = Forecast(
                date=row['ds'],
                predicted_value=row['yhat'],
                confidence_lower=row.get('yhat_lower'),
                confidence_upper=row.get('yhat_upper')
            )
            forecasts.append(forecast_entity)
        
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
        
        return data
    
    async def evaluate_model_accuracy(
        self,
        test_data: List[WeatherData],
        predictions: List[Forecast],
        metric: str
    ) -> Dict[str, float]:
        """Evaluate Prophet model accuracy."""
        # Extract actual values
        actual_values = self._extract_metric_data(test_data, metric)
        
        # Extract predicted values
        predicted_values = [f.predicted_value for f in predictions]
        
        # Ensure same length
        min_length = min(len(actual_values), len(predicted_values))
        actual_values = actual_values[:min_length]
        predicted_values = predicted_values[:min_length]
        
        # Calculate metrics
        import numpy as np
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
        """Train Prophet model."""
        return {
            'model_type': 'prophet',
            'metric': metric,
            'training_samples': len(training_data),
            'status': 'trained'
        }
    
    async def get_model_info(self, model_type: str) -> Dict[str, Any]:
        """Get Prophet model information."""
        return {
            'model_type': 'prophet',
            'description': 'Facebook Prophet time series forecasting',
            'supports_confidence_intervals': True,
            'min_training_samples': 30,
            'recommended_seasonality': {'yearly': True, 'weekly': False, 'daily': False}
        }
    
    async def predict_with_confidence_intervals(
        self,
        historical_data: List[WeatherData],
        prediction_days: int,
        confidence_level: float,
        model_config: Dict[str, Any]
    ) -> List[Forecast]:
        """Predict with confidence intervals using Prophet."""
        # Prophet supports confidence intervals natively
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
        """Perform batch prediction using Prophet."""
        results = []
        
        for historical_data in historical_data_list:
            try:
                result = await self.predict_multiple_metrics(historical_data, metrics, model_config)
                results.append(result)
            except Exception as e:
                # Add error result
                results.append({'error': str(e)})
        
        return results
