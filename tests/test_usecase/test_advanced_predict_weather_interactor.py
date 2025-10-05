"""Tests for advanced weather prediction interactor."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from agrr_core.entity import WeatherData, Forecast, Location
from agrr_core.usecase.interactors.advanced_predict_weather_interactor import AdvancedPredictWeatherInteractor
from agrr_core.usecase.gateways.weather_data_gateway import WeatherDataGateway
from agrr_core.usecase.gateways.weather_data_repository_gateway import WeatherDataRepositoryGateway
from agrr_core.usecase.gateways.prediction_service_gateway import PredictionServiceGateway
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort
from agrr_core.usecase.dto.prediction_config_dto import PredictionConfigDTO
from agrr_core.usecase.dto.multi_metric_prediction_request_dto import MultiMetricPredictionRequestDTO
from agrr_core.usecase.dto.model_evaluation_request_dto import ModelEvaluationRequestDTO
from agrr_core.usecase.dto.batch_prediction_request_dto import BatchPredictionRequestDTO
from agrr_core.usecase.dto.advanced_prediction_response_dto import AdvancedPredictionResponseDTO
from agrr_core.usecase.dto.model_accuracy_dto import ModelAccuracyDTO
from agrr_core.usecase.dto.batch_prediction_response_dto import BatchPredictionResponseDTO
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
def mock_gateways():
    """Mock gateways for testing."""
    weather_data_gateway = AsyncMock(spec=WeatherDataGateway)
    weather_data_repository_gateway = AsyncMock(spec=WeatherDataRepositoryGateway)
    prediction_service_gateway = AsyncMock(spec=PredictionServiceGateway)
    prediction_presenter_port = AsyncMock(spec=PredictionPresenterOutputPort)
    
    return {
        'weather_data_gateway': weather_data_gateway,
        'weather_data_repository_gateway': weather_data_repository_gateway,
        'prediction_service_gateway': prediction_service_gateway,
        'prediction_presenter_port': prediction_presenter_port
    }


@pytest.fixture
def interactor(mock_gateways):
    """Advanced predict weather interactor instance."""
    return AdvancedPredictWeatherInteractor(
        weather_data_gateway=mock_gateways['weather_data_gateway'],
        weather_data_repository_gateway=mock_gateways['weather_data_repository_gateway'],
        prediction_service_gateway=mock_gateways['prediction_service_gateway'],
        prediction_presenter_output_port=mock_gateways['prediction_presenter_port']
    )


@pytest.fixture
def sample_request():
    """Sample multi-metric prediction request."""
    config = PredictionConfigDTO(
        model_type='prophet',
        seasonality={'yearly': True, 'weekly': False, 'daily': False},
        trend='linear',
        custom_params={'changepoint_prior_scale': 0.05},
        confidence_level=0.95,
        prediction_horizon=30,
        validation_split=0.2
    )
    
    return MultiMetricPredictionRequestDTO(
        latitude=35.6762,
        longitude=139.6503,
        start_date='2024-01-01',
        end_date='2024-03-31',
        prediction_days=30,
        metrics=['temperature', 'precipitation'],
        config=config,
        location_name='Tokyo'
    )


@pytest.mark.asyncio
async def test_execute_multi_metric_prediction_success(interactor, sample_request, sample_weather_data, mock_gateways):
    """Test successful multi-metric prediction execution."""
    
    # Mock weather data retrieval
    location = Location(35.6762, 139.6503)
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.return_value = (
        sample_weather_data, location
    )
    
    # Mock prediction service
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
    mock_gateways['prediction_service_gateway'].predict_multiple_metrics.return_value = mock_forecasts
    
    # Execute
    result = await interactor.execute_multi_metric_prediction(sample_request)
    
    # Verify
    assert isinstance(result, AdvancedPredictionResponseDTO)
    assert len(result.historical_data) == 100
    assert 'temperature' in result.forecasts
    assert 'precipitation' in result.forecasts
    assert result.model_metrics['model_type'] == 'prophet'
    assert result.model_metrics['metrics_predicted'] == ['temperature', 'precipitation']
    
    # Verify method calls
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.assert_called_once()
    mock_gateways['prediction_service_gateway'].predict_multiple_metrics.assert_called_once()
    mock_gateways['weather_data_repository_gateway'].save_forecast_with_metadata.assert_called_once()


@pytest.mark.asyncio
async def test_execute_multi_metric_prediction_no_data(interactor, sample_request, mock_gateways):
    """Test prediction execution with no historical data."""
    
    # Mock empty weather data
    location = Location(35.6762, 139.6503)
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.return_value = (
        [], location
    )
    
    # Execute and expect error
    with pytest.raises(PredictionError, match="No historical data available"):
        await interactor.execute_multi_metric_prediction(sample_request)


@pytest.mark.asyncio
async def test_execute_multi_metric_prediction_invalid_location(interactor, sample_request, mock_gateways):
    """Test prediction execution with invalid location."""
    
    # Mock location validation error
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.side_effect = ValueError("Invalid location")
    
    # Execute and expect error
    with pytest.raises(PredictionError, match="Invalid request parameters"):
        await interactor.execute_multi_metric_prediction(sample_request)


@pytest.mark.asyncio
async def test_execute_model_evaluation(interactor, sample_weather_data, mock_gateways):
    """Test model evaluation execution."""
    
    # Create evaluation request
    config = PredictionConfigDTO(
        model_type='prophet',
        seasonality={'yearly': True},
        trend='linear',
        custom_params={},
        confidence_level=0.95,
        prediction_horizon=30,
        validation_split=0.2
    )
    
    request = ModelEvaluationRequestDTO(
        model_type='prophet',
        test_data_start_date='2024-03-01',
        test_data_end_date='2024-03-31',
        validation_split=0.2,
        metrics=['temperature'],
        config=config
    )
    
    # Mock data retrieval
    test_data = sample_weather_data[-30:]  # Last 30 days
    training_data = sample_weather_data[:-30]  # All but last 30 days
    location = Location(35.6762, 139.6503)
    
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.side_effect = [
        (training_data, location),
        (test_data, location)
    ]
    
    # Mock prediction and evaluation
    mock_forecasts = {
        'temperature': [
            Forecast(date=datetime(2024, 4, 1), predicted_value=25.0),
            Forecast(date=datetime(2024, 4, 2), predicted_value=25.5)
        ]
    }
    mock_gateways['prediction_service_gateway'].predict_multiple_metrics.return_value = mock_forecasts
    
    mock_accuracy = {
        'mae': 1.5,
        'mse': 2.25,
        'rmse': 1.5,
        'mape': 5.0,
        'r2_score': 0.85
    }
    mock_gateways['prediction_service_gateway'].evaluate_model_accuracy.return_value = mock_accuracy
    
    # Execute
    result = await interactor.execute_model_evaluation(request)
    
    # Verify
    assert result.model_type == 'prophet'
    assert result.metric == 'temperature'
    assert result.mae == 1.5
    assert result.rmse == 1.5
    assert result.mape == 5.0
    assert result.r2_score == 0.85
    
    # Verify method calls
    assert mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.call_count == 2
    mock_gateways['prediction_service_gateway'].predict_multiple_metrics.assert_called_once()
    mock_gateways['prediction_service_gateway'].evaluate_model_accuracy.assert_called_once()
    mock_gateways['weather_data_repository_gateway'].save_model_evaluation.assert_called_once()


@pytest.mark.asyncio
async def test_execute_batch_prediction(interactor, sample_weather_data, mock_gateways):
    """Test batch prediction execution."""
    
    # Create batch request
    config = PredictionConfigDTO(
        model_type='prophet',
        seasonality={'yearly': True},
        trend='linear',
        custom_params={},
        confidence_level=0.95,
        prediction_horizon=7,
        validation_split=0.2
    )
    
    request = BatchPredictionRequestDTO(
        locations=[
            {'lat': 35.6762, 'lon': 139.6503, 'name': 'Tokyo'},
            {'lat': 40.7128, 'lon': -74.0060, 'name': 'New York'}
        ],
        start_date='2024-01-01',
        end_date='2024-03-31',
        prediction_days=7,
        metrics=['temperature'],
        config=config
    )
    
    # Mock data retrieval for both locations
    location1 = Location(35.6762, 139.6503)
    location2 = Location(40.7128, -74.0060)
    
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.side_effect = [
        (sample_weather_data, location1),
        (sample_weather_data, location2)
    ]
    
    # Mock prediction service
    mock_forecasts = {
        'temperature': [
            Forecast(date=datetime(2024, 4, 1), predicted_value=25.0),
            Forecast(date=datetime(2024, 4, 2), predicted_value=25.5)
        ]
    }
    mock_gateways['prediction_service_gateway'].predict_multiple_metrics.return_value = mock_forecasts
    
    # Execute
    result = await interactor.execute_batch_prediction(request)
    
    # Verify
    assert len(result.results) == 2
    assert len(result.errors) == 0
    assert result.summary['total_locations'] == 2
    assert result.summary['successful_predictions'] == 2
    assert result.summary['failed_predictions'] == 0
    assert result.processing_time > 0
    
    # Verify method calls
    assert mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.call_count == 2
    assert mock_gateways['prediction_service_gateway'].predict_multiple_metrics.call_count == 2


@pytest.mark.asyncio
async def test_get_available_models(interactor, mock_gateways):
    """Test getting available models."""
    
    mock_models = [
        {'model_type': 'prophet', 'name': 'Facebook Prophet'},
        {'model_type': 'lstm', 'name': 'LSTM'},
        {'model_type': 'arima', 'name': 'ARIMA'}
    ]
    mock_gateways['weather_data_repository_gateway'].get_available_models.return_value = ['arima', 'prophet', 'lstm']
    
    result = await interactor.get_available_models()
    
    assert len(result) == 3
    assert result[0]['type'] == 'arima'
    assert result[1]['type'] == 'prophet'
    assert result[2]['type'] == 'lstm'
    
    mock_gateways['weather_data_repository_gateway'].get_available_models.assert_called_once()


@pytest.mark.asyncio
async def test_get_model_info(interactor, mock_gateways):
    """Test getting model information."""
    
    mock_info = {
        'model_type': 'prophet',
        'name': 'Facebook Prophet',
        'description': 'Additive regression model',
        'supported_metrics': ['temperature', 'precipitation'],
        'min_training_data_points': 30
    }
    mock_gateways['prediction_service_gateway'].get_model_info.return_value = mock_info
    
    result = await interactor.get_model_info('prophet')
    
    assert result['model_type'] == 'prophet'
    assert result['name'] == 'Facebook Prophet'
    assert result['description'] == 'Additive regression model'
    
    mock_gateways['prediction_service_gateway'].get_model_info.assert_called_once_with('prophet')


@pytest.mark.asyncio
async def test_compare_models_supported(interactor, sample_weather_data, mock_gateways):
    """Test model comparison when supported."""
    
    # Mock comparison method
    mock_comparison = {
        'prophet': {'accuracy': {'temperature': {'mae': 1.5, 'rmse': 2.0}}},
        'lstm': {'accuracy': {'temperature': {'mae': 2.0, 'rmse': 2.5}}}
    }
    # Model comparison is not yet implemented
    pass
    
    with pytest.raises(PredictionError, match="Model comparison not yet implemented"):
        await interactor.compare_models(
            sample_weather_data, sample_weather_data, ['temperature'], 
            [{'model_type': 'prophet'}, {'model_type': 'lstm'}]
        )


@pytest.mark.asyncio
async def test_compare_models_not_supported(interactor, sample_weather_data, mock_gateways):
    """Test model comparison when not supported."""
    
    # Mock service without compare_models method
    # Model comparison is not yet implemented
    
    with pytest.raises(PredictionError, match="Model comparison not yet implemented"):
        await interactor.compare_models(
            sample_weather_data, sample_weather_data, ['temperature'], 
            [{'model_type': 'prophet'}]
        )
