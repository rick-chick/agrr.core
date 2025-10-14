"""Tests for model evaluation interactor."""

import pytest
from unittest.mock import AsyncMock
from datetime import datetime, timedelta

from agrr_core.entity import WeatherData, Forecast, Location
from agrr_core.usecase.interactors.prediction_evaluate_interactor import ModelEvaluationInteractor
from agrr_core.usecase.gateways.weather_data_gateway import WeatherDataGateway
from agrr_core.usecase.gateways.model_config_gateway import ModelConfigGateway
from agrr_core.usecase.gateways.prediction_model_gateway import PredictionModelGateway
from agrr_core.usecase.dto.prediction_config_dto import PredictionConfigDTO
from agrr_core.usecase.dto.model_evaluation_request_dto import ModelEvaluationRequestDTO
from agrr_core.entity.exceptions.prediction_error import PredictionError


@pytest.fixture
def sample_test_data():
    """Sample test data for evaluation."""
    data = []
    base_date = datetime(2024, 2, 1)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        weather_data = WeatherData(
            time=date,
            temperature_2m_max=25.0 + i * 0.1,
            temperature_2m_min=15.0 + i * 0.1,
            temperature_2m_mean=20.0 + i * 0.1,
            precipitation_sum=float(i % 5),
            sunshine_duration=3600.0 + i * 20
        )
        data.append(weather_data)
    
    return data


@pytest.fixture
def sample_training_data():
    """Sample training data for evaluation."""
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(31):
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
    model_config_gateway = AsyncMock(spec=ModelConfigGateway)
    prediction_model_gateway = AsyncMock(spec=PredictionModelGateway)
    
    return {
        'weather_data_gateway': weather_data_gateway,
        'model_config_gateway': model_config_gateway,
        'prediction_model_gateway': prediction_model_gateway
    }


@pytest.fixture
def interactor(mock_gateways):
    """Create interactor with mocked dependencies."""
    return ModelEvaluationInteractor(
        weather_data_gateway=mock_gateways['weather_data_gateway'],
        model_config_gateway=mock_gateways['model_config_gateway'],
        prediction_model_gateway=mock_gateways['prediction_model_gateway']
    )


@pytest.fixture
def sample_request():
    """Sample evaluation request."""
    config = PredictionConfigDTO(
        model_type='Prophet',
        seasonality=True,
        trend=True,
        custom_params={},
        confidence_level=0.95,
        validation_split=0.2
    )
    
    return ModelEvaluationRequestDTO(
        model_type='Prophet',
        metrics=['temperature'],
        test_data_start_date='2024-02-01',
        test_data_end_date='2024-03-01',
        config=config,
        validation_split=0.2
    )


@pytest.mark.asyncio
async def test_execute_success(interactor, sample_request, sample_test_data, sample_training_data, mock_gateways):
    """Test successful model evaluation execution."""
    # Setup mocks
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.side_effect = [
        (sample_test_data, Location(0.0, 0.0)),
        (sample_training_data, Location(0.0, 0.0))
    ]
    
    # Mock forecasts
    forecasts = {
        'temperature': [
            Forecast(date=datetime(2024, 2, 1), predicted_value=25.0, confidence_lower=23.0, confidence_upper=27.0),
            Forecast(date=datetime(2024, 2, 2), predicted_value=26.0, confidence_lower=24.0, confidence_upper=28.0)
        ]
    }
    
    mock_gateways['prediction_model_gateway'].predict_multiple_metrics.return_value = forecasts
    
    # Mock accuracy results
    accuracy_results = {
        'mae': 1.5,
        'mse': 2.25,
        'rmse': 1.5,
        'mape': 5.0,
        'r2_score': 0.85
    }
    
    mock_gateways['prediction_model_gateway'].evaluate_model_accuracy.return_value = accuracy_results
    mock_gateways['model_config_gateway'].save_model_evaluation.return_value = None
    
    # Execute
    result = await interactor.execute(sample_request)
    
    # Assertions
    assert result is not None
    assert result.model_type == 'Prophet'
    assert result.metric == 'temperature'
    assert result.mae == 1.5
    assert result.mse == 2.25
    assert result.rmse == 1.5
    assert result.mape == 5.0
    assert result.r2_score == 0.85
    assert result.test_data_points == len(sample_test_data)
    
    # Verify gateway calls
    assert mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.call_count == 2
    mock_gateways['prediction_model_gateway'].predict_multiple_metrics.assert_called_once()
    mock_gateways['prediction_model_gateway'].evaluate_model_accuracy.assert_called_once()
    mock_gateways['model_config_gateway'].save_model_evaluation.assert_called_once()


@pytest.mark.asyncio
async def test_execute_gateway_error(interactor, sample_request, mock_gateways):
    """Test execution with gateway error."""
    # Setup gateway to raise exception
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.side_effect = Exception("Gateway error")
    
    with pytest.raises(PredictionError, match="Model evaluation failed"):
        await interactor.execute(sample_request)


@pytest.mark.asyncio
async def test_execute_prediction_error(interactor, sample_request, sample_test_data, sample_training_data, mock_gateways):
    """Test execution with prediction service error."""
    # Setup mocks
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.side_effect = [
        (sample_test_data, Location(0.0, 0.0)),
        (sample_training_data, Location(0.0, 0.0))
    ]
    
    # Mock prediction service to raise exception
    mock_gateways['prediction_model_gateway'].predict_multiple_metrics.side_effect = Exception("Prediction error")
    
    with pytest.raises(PredictionError, match="Model evaluation failed"):
        await interactor.execute(sample_request)
