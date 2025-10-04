"""Tests for integrated prediction service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from agrr_core.entity import WeatherData, Forecast, Location
from agrr_core.entity.entities.prediction_model import ModelType
from agrr_core.adapter.services.integrated_prediction_service import IntegratedPredictionService
from agrr_core.entity.exceptions.prediction_error import PredictionError


@pytest.fixture
def sample_weather_data():
    """Sample weather data for testing."""
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(100):
        date = base_date + timedelta(days=i)
        weather_data = WeatherData(
            time=date,
            temperature_2m_max=20.0 + i * 0.1,
            temperature_2m_min=10.0 + i * 0.1,
            temperature_2m_mean=15.0 + i * 0.1,
            precipitation_sum=float(i % 7),
            sunshine_duration=3600.0 + i * 10
        )
        data.append(weather_data)
    
    return data


@pytest.fixture
def integrated_service():
    """Integrated prediction service instance."""
    return IntegratedPredictionService()


@pytest.mark.asyncio
async def test_predict_multiple_metrics_prophet(integrated_service, sample_weather_data):
    """Test multi-metric prediction with Prophet model."""
    
    model_config = {
        'model_type': 'prophet',
        'prediction_days': 30,
        'seasonality': {'yearly': True, 'weekly': False, 'daily': False},
        'trend': 'linear'
    }
    
    metrics = ['temperature', 'precipitation']
    
    # Mock the Prophet service
    with patch.object(integrated_service.model_services[ModelType.PROPHET], 'predict_multiple_metrics') as mock_predict:
        mock_forecasts = {
            'temperature': [
                Forecast(date=datetime(2024, 4, 1), predicted_value=25.0, confidence_lower=23.0, confidence_upper=27.0),
                Forecast(date=datetime(2024, 4, 2), predicted_value=25.5, confidence_lower=23.5, confidence_upper=27.5)
            ],
            'precipitation': [
                Forecast(date=datetime(2024, 4, 1), predicted_value=2.0, confidence_lower=0.0, confidence_upper=4.0),
                Forecast(date=datetime(2024, 4, 2), predicted_value=1.5, confidence_lower=0.0, confidence_upper=3.0)
            ]
        }
        mock_predict.return_value = mock_forecasts
        
        result = await integrated_service.predict_multiple_metrics(
            sample_weather_data, metrics, model_config
        )
        
        assert 'temperature' in result
        assert 'precipitation' in result
        assert len(result['temperature']) == 2
        assert len(result['precipitation']) == 2
        mock_predict.assert_called_once()


@pytest.mark.asyncio
async def test_predict_multiple_metrics_lstm(integrated_service, sample_weather_data):
    """Test multi-metric prediction with LSTM model."""
    
    model_config = {
        'model_type': 'lstm',
        'prediction_days': 30,
        'epochs': 10,
        'batch_size': 32,
        'sequence_length': 30
    }
    
    metrics = ['temperature']
    
    # Mock the LSTM service
    with patch.object(integrated_service.model_services[ModelType.LSTM], 'predict_multiple_metrics') as mock_predict:
        mock_forecasts = {
            'temperature': [
                Forecast(date=datetime(2024, 4, 1), predicted_value=25.0),
                Forecast(date=datetime(2024, 4, 2), predicted_value=25.5)
            ]
        }
        mock_predict.return_value = mock_forecasts
        
        result = await integrated_service.predict_multiple_metrics(
            sample_weather_data, metrics, model_config
        )
        
        assert 'temperature' in result
        assert len(result['temperature']) == 2
        mock_predict.assert_called_once()


@pytest.mark.asyncio
async def test_predict_multiple_metrics_arima(integrated_service, sample_weather_data):
    """Test multi-metric prediction with ARIMA model."""
    
    model_config = {
        'model_type': 'arima',
        'prediction_days': 30,
        'order': (1, 1, 1),
        'seasonal_order': (1, 1, 1, 12)
    }
    
    metrics = ['temperature']
    
    # Mock the ARIMA service
    with patch.object(integrated_service.model_services[ModelType.ARIMA], 'predict_multiple_metrics') as mock_predict:
        mock_forecasts = {
            'temperature': [
                Forecast(date=datetime(2024, 4, 1), predicted_value=25.0, confidence_lower=23.0, confidence_upper=27.0),
                Forecast(date=datetime(2024, 4, 2), predicted_value=25.5, confidence_lower=23.5, confidence_upper=27.5)
            ]
        }
        mock_predict.return_value = mock_forecasts
        
        result = await integrated_service.predict_multiple_metrics(
            sample_weather_data, metrics, model_config
        )
        
        assert 'temperature' in result
        assert len(result['temperature']) == 2
        mock_predict.assert_called_once()


@pytest.mark.asyncio
async def test_unsupported_model_type(integrated_service, sample_weather_data):
    """Test error handling for unsupported model type."""
    
    model_config = {
        'model_type': 'unsupported_model',
        'prediction_days': 30
    }
    
    metrics = ['temperature']
    
    with pytest.raises(PredictionError, match="Unsupported model type"):
        await integrated_service.predict_multiple_metrics(
            sample_weather_data, metrics, model_config
        )


@pytest.mark.asyncio
async def test_insufficient_training_data(integrated_service):
    """Test error handling for insufficient training data."""
    
    # Create minimal data
    minimal_data = [
        WeatherData(
            time=datetime(2024, 1, 1),
            temperature_2m_max=20.0,
            temperature_2m_min=10.0,
            temperature_2m_mean=15.0,
            precipitation_sum=0.0,
            sunshine_duration=3600.0
        )
    ]
    
    model_config = {
        'model_type': 'lstm',
        'prediction_days': 30
    }
    
    metrics = ['temperature']
    
    with pytest.raises(PredictionError, match="Insufficient training data"):
        await integrated_service.predict_multiple_metrics(
            minimal_data, metrics, model_config
        )


@pytest.mark.asyncio
async def test_unsupported_metric(integrated_service, sample_weather_data):
    """Test error handling for unsupported metric."""
    
    model_config = {
        'model_type': 'prophet',
        'prediction_days': 30
    }
    
    metrics = ['unsupported_metric']
    
    with pytest.raises(PredictionError, match="does not support metrics"):
        await integrated_service.predict_multiple_metrics(
            sample_weather_data, metrics, model_config
        )


@pytest.mark.asyncio
async def test_get_model_info(integrated_service):
    """Test getting model information."""
    
    model_info = await integrated_service.get_model_info('prophet')
    
    assert model_info['model_type'] == 'prophet'
    assert 'name' in model_info
    assert 'description' in model_info
    assert 'supported_metrics' in model_info
    assert 'min_training_data_points' in model_info


@pytest.mark.asyncio
async def test_get_available_models(integrated_service):
    """Test getting available models."""
    
    models = await integrated_service.get_available_models()
    
    assert len(models) > 0
    model_types = [model['model_type'] for model in models]
    assert 'prophet' in model_types
    assert 'lstm' in model_types
    assert 'arima' in model_types


@pytest.mark.asyncio
async def test_batch_predict(integrated_service, sample_weather_data):
    """Test batch prediction."""
    
    model_config = {
        'model_type': 'prophet',
        'prediction_days': 7
    }
    
    metrics = ['temperature']
    
    historical_data_list = [sample_weather_data, sample_weather_data]
    
    # Mock the Prophet service
    with patch.object(integrated_service.model_services[ModelType.PROPHET], 'batch_predict') as mock_batch:
        mock_results = [
            {'temperature': [Forecast(date=datetime(2024, 4, 1), predicted_value=25.0)]},
            {'temperature': [Forecast(date=datetime(2024, 4, 1), predicted_value=26.0)]}
        ]
        mock_batch.return_value = mock_results
        
        result = await integrated_service.batch_predict(
            historical_data_list, model_config, metrics
        )
        
        assert len(result) == 2
        mock_batch.assert_called_once()


@pytest.mark.asyncio
async def test_evaluate_model_accuracy(integrated_service, sample_weather_data):
    """Test model accuracy evaluation."""
    
    test_data = sample_weather_data[-20:]  # Last 20 data points
    predictions = [
        Forecast(date=datetime(2024, 4, 1), predicted_value=25.0),
        Forecast(date=datetime(2024, 4, 2), predicted_value=25.5)
    ]
    
    # Mock the Prophet service
    with patch.object(integrated_service.model_services[ModelType.PROPHET], 'evaluate_model_accuracy') as mock_eval:
        mock_accuracy = {
            'mae': 1.5,
            'mse': 2.25,
            'rmse': 1.5,
            'mape': 5.0
        }
        mock_eval.return_value = mock_accuracy
        
        result = await integrated_service.evaluate_model_accuracy(
            test_data, predictions, 'temperature'
        )
        
        assert result['mae'] == 1.5
        assert result['mse'] == 2.25
        assert result['rmse'] == 1.5
        assert result['mape'] == 5.0
        mock_eval.assert_called_once()
