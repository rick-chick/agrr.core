"""Prediction mock gateway implementation for testing and development.

This gateway returns mock predictions based on last year's same period data.
Used for testing and development when real prediction services are not available.
"""

import logging
import json
import math
import random
from typing import List, Dict
from datetime import datetime, timedelta, date
from pathlib import Path

from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.prediction_forecast_entity import Forecast
from agrr_core.usecase.gateways.prediction_gateway import PredictionGateway


class PredictionMockGateway(PredictionGateway):
    """Mock prediction gateway that returns last year's same period data as predictions.
    
    This gateway is useful for:
    - Testing and development
    - When ML models are not available
    - Demonstrating functionality without external dependencies
    
    The mock predictions are generated based on last year's same period data
    with slight variations to simulate realistic forecast patterns.
    """
    
    def __init__(self, mock_data_file: str = None):
        """Initialize mock prediction gateway.
        
        Args:
            mock_data_file: Optional path to mock data file (JSON format)
                          If None, generates synthetic predictions
        """
        self.mock_data_file = mock_data_file
        self.logger = logging.getLogger(__name__)
        self._mock_data_cache = None
    
    async def read_historical_data(self, source: str) -> List[WeatherData]:
        """Read historical weather data from source file.
        
        Args:
            source: Path to historical weather data file
            
        Returns:
            List of WeatherData entities
        """
        try:
            # Read JSON file
            with open(source, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            weather_data_list = []
            
            # Parse weather data
            for item in data.get('data', []):
                weather_data = WeatherData(
                    time=datetime.fromisoformat(item['time']),
                    temperature_2m_max=item.get('temperature_2m_max'),
                    temperature_2m_min=item.get('temperature_2m_min'),
                    temperature_2m_mean=item.get('temperature_2m_mean'),
                    precipitation_sum=item.get('precipitation_sum'),
                    sunshine_duration=item.get('sunshine_duration'),
                    wind_speed_10m=item.get('wind_speed_10m'),
                    weather_code=item.get('weather_code')
                )
                weather_data_list.append(weather_data)
            
            self.logger.info(f"Read {len(weather_data_list)} historical records from {source}")
            return weather_data_list
            
        except Exception as e:
            self.logger.error(f"Failed to read historical data from {source}: {e}")
            raise
    
    async def create(self, predictions: List[Forecast], destination: str) -> None:
        """Create predictions at destination.
        
        Args:
            predictions: List of forecast entities
            destination: Output file path
        """
        try:
            # Convert predictions to JSON format
            predictions_data = []
            for forecast in predictions:
                prediction_dict = {
                    'date': forecast.date.isoformat(),
                    'predicted_value': forecast.predicted_value,
                    'confidence_lower': forecast.confidence_lower,
                    'confidence_upper': forecast.confidence_upper
                }
                predictions_data.append(prediction_dict)
            
            # Create output data structure
            output_data = {
                'predictions': predictions_data,
                'model_type': 'Mock',
                'prediction_days': len(predictions),
                'metrics': ['temperature', 'temperature_max', 'temperature_min']  # Mock supports all metrics
            }
            
            # Write to file
            Path(destination).write_text(
                json.dumps(output_data, indent=2, ensure_ascii=False)
            )
            
            self.logger.info(f"Mock predictions saved to {destination}")
            
        except Exception as e:
            self.logger.error(f"Failed to save predictions to {destination}: {e}")
            raise
    
    async def predict(
        self,
        historical_data: List[WeatherData],
        metric: str,
        config: dict
    ) -> List[Forecast]:
        """Predict weather metrics using historical data.
        
        Returns mock predictions based on last year's same period data.
        
        Args:
            historical_data: Historical weather data
            metric: Metric to predict (e.g., 'temperature')
            config: Prediction configuration including 'prediction_days'
            
        Returns:
            List of forecast entities
        """
        try:
            prediction_days = config.get('prediction_days', 30)
            
            self.logger.info(
                f"Generating mock predictions for {metric} "
                f"({prediction_days} days) based on last year's data"
            )
            
            # Generate mock predictions
            predictions = self._generate_mock_predictions(
                historical_data, metric, prediction_days
            )
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Failed to generate mock predictions: {e}")
            raise
    
    async def predict_multiple_metrics(
        self,
        historical_data: List[WeatherData],
        metrics: List[str],
        config: dict
    ) -> Dict[str, List[Forecast]]:
        """Predict multiple weather metrics using historical data.
        
        Returns mock predictions for multiple metrics.
        
        Args:
            historical_data: Historical weather data
            metrics: List of metrics to predict
            config: Prediction configuration including 'prediction_days'
            
        Returns:
            Dictionary mapping metric names to forecast lists
        """
        try:
            prediction_days = config.get('prediction_days', 30)
            
            self.logger.info(
                f"Generating mock predictions for {len(metrics)} metrics "
                f"({prediction_days} days each) based on last year's data"
            )
            
            # Generate mock predictions for each metric
            all_predictions = {}
            for metric in metrics:
                predictions = self._generate_mock_predictions(
                    historical_data, metric, prediction_days
                )
                all_predictions[metric] = predictions
            
            return all_predictions
            
        except Exception as e:
            self.logger.error(f"Failed to generate mock multi-metric predictions: {e}")
            raise
    
    def _generate_mock_predictions(
        self,
        historical_data: List[WeatherData],
        metric: str,
        prediction_days: int
    ) -> List[Forecast]:
        """Generate mock predictions based on historical data.
        
        Args:
            historical_data: Historical weather data
            metric: Metric to predict
            prediction_days: Number of days to predict
            
        Returns:
            List of forecast entities
        """
        import random
        
        predictions = []
        start_date = datetime.now().date() + timedelta(days=1)
        
        for i in range(prediction_days):
            prediction_date = start_date + timedelta(days=i)
            
            # Get corresponding date last year
            last_year_date = prediction_date.replace(year=prediction_date.year - 1)
            
            # Find historical data for the same period last year
            historical_value = self._find_historical_value(
                historical_data, last_year_date, metric
            )
            
            # Add some variation to simulate forecast uncertainty
            if historical_value is not None:
                base_value = historical_value
                variation = random.uniform(-2.0, 2.0)  # ±2°C variation
                predicted_value = base_value + variation
                
                # Generate confidence intervals
                confidence_range = random.uniform(1.5, 3.0)  # 1.5-3°C range
                confidence_lower = predicted_value - confidence_range
                confidence_upper = predicted_value + confidence_range
            else:
                # Fallback to seasonal average if no historical data
                predicted_value = self._get_seasonal_average(prediction_date, metric)
                confidence_lower = predicted_value - 2.0
                confidence_upper = predicted_value + 2.0
            
            # Create forecast entity
            forecast = Forecast(
                date=prediction_date,
                predicted_value=round(predicted_value, 1),
                confidence_lower=round(confidence_lower, 1),
                confidence_upper=round(confidence_upper, 1)
            )
            
            predictions.append(forecast)
        
        return predictions
    
    def _find_historical_value(
        self,
        historical_data: List[WeatherData],
        target_date: date,
        metric: str
    ) -> float:
        """Find historical value for a specific date and metric.
        
        Args:
            historical_data: Historical weather data
            target_date: Target date
            metric: Metric name
            
        Returns:
            Historical value or None if not found
        """
        for data in historical_data:
            if data.time.date() == target_date:
                if metric == 'temperature':
                    return data.temperature_2m_mean
                elif metric == 'temperature_max':
                    return data.temperature_2m_max
                elif metric == 'temperature_min':
                    return data.temperature_2m_min
                # Add more metrics as needed
        
        return None
    
    def _get_seasonal_average(self, date: date, metric: str) -> float:
        """Get seasonal average for a metric.
        
        Args:
            date: Target date
            metric: Metric name
            
        Returns:
            Seasonal average value
        """
        # Simple seasonal model
        day_of_year = date.timetuple().tm_yday
        
        if metric in ['temperature', 'temperature_max', 'temperature_min']:
            # Temperature seasonal variation
            base_temp = 20 + 10 * math.cos(2 * math.pi * (day_of_year - 200) / 365)
            
            if metric == 'temperature_max':
                return base_temp + 5.0  # Max is typically 5°C higher
            elif metric == 'temperature_min':
                return base_temp - 5.0  # Min is typically 5°C lower
            else:
                return base_temp
        else:
            # Default fallback
            return 20.0
