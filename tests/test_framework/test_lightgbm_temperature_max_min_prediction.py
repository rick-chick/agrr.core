"""Tests for LightGBM temperature_max and temperature_min prediction."""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch

from agrr_core.framework.services.ml.lightgbm_prediction_service import (
    LightGBMPredictionService,
    LIGHTGBM_AVAILABLE
)
from agrr_core.framework.services.ml.feature_engineering_service import FeatureEngineeringService
from agrr_core.entity import WeatherData, Forecast


@pytest.mark.skipif(not LIGHTGBM_AVAILABLE, reason="LightGBM not installed")
class TestLightGBMTemperatureMaxMinPrediction:
    """Test cases for LightGBM temperature_max and temperature_min prediction."""
    
    @pytest.fixture
    def sample_weather_data(self):
        """Create sample weather data with realistic temperature patterns."""
        data = []
        base_date = datetime(2023, 1, 1)
        
        # Create 120 days of data (minimum 90 required for LightGBM)
        for i in range(120):
            date = base_date + timedelta(days=i)
            
            # Seasonal pattern with noise
            seasonal_factor = np.sin(2 * np.pi * i / 365)
            noise = np.random.normal(0, 0.5)
            
            # Base temperatures with seasonal variation
            base_temp = 15.0 + 10.0 * seasonal_factor
            temp_max = base_temp + 5.0 + noise
            temp_min = base_temp - 5.0 + noise
            temp_mean = (temp_max + temp_min) / 2
            
            weather_data = WeatherData(
                time=date,
                temperature_2m_max=float(temp_max),
                temperature_2m_min=float(temp_min),
                temperature_2m_mean=float(temp_mean),
                precipitation_sum=float(np.random.uniform(0, 10)),
                sunshine_duration=float(np.random.uniform(0, 43200))
            )
            data.append(weather_data)
        
        return data
    
    @pytest.fixture
    def lightgbm_service(self):
        """Create LightGBM prediction service."""
        model_params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'n_estimators': 100,  # Reduced for faster testing
            'early_stopping_rounds': 10,
        }
        return LightGBMPredictionService(model_params=model_params)
    
    @pytest.mark.asyncio
    async def test_predict_temperature_max(self, lightgbm_service, sample_weather_data):
        """Test temperature_max prediction with LightGBM."""
        metric = 'temperature_max'
        prediction_days = 7
        model_config = {
            'prediction_days': prediction_days,
            'lookback_days': [1, 7, 14],
            'calculate_confidence_intervals': True
        }
        
        # Execute prediction
        forecasts = await lightgbm_service.predict(
            historical_data=sample_weather_data,
            metric=metric,
            prediction_days=prediction_days,
            model_config=model_config
        )
        
        # Assertions
        assert len(forecasts) == prediction_days
        assert all(isinstance(f, Forecast) for f in forecasts)
        
        # Check that predicted values are reasonable (within range)
        predicted_values = [f.predicted_value for f in forecasts]
        assert all(5.0 <= v <= 35.0 for v in predicted_values), "Predicted temp_max should be realistic"
        
        # Check confidence intervals exist
        assert all(f.confidence_lower is not None for f in forecasts)
        assert all(f.confidence_upper is not None for f in forecasts)
        assert all(f.confidence_lower < f.predicted_value < f.confidence_upper for f in forecasts)
    
    @pytest.mark.asyncio
    async def test_predict_temperature_min(self, lightgbm_service, sample_weather_data):
        """Test temperature_min prediction with LightGBM."""
        metric = 'temperature_min'
        prediction_days = 7
        model_config = {
            'prediction_days': prediction_days,
            'lookback_days': [1, 7, 14],
            'calculate_confidence_intervals': True
        }
        
        # Execute prediction
        forecasts = await lightgbm_service.predict(
            historical_data=sample_weather_data,
            metric=metric,
            prediction_days=prediction_days,
            model_config=model_config
        )
        
        # Assertions
        assert len(forecasts) == prediction_days
        assert all(isinstance(f, Forecast) for f in forecasts)
        
        # Check that predicted values are reasonable (within range)
        predicted_values = [f.predicted_value for f in forecasts]
        assert all(0.0 <= v <= 25.0 for v in predicted_values), "Predicted temp_min should be realistic"
        
        # Check confidence intervals exist
        assert all(f.confidence_lower is not None for f in forecasts)
        assert all(f.confidence_upper is not None for f in forecasts)
        assert all(f.confidence_lower < f.predicted_value < f.confidence_upper for f in forecasts)
    
    @pytest.mark.asyncio
    async def test_predict_multiple_metrics_with_max_min(self, lightgbm_service, sample_weather_data):
        """Test predicting temperature, temperature_max, temperature_min together."""
        metrics = ['temperature', 'temperature_max', 'temperature_min']
        prediction_days = 7
        model_config = {
            'prediction_days': prediction_days,
            'lookback_days': [1, 7, 14],
        }
        
        # Execute multi-metric prediction
        results = await lightgbm_service.predict_multiple_metrics(
            historical_data=sample_weather_data,
            metrics=metrics,
            model_config=model_config
        )
        
        # Assertions
        assert len(results) == 3
        assert 'temperature' in results
        assert 'temperature_max' in results
        assert 'temperature_min' in results
        
        # Check each metric's predictions
        for metric, forecasts in results.items():
            assert len(forecasts) == prediction_days
            assert all(isinstance(f, Forecast) for f in forecasts)
        
        # Verify logical relationship: temp_min < temp_mean < temp_max
        for i in range(prediction_days):
            temp_mean = results['temperature'][i].predicted_value
            temp_max = results['temperature_max'][i].predicted_value
            temp_min = results['temperature_min'][i].predicted_value
            
            assert temp_min < temp_mean < temp_max, \
                f"Day {i}: temp_min ({temp_min}) < temp_mean ({temp_mean}) < temp_max ({temp_max}) should hold"
    
    @pytest.mark.asyncio
    async def test_evaluate_temperature_max_accuracy(self, lightgbm_service, sample_weather_data):
        """Test evaluating temperature_max prediction accuracy."""
        metric = 'temperature_max'
        
        # Split data into train and test
        train_data = sample_weather_data[:100]
        test_data = sample_weather_data[100:107]  # 7 days for testing
        
        # Generate predictions
        model_config = {
            'prediction_days': 7,
            'lookback_days': [1, 7, 14],
        }
        
        # Use train data to predict
        forecasts = await lightgbm_service.predict(
            historical_data=train_data,
            metric=metric,
            prediction_days=7,
            model_config=model_config
        )
        
        # Evaluate accuracy
        accuracy_metrics = await lightgbm_service.evaluate_model_accuracy(
            test_data=test_data,
            predictions=forecasts,
            metric=metric
        )
        
        # Assertions
        assert 'mae' in accuracy_metrics
        assert 'rmse' in accuracy_metrics
        assert 'mse' in accuracy_metrics
        assert 'mape' in accuracy_metrics
        assert 'r2' in accuracy_metrics
        
        # Check that metrics are reasonable
        assert 0 <= accuracy_metrics['mae'] < 20, "MAE should be reasonable for temperature"
        assert 0 <= accuracy_metrics['rmse'] < 20, "RMSE should be reasonable for temperature"
        assert accuracy_metrics['mse'] >= 0, "MSE should be non-negative"
    
    @pytest.mark.asyncio
    async def test_evaluate_temperature_min_accuracy(self, lightgbm_service, sample_weather_data):
        """Test evaluating temperature_min prediction accuracy."""
        metric = 'temperature_min'
        
        # Split data into train and test
        train_data = sample_weather_data[:100]
        test_data = sample_weather_data[100:107]  # 7 days for testing
        
        # Generate predictions
        model_config = {
            'prediction_days': 7,
            'lookback_days': [1, 7, 14],
        }
        
        forecasts = await lightgbm_service.predict(
            historical_data=train_data,
            metric=metric,
            prediction_days=7,
            model_config=model_config
        )
        
        # Evaluate accuracy
        accuracy_metrics = await lightgbm_service.evaluate_model_accuracy(
            test_data=test_data,
            predictions=forecasts,
            metric=metric
        )
        
        # Assertions
        assert 'mae' in accuracy_metrics
        assert 'rmse' in accuracy_metrics
        assert 'r2' in accuracy_metrics
        
        # Check that metrics are reasonable
        assert 0 <= accuracy_metrics['mae'] < 20, "MAE should be reasonable for temperature"
        assert 0 <= accuracy_metrics['rmse'] < 20, "RMSE should be reasonable for temperature"
    
    def test_get_target_column_temperature_max(self):
        """Test that _get_target_column returns correct column for temperature_max."""
        service = FeatureEngineeringService()
        
        target_col = service._get_target_column('temperature_max')
        
        assert target_col == 'temp_max'
    
    def test_get_target_column_temperature_min(self):
        """Test that _get_target_column returns correct column for temperature_min."""
        service = FeatureEngineeringService()
        
        target_col = service._get_target_column('temperature_min')
        
        assert target_col == 'temp_min'
    
    @pytest.mark.asyncio
    async def test_temperature_max_features_are_used(self, lightgbm_service, sample_weather_data):
        """Test that temp_max lag features are properly utilized in prediction."""
        metric = 'temperature_max'
        prediction_days = 7
        model_config = {
            'prediction_days': prediction_days,
            'lookback_days': [1, 7, 14, 30],
        }
        
        # Execute prediction
        forecasts = await lightgbm_service.predict(
            historical_data=sample_weather_data,
            metric=metric,
            prediction_days=prediction_days,
            model_config=model_config
        )
        
        # Check that model was trained with temp_max features
        feature_importance = lightgbm_service.get_feature_importance()
        assert feature_importance is not None, "Feature importance should be available"
        
        # Check that temp_max lag features are present
        temp_max_features = [f for f in feature_importance.keys() if 'temp_max' in f]
        assert len(temp_max_features) > 0, "temp_max features should be used in the model"
    
    @pytest.mark.asyncio
    async def test_temperature_min_features_are_used(self, lightgbm_service, sample_weather_data):
        """Test that temp_min lag features are properly utilized in prediction."""
        metric = 'temperature_min'
        prediction_days = 7
        model_config = {
            'prediction_days': prediction_days,
            'lookback_days': [1, 7, 14, 30],
        }
        
        # Execute prediction
        forecasts = await lightgbm_service.predict(
            historical_data=sample_weather_data,
            metric=metric,
            prediction_days=prediction_days,
            model_config=model_config
        )
        
        # Check that model was trained with temp_min features
        feature_importance = lightgbm_service.get_feature_importance()
        assert feature_importance is not None, "Feature importance should be available"
        
        # Check that temp_min lag features are present
        temp_min_features = [f for f in feature_importance.keys() if 'temp_min' in f]
        assert len(temp_min_features) > 0, "temp_min features should be used in the model"
    
    @pytest.mark.asyncio
    async def test_insufficient_data_for_lightgbm(self, lightgbm_service):
        """Test that LightGBM raises error with insufficient data."""
        # Create only 50 days of data (less than minimum 90)
        insufficient_data = []
        base_date = datetime(2023, 1, 1)
        
        for i in range(50):
            date = base_date + timedelta(days=i)
            weather_data = WeatherData(
                time=date,
                temperature_2m_max=20.0,
                temperature_2m_min=10.0,
                temperature_2m_mean=15.0,
                precipitation_sum=0.0,
                sunshine_duration=28800.0
            )
            insufficient_data.append(weather_data)
        
        model_config = {'prediction_days': 7}
        
        # Should raise PredictionError
        with pytest.raises(Exception) as exc_info:
            await lightgbm_service.predict(
                historical_data=insufficient_data,
                metric='temperature_max',
                prediction_days=7,
                model_config=model_config
            )
        
        assert "Insufficient data" in str(exc_info.value)

