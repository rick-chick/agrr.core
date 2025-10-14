"""Tests for LightGBM prediction service."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys

from agrr_core.entity import WeatherData, Forecast
from agrr_core.entity.exceptions.prediction_error import PredictionError


# Mock LightGBM if not available
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    # Create mock for testing
    sys.modules['lightgbm'] = Mock()


from agrr_core.adapter.services.prediction_lightgbm_service import PredictionLightGBMService


def create_sample_weather_data(days: int = 100, start_date: datetime = None) -> list:
    """Create sample weather data for testing."""
    if start_date is None:
        start_date = datetime(2024, 1, 1)
    
    data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        # Simulate seasonal temperature pattern
        day_of_year = date.timetuple().tm_yday
        temp_mean = 10 + 10 * (1 - abs(day_of_year - 182.5) / 182.5)  # Peak in summer
        
        weather = WeatherData(
            time=date,
            temperature_2m_max=temp_mean + 5,
            temperature_2m_min=temp_mean - 5,
            temperature_2m_mean=temp_mean,
            precipitation_sum=2.0,
            sunshine_duration=10000.0
        )
        data.append(weather)
    
    return data


@pytest.mark.skipif(not LIGHTGBM_AVAILABLE, reason="LightGBM not installed")
class TestPredictionLightGBMService:
    """Test LightGBM prediction service."""
    
    @pytest.mark.asyncio
    async def test_init_without_lightgbm(self):
        """Test initialization when LightGBM is not available."""
        with patch('agrr_core.adapter.services.prediction_lightgbm_service.LIGHTGBM_AVAILABLE', False):
            with pytest.raises(ImportError, match="LightGBM is not installed"):
                service = PredictionLightGBMService()
    
    @pytest.mark.asyncio
    async def test_init_with_default_params(self):
        """Test initialization with default parameters."""
        service = PredictionLightGBMService()
        
        assert service.model_params is not None
        assert service.model_params['objective'] == 'regression'
        assert service.model_params['metric'] == 'rmse'
    
    @pytest.mark.asyncio
    async def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        custom_params = {
            'objective': 'regression',
            'learning_rate': 0.05,
            'num_leaves': 50,
        }
        service = PredictionLightGBMService(model_params=custom_params)
        
        assert service.model_params['learning_rate'] == 0.05
        assert service.model_params['num_leaves'] == 50
    
    @pytest.mark.asyncio
    async def test_predict_single_metric_temperature(self):
        """Test temperature prediction."""
        service = PredictionLightGBMService()
        historical_data = create_sample_weather_data(days=100)
        
        model_config = {
            'prediction_days': 7,
            'lookback_days': [1, 7],
            'lgb_params': {
                'n_estimators': 100,  # Reduce for faster testing
            }
        }
        
        forecasts = await service._predict_single_metric(
            historical_data, 'temperature', model_config
        )
        
        assert len(forecasts) == 7
        assert all(isinstance(f, Forecast) for f in forecasts)
        assert all(f.predicted_value is not None for f in forecasts)
        assert all(f.confidence_lower is not None for f in forecasts)
        assert all(f.confidence_upper is not None for f in forecasts)
    
    @pytest.mark.asyncio
    async def test_predict_insufficient_data(self):
        """Test prediction with insufficient data."""
        service = PredictionLightGBMService()
        historical_data = create_sample_weather_data(days=50)  # Too few
        
        model_config = {'prediction_days': 7}
        
        with pytest.raises(PredictionError, match="Insufficient data"):
            await service._predict_single_metric(
                historical_data, 'temperature', model_config
            )
    
    @pytest.mark.asyncio
    async def test_predict_multiple_metrics(self):
        """Test prediction for multiple metrics."""
        service = PredictionLightGBMService()
        historical_data = create_sample_weather_data(days=100)
        
        model_config = {
            'prediction_days': 7,
            'lgb_params': {
                'n_estimators': 100,
            }
        }
        
        results = await service.predict_multiple_metrics(
            historical_data,
            ['temperature', 'precipitation'],
            model_config
        )
        
        assert 'temperature' in results
        assert 'precipitation' in results
        assert len(results['temperature']) == 7
        assert len(results['precipitation']) == 7
    
    @pytest.mark.asyncio
    async def test_evaluate_model_accuracy(self):
        """Test model accuracy evaluation."""
        service = PredictionLightGBMService()
        
        # Create test data
        test_data = create_sample_weather_data(days=7, start_date=datetime(2024, 4, 1))
        
        # Create predictions (with small error)
        predictions = []
        for weather in test_data:
            pred = Forecast(
                date=weather.time,
                predicted_value=weather.temperature_2m_mean + 0.5,  # Add small error
                confidence_lower=weather.temperature_2m_mean - 1,
                confidence_upper=weather.temperature_2m_mean + 2
            )
            predictions.append(pred)
        
        metrics = await service.evaluate_model_accuracy(
            test_data, predictions, 'temperature'
        )
        
        assert 'mae' in metrics
        assert 'rmse' in metrics
        assert 'mape' in metrics
        assert 'r2' in metrics
        assert metrics['mae'] > 0
        assert metrics['rmse'] > 0
    
    @pytest.mark.asyncio
    async def test_train_model(self):
        """Test model training."""
        service = PredictionLightGBMService()
        training_data = create_sample_weather_data(days=100)
        
        model_config = {'prediction_days': 30}
        
        result = await service.train_model(
            training_data, model_config, 'temperature'
        )
        
        assert result['model_type'] == 'lightgbm'
        assert result['metric'] == 'temperature'
        assert result['training_samples'] == 100
        assert result['status'] == 'trained'
    
    @pytest.mark.asyncio
    async def test_get_model_info(self):
        """Test getting model information."""
        service = PredictionLightGBMService()
        
        info = await service.get_model_info('lightgbm')
        
        assert info['model_type'] == 'lightgbm'
        assert info['description'] == 'Light Gradient Boosting Machine'
        assert info['supports_confidence_intervals'] is True
        assert info['min_training_samples'] == 90
        assert 'recommended_params' in info
    
    @pytest.mark.asyncio
    async def test_predict_with_confidence_intervals(self):
        """Test prediction with confidence intervals."""
        service = PredictionLightGBMService()
        historical_data = create_sample_weather_data(days=100)
        
        model_config = {
            'lgb_params': {
                'n_estimators': 100,
            }
        }
        
        forecasts = await service.predict_with_confidence_intervals(
            historical_data,
            prediction_days=7,
            confidence_level=0.95,
            model_config=model_config
        )
        
        assert len(forecasts) == 7
        assert all(f.confidence_lower < f.predicted_value < f.confidence_upper for f in forecasts)
    
    @pytest.mark.asyncio
    async def test_batch_predict(self):
        """Test batch prediction."""
        service = PredictionLightGBMService()
        
        # Create multiple historical datasets
        historical_data_list = [
            create_sample_weather_data(days=100, start_date=datetime(2024, 1, 1)),
            create_sample_weather_data(days=100, start_date=datetime(2024, 7, 1)),
        ]
        
        model_config = {
            'prediction_days': 7,
            'lgb_params': {
                'n_estimators': 100,
            }
        }
        
        results = await service.batch_predict(
            historical_data_list,
            model_config,
            ['temperature']
        )
        
        assert len(results) == 2
        assert 'temperature' in results[0]
        assert 'temperature' in results[1]
        assert len(results[0]['temperature']) == 7
        assert len(results[1]['temperature']) == 7
    
    @pytest.mark.asyncio
    async def test_confidence_intervals_width(self):
        """Test that confidence intervals have reasonable width."""
        service = PredictionLightGBMService()
        historical_data = create_sample_weather_data(days=100)
        
        model_config = {
            'prediction_days': 7,
            'calculate_confidence_intervals': True,
            'lgb_params': {
                'n_estimators': 100,
            }
        }
        
        forecasts = await service._predict_single_metric(
            historical_data, 'temperature', model_config
        )
        
        # Check that intervals widen for longer-term predictions (generally)
        widths = [f.confidence_upper - f.confidence_lower for f in forecasts]
        
        assert all(w > 0 for w in widths), "All intervals should have positive width"
        # Average width should be reasonable (not too narrow or too wide)
        avg_width = sum(widths) / len(widths)
        assert 1 < avg_width < 20, f"Average interval width {avg_width} seems unreasonable"
    
    @pytest.mark.asyncio
    async def test_predictions_follow_seasonal_pattern(self):
        """Test that predictions capture seasonal patterns."""
        service = PredictionLightGBMService()
        
        # Create data with strong seasonal pattern
        historical_data = create_sample_weather_data(days=365)
        
        model_config = {
            'prediction_days': 30,
            'lgb_params': {
                'n_estimators': 200,
            }
        }
        
        forecasts = await service._predict_single_metric(
            historical_data, 'temperature', model_config
        )
        
        # Check that predictions are in reasonable range
        predictions = [f.predicted_value for f in forecasts]
        assert min(predictions) > -10, "Predictions should not be extremely cold"
        assert max(predictions) < 40, "Predictions should not be extremely hot"
        
        # Check that predictions vary (not constant)
        assert max(predictions) - min(predictions) > 1, "Predictions should show variation"


# Tests for FeatureEngineeringService

from agrr_core.adapter.services.feature_engineering_service import FeatureEngineeringService


class TestFeatureEngineeringService:
    """Test feature engineering service."""
    
    def test_create_features(self):
        """Test feature creation from historical data."""
        historical_data = create_sample_weather_data(days=100)
        
        features_df = FeatureEngineeringService.create_features(
            historical_data, 'temperature', lookback_days=[1, 7]
        )
        
        assert len(features_df) == 100
        assert 'temperature' in features_df.columns
        assert 'month' in features_df.columns
        assert 'day_of_year' in features_df.columns
        assert 'temperature_lag1' in features_df.columns
        assert 'temperature_lag7' in features_df.columns
        assert 'temperature_ma7' in features_df.columns
        assert 'temperature_std7' in features_df.columns
    
    def test_create_future_features(self):
        """Test future feature creation."""
        historical_data = create_sample_weather_data(days=100)
        
        future_df = FeatureEngineeringService.create_future_features(
            historical_data, 'temperature', prediction_days=7, lookback_days=[1, 7]
        )
        
        assert len(future_df) == 7
        assert 'month' in future_df.columns
        assert 'day_of_year' in future_df.columns
        assert 'temperature_lag1' in future_df.columns
        assert 'temperature_lag7' in future_df.columns
    
    def test_cyclical_encoding(self):
        """Test cyclical encoding of temporal features."""
        historical_data = create_sample_weather_data(days=365)
        
        features_df = FeatureEngineeringService.create_features(
            historical_data, 'temperature'
        )
        
        # Check that cyclical encoding exists
        assert 'month_sin' in features_df.columns
        assert 'month_cos' in features_df.columns
        assert 'day_of_year_sin' in features_df.columns
        assert 'day_of_year_cos' in features_df.columns
        
        # Check that values are in [-1, 1] range
        assert features_df['month_sin'].min() >= -1
        assert features_df['month_sin'].max() <= 1
        assert features_df['month_cos'].min() >= -1
        assert features_df['month_cos'].max() <= 1
    
    def test_season_flags(self):
        """Test season flag creation."""
        historical_data = create_sample_weather_data(days=365)
        
        features_df = FeatureEngineeringService.create_features(
            historical_data, 'temperature'
        )
        
        assert 'is_winter' in features_df.columns
        assert 'is_spring' in features_df.columns
        assert 'is_summer' in features_df.columns
        assert 'is_autumn' in features_df.columns
        
        # Each day should belong to exactly one season
        season_sum = (features_df['is_winter'] + features_df['is_spring'] + 
                      features_df['is_summer'] + features_df['is_autumn'])
        assert all(season_sum == 1)
    
    def test_get_feature_names(self):
        """Test getting feature names."""
        feature_names = FeatureEngineeringService.get_feature_names(
            'temperature', lookback_days=[1, 7]
        )
        
        assert 'month' in feature_names
        assert 'temperature_lag1' in feature_names
        assert 'temperature_lag7' in feature_names
        assert 'temperature_ma7' in feature_names
        assert 'temperature_diff1' in feature_names
        assert 'temperature_ema7' in feature_names

