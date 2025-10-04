"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from agrr_core.entity import WeatherData, Forecast, Location


@pytest.fixture
def mock_weather_data():
    """Mock weather data for testing."""
    return WeatherData(
        time=datetime(2024, 1, 1),
        temperature_2m_max=25.0,
        temperature_2m_min=15.0,
        temperature_2m_mean=20.0,
        precipitation_sum=5.0,
        sunshine_duration=28800.0
    )


@pytest.fixture
def mock_forecast():
    """Mock forecast for testing."""
    return Forecast(
        date=datetime(2024, 1, 2),
        predicted_value=22.0,
        confidence_lower=20.0,
        confidence_upper=24.0
    )


@pytest.fixture
def mock_location():
    """Mock location for testing."""
    return Location(35.6762, 139.6503)


@pytest.fixture
def sample_weather_data_list():
    """Sample list of weather data for testing."""
    data = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(30):
        date = base_date + timedelta(days=i)
        weather_data = WeatherData(
            time=date,
            temperature_2m_max=20.0 + i * 0.5,
            temperature_2m_min=10.0 + i * 0.3,
            temperature_2m_mean=15.0 + i * 0.4,
            precipitation_sum=float(i % 5),
            sunshine_duration=3600.0 + i * 100
        )
        data.append(weather_data)
    
    return data


@pytest.fixture
def sample_forecast_list():
    """Sample list of forecasts for testing."""
    forecasts = []
    base_date = datetime(2024, 2, 1)
    
    for i in range(7):
        date = base_date + timedelta(days=i)
        forecast = Forecast(
            date=date,
            predicted_value=20.0 + i * 0.5,
            confidence_lower=18.0 + i * 0.5,
            confidence_upper=22.0 + i * 0.5
        )
        forecasts.append(forecast)
    
    return forecasts


@pytest.fixture
def mock_prophet_service():
    """Mock Prophet prediction service."""
    service = AsyncMock()
    service.predict_weather.return_value = sample_forecast_list()
    return service


@pytest.fixture
def mock_lstm_service():
    """Mock LSTM prediction service."""
    service = AsyncMock()
    service.predict_multiple_metrics.return_value = {
        'temperature': sample_forecast_list()
    }
    return service


@pytest.fixture
def mock_arima_service():
    """Mock ARIMA prediction service."""
    service = AsyncMock()
    service.predict_multiple_metrics.return_value = {
        'temperature': sample_forecast_list()
    }
    return service


@pytest.fixture
def mock_weather_data_repository():
    """Mock weather data repository."""
    repository = AsyncMock()
    repository.get_weather_data_by_location_and_date_range.return_value = (
        sample_weather_data_list(), mock_location()
    )
    repository.save_weather_data.return_value = None
    return repository


@pytest.fixture
def mock_prediction_repository():
    """Mock prediction repository."""
    repository = AsyncMock()
    repository.save_forecast.return_value = None
    repository.get_forecast_by_date_range.return_value = sample_forecast_list()
    repository.clear.return_value = None
    return repository


@pytest.fixture
def mock_prediction_presenter():
    """Mock prediction presenter."""
    presenter = MagicMock()
    presenter.format_prediction_dto.return_value = {'success': True}
    presenter.format_error.return_value = {'error': 'Test error'}
    presenter.format_success.return_value = {'success': True, 'data': {}}
    return presenter


@pytest.fixture
def mock_advanced_prediction_input_port():
    """Mock advanced prediction input port."""
    port = AsyncMock()
    port.save_prediction_config.return_value = None
    port.get_model_performance.return_value = {'accuracy': 0.85}
    port.save_model_evaluation.return_value = None
    port.get_available_models.return_value = ['prophet', 'lstm', 'arima']
    port.save_forecast_with_metadata.return_value = None
    return port


@pytest.fixture
def mock_advanced_prediction_output_port():
    """Mock advanced prediction output port."""
    port = AsyncMock()
    port.predict_multiple_metrics.return_value = {
        'temperature': sample_forecast_list(),
        'precipitation': sample_forecast_list()
    }
    port.evaluate_model_accuracy.return_value = {
        'mae': 1.5,
        'mse': 2.25,
        'rmse': 1.5,
        'mape': 5.0
    }
    port.train_model.return_value = {'status': 'trained'}
    port.get_model_info.return_value = {
        'model_type': 'prophet',
        'description': 'Test model'
    }
    port.predict_with_confidence_intervals.return_value = sample_forecast_list()
    port.batch_predict.return_value = [
        {'temperature': sample_forecast_list()},
        {'temperature': sample_forecast_list()}
    ]
    port.get_available_models.return_value = [
        {'model_type': 'prophet', 'name': 'Facebook Prophet'},
        {'model_type': 'lstm', 'name': 'LSTM'},
        {'model_type': 'arima', 'name': 'ARIMA'}
    ]
    return port


@pytest.fixture
def mock_visualization_service():
    """Mock visualization service."""
    service = AsyncMock()
    service.create_prediction_chart.return_value = {
        'status': 'success',
        'image_base64': 'base64_encoded_image_data'
    }
    service.create_trend_analysis_chart.return_value = {
        'status': 'success',
        'image_base64': 'base64_encoded_trend_data'
    }
    service.create_model_comparison_chart.return_value = {
        'status': 'success',
        'image_base64': 'base64_encoded_comparison_data'
    }
    service.create_visualization_data.return_value = MagicMock()
    return service


# Async test marker
pytest_plugins = ['pytest_asyncio']


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")