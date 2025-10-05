"""Tests for multi-metric prediction interactor."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from agrr_core.entity import WeatherData, Forecast, Location
from agrr_core.usecase.interactors.prediction_multi_metric_interactor import MultiMetricPredictionInteractor
from agrr_core.usecase.gateways.weather_data_gateway import WeatherDataGateway
from agrr_core.usecase.gateways.weather_data_repository_gateway import WeatherDataRepositoryGateway
from agrr_core.usecase.gateways.prediction_service_gateway import PredictionServiceGateway
from agrr_core.usecase.ports.output.prediction_presenter_output_port import PredictionPresenterOutputPort
from agrr_core.usecase.dto.prediction_config_dto import PredictionConfigDTO
from agrr_core.usecase.dto.multi_metric_prediction_request_dto import MultiMetricPredictionRequestDTO
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
    """Create interactor with mocked dependencies."""
    return MultiMetricPredictionInteractor(
        weather_data_gateway=mock_gateways['weather_data_gateway'],
        weather_data_repository_gateway=mock_gateways['weather_data_repository_gateway'],
        prediction_service_gateway=mock_gateways['prediction_service_gateway'],
        prediction_presenter_output_port=mock_gateways['prediction_presenter_port']
    )


@pytest.fixture
def sample_request():
    """Sample prediction request."""
    config = PredictionConfigDTO(
        model_type='Prophet',
        seasonality=True,
        trend=True,
        custom_params={},
        confidence_level=0.95,
        validation_split=0.2
    )
    
    return MultiMetricPredictionRequestDTO(
        latitude=35.6762,
        longitude=139.6503,
        start_date='2024-01-01',
        end_date='2024-01-31',
        prediction_days=7,
        metrics=['temperature', 'precipitation'],
        config=config,
        location_name='Tokyo'
    )


@pytest.mark.asyncio
async def test_execute_success(interactor, sample_request, sample_weather_data, mock_gateways):
    """Test successful multi-metric prediction execution."""
    # Setup mocks
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.return_value = (
        sample_weather_data, Location(35.6762, 139.6503)
    )
    
    # Mock forecasts
    forecasts = {
        'temperature': [
            Forecast(date=datetime(2024, 2, 1), predicted_value=25.0, confidence_lower=23.0, confidence_upper=27.0),
            Forecast(date=datetime(2024, 2, 2), predicted_value=26.0, confidence_lower=24.0, confidence_upper=28.0)
        ],
        'precipitation': [
            Forecast(date=datetime(2024, 2, 1), predicted_value=5.0, confidence_lower=2.0, confidence_upper=8.0),
            Forecast(date=datetime(2024, 2, 2), predicted_value=3.0, confidence_lower=1.0, confidence_upper=6.0)
        ]
    }
    
    mock_gateways['prediction_service_gateway'].predict_multiple_metrics.return_value = forecasts
    mock_gateways['weather_data_repository_gateway'].save_forecast_with_metadata.return_value = None
    
    # Execute
    result = await interactor.execute(sample_request)
    
    # Assertions
    assert result is not None
    assert 'historical_data' in result.__dict__
    assert 'forecasts' in result.__dict__
    assert 'model_metrics' in result.__dict__
    assert 'prediction_metadata' in result.__dict__
    
    # Verify gateway calls
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.assert_called_once()
    mock_gateways['prediction_service_gateway'].predict_multiple_metrics.assert_called_once()
    mock_gateways['weather_data_repository_gateway'].save_forecast_with_metadata.assert_called_once()


@pytest.mark.asyncio
async def test_execute_no_historical_data(interactor, sample_request, mock_gateways):
    """Test execution with no historical data."""
    # Setup mocks - return empty data
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.return_value = (
        [], Location(35.6762, 139.6503)
    )
    
    # Execute and expect exception
    with pytest.raises(PredictionError, match="No historical data available"):
        await interactor.execute(sample_request)


@pytest.mark.asyncio
async def test_execute_invalid_location(interactor, sample_request):
    """Test execution with invalid location."""
    # Invalid latitude
    sample_request.latitude = 200.0
    
    with pytest.raises(PredictionError, match="Invalid request parameters"):
        await interactor.execute(sample_request)


@pytest.mark.asyncio
async def test_execute_invalid_date_range(interactor, sample_request):
    """Test execution with invalid date range."""
    # Invalid date range
    sample_request.start_date = '2024-01-31'
    sample_request.end_date = '2024-01-01'
    
    with pytest.raises(PredictionError, match="Invalid request parameters"):
        await interactor.execute(sample_request)


@pytest.mark.asyncio
async def test_execute_gateway_error(interactor, sample_request, mock_gateways):
    """Test execution with gateway error."""
    # Setup gateway to raise exception
    mock_gateways['weather_data_gateway'].get_weather_data_by_location_and_date_range.side_effect = Exception("Gateway error")
    
    with pytest.raises(PredictionError, match="Prediction failed"):
        await interactor.execute(sample_request)
