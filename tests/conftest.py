"""Pytest configuration and shared fixtures.

Fixtures are organized by Clean Architecture layers:
1. Entity Layer - Domain entities and value objects
2. UseCase Layer - Gateways and Ports (interfaces)
3. Adapter Layer - Repositories and Services (implementations)
4. Framework Layer - External service clients
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from agrr_core.entity import WeatherData, Forecast, Location
from agrr_core.entity import (
    Crop,
    GrowthStage,
    TemperatureProfile,
    SunshineProfile,
    ThermalRequirement,
    StageRequirement,
)
from agrr_core.entity.entities.crop_profile_entity import CropProfile


# ============================================================================
# Entity Layer Fixtures
# ============================================================================

@pytest.fixture
def entity_weather_data():
    """Single weather data entity for testing."""
    return WeatherData(
        time=datetime(2024, 1, 1),
        temperature_2m_max=25.0,
        temperature_2m_min=15.0,
        temperature_2m_mean=20.0,
        precipitation_sum=5.0,
        sunshine_duration=28800.0
    )


@pytest.fixture
def entity_weather_data_list():
    """List of weather data entities for testing."""
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
def entity_forecast():
    """Single forecast entity for testing."""
    return Forecast(
        date=datetime(2024, 1, 2),
        predicted_value=22.0,
        confidence_lower=20.0,
        confidence_upper=24.0
    )


@pytest.fixture
def entity_forecast_list():
    """List of forecast entities for testing."""
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
def entity_location():
    """Location entity for testing."""
    return Location(35.6762, 139.6503)


@pytest.fixture
def entity_crop_profile() -> CropProfile:
    """Crop requirement aggregate entity for testing."""
    crop = Crop(crop_id="tomato", name="Tomato", area_per_unit=0.5, variety=None)
    stage = GrowthStage(name="Vegetative", order=1)
    temp = TemperatureProfile(
        base_temperature=10.0,
        optimal_min=20.0,
        optimal_max=26.0,
        low_stress_threshold=12.0,
        high_stress_threshold=32.0,
        frost_threshold=0.0,
        sterility_risk_threshold=None,
    )
    sun = SunshineProfile(minimum_sunshine_hours=3.0, target_sunshine_hours=6.0)
    thermal = ThermalRequirement(required_gdd=400.0)
    sr = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
    return CropProfile(crop=crop, stage_requirements=[sr])


@pytest.fixture
def entity_crop_profile_rice() -> CropProfile:
    """Rice crop requirement aggregate for growth progress tests."""
    crop = Crop(crop_id="rice", name="Rice", area_per_unit=0.25, variety="Koshihikari")
    stage = GrowthStage(name="Vegetative", order=1)
    temp = TemperatureProfile(
        base_temperature=10.0,
        optimal_min=20.0,
        optimal_max=30.0,
        low_stress_threshold=15.0,
        high_stress_threshold=35.0,
        frost_threshold=0.0,
    )
    sun = SunshineProfile(minimum_sunshine_hours=4.0, target_sunshine_hours=8.0)
    thermal = ThermalRequirement(required_gdd=500.0)
    sr = StageRequirement(stage=stage, temperature=temp, sunshine=sun, thermal=thermal)
    return CropProfile(crop=crop, stage_requirements=[sr])


# ============================================================================
# UseCase Layer Fixtures - Gateway Interfaces
# ============================================================================

@pytest.fixture
def gateway_weather(entity_weather_data_list):
    """Mock WeatherGateway (UseCase layer interface)."""
    gateway = AsyncMock()
    gateway.get.return_value = entity_weather_data_list
    gateway.get_by_location_and_date_range.return_value = entity_weather_data_list
    return gateway


@pytest.fixture
def gateway_crop_profile(entity_crop_profile):
    """Mock CropProfileGateway (UseCase layer interface)."""
    gateway = AsyncMock()
    gateway.craft.return_value = entity_crop_profile
    
    # Mock 3-step LLM methods
    gateway.extract_crop_variety.return_value = {
        "crop_name": "Tomato",
        "variety": "default"
    }
    gateway.define_growth_stages.return_value = {
        "crop_info": {
            "name": "Tomato",
            "variety": "default"
        },
        "management_stages": [
            {
                "stage_name": "Vegetative",
                "management_focus": "Growth establishment",
                "management_boundary": "First flower appearance"
            }
        ]
    }
    gateway.research_stage_requirements.return_value = {
        "stage_name": "Vegetative",
        "temperature": {
            "base_temperature": 10.0,
            "optimal_min": 20.0,
            "optimal_max": 26.0,
            "low_stress_threshold": 12.0,
            "high_stress_threshold": 32.0,
            "frost_threshold": 0.0,
            "sterility_risk_threshold": 35.0
        },
        "sunshine": {
            "minimum_sunshine_hours": 3.0,
            "target_sunshine_hours": 6.0
        },
        "thermal": {
            "required_gdd": 400.0
        }
    }
    gateway.extract_crop_economics.return_value = {
        "area_per_unit": 0.5,
        "revenue_per_area": 2000.0
    }
    gateway.extract_crop_family.return_value = {
        "family_ja": "ナス科",
        "family_scientific": "Solanaceae"
    }
    return gateway


@pytest.fixture
def gateway_interaction_rule():
    """Mock InteractionRuleGateway (UseCase layer interface)."""
    gateway = AsyncMock()
    gateway.get_rules.return_value = []
    return gateway


# ============================================================================
# UseCase Layer Fixtures - Output Ports (Presenter Interfaces)
# ============================================================================

@pytest.fixture
def output_port_crop_profile():
    """Mock CropRequirementOutputPort (presenter interface)."""
    port = MagicMock()
    port.format_success.side_effect = lambda data: {"success": True, "data": data}
    port.format_error.side_effect = lambda msg, error_code="CROP_REQUIREMENT_ERROR": {
        "success": False,
        "error": msg,
        "code": error_code,
    }
    return port


@pytest.fixture
def output_port_weather():
    """Mock WeatherOutputPort (presenter interface)."""
    port = MagicMock()
    port.format_success.return_value = {'success': True, 'data': {}}
    port.format_error.return_value = {'error': 'Test error'}
    return port


@pytest.fixture
def output_port_prediction(entity_forecast_list):
    """Mock PredictionOutputPort (presenter interface)."""
    port = AsyncMock()
    port.predict_multiple_metrics.return_value = {
        'temperature': entity_forecast_list,
        'precipitation': entity_forecast_list
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
    port.predict_with_confidence_intervals.return_value = entity_forecast_list
    port.batch_predict.return_value = [
        {'temperature': entity_forecast_list},
        {'temperature': entity_forecast_list}
    ]
    port.get_available_models.return_value = [
        {'model_type': 'prophet', 'name': 'Facebook Prophet'},
        {'model_type': 'lstm', 'name': 'LSTM'},
        {'model_type': 'arima', 'name': 'ARIMA'}
    ]
    return port


@pytest.fixture
def output_port_growth_progress():
    """Mock GrowthProgressCalculateOutputPort (presenter interface)."""
    presenter = MagicMock()
    presenter.present = MagicMock()
    return presenter


# ============================================================================
# UseCase Layer Fixtures - Input Ports (for advanced features)
# ============================================================================

@pytest.fixture
def input_port_prediction():
    """Mock PredictionInputPort (for advanced prediction features)."""
    port = AsyncMock()
    port.save_prediction_config.return_value = None
    port.get_model_performance.return_value = {'accuracy': 0.85}
    port.save_model_evaluation.return_value = None
    port.get_available_models.return_value = ['prophet', 'lstm', 'arima']
    port.save_forecast_with_metadata.return_value = None
    return port


# ============================================================================
# Adapter Layer Fixtures - Repository Implementations
# ============================================================================

@pytest.fixture
def repository_weather_data(entity_weather_data_list, entity_location):
    """Mock weather data repository (Adapter layer implementation)."""
    repository = AsyncMock()
    repository.get_weather_data_by_location_and_date_range.return_value = (
        entity_weather_data_list, entity_location
    )
    repository.save_weather_data.return_value = None
    return repository


@pytest.fixture
def repository_prediction(entity_forecast_list):
    """Mock prediction repository (Adapter layer implementation)."""
    repository = AsyncMock()
    repository.save_forecast.return_value = None
    repository.get_forecast_by_date_range.return_value = entity_forecast_list
    repository.clear.return_value = None
    return repository


@pytest.fixture
def repository_file():
    """Mock file repository (Adapter layer implementation)."""
    repository = AsyncMock()
    repository.exists.return_value = True
    repository.read.return_value = '{"data": [{"time": "2024-01-01", "temperature_2m_max": 25.0}]}'
    repository.write.return_value = None
    repository.delete.return_value = None
    return repository


# ============================================================================
# Adapter Layer Fixtures - Service Implementations
# ============================================================================

@pytest.fixture
def service_prophet(entity_forecast_list):
    """Mock Prophet prediction service (Adapter layer implementation)."""
    service = AsyncMock()
    service.predict_weather.return_value = entity_forecast_list
    return service


@pytest.fixture
def service_lstm(entity_forecast_list):
    """Mock LSTM prediction service (Adapter layer implementation)."""
    service = AsyncMock()
    service.predict_multiple_metrics.return_value = {
        'temperature': entity_forecast_list
    }
    return service


@pytest.fixture
def service_arima(entity_forecast_list):
    """Mock ARIMA prediction service (Adapter layer implementation)."""
    service = AsyncMock()
    service.predict_multiple_metrics.return_value = {
        'temperature': entity_forecast_list
    }
    return service


# ============================================================================
# Framework Layer Fixtures - External Services
# ============================================================================

@pytest.fixture
def external_http_service():
    """Mock HTTP service for external API calls (Framework layer)."""
    service = AsyncMock()
    service.get.return_value = {
        'latitude': 35.6762,
        'longitude': 139.6503,
        'elevation': 10.0,
        'timezone': 'Asia/Tokyo',
        'daily': {
            'time': ['2024-01-01', '2024-01-02'],
            'temperature_2m_max': [25.0, 26.0],
            'temperature_2m_min': [15.0, 16.0],
            'temperature_2m_mean': [20.0, 21.0],
            'precipitation_sum': [5.0, 3.0],
            'sunshine_duration': [28800.0, 30000.0]
        }
    }
    return service


# ============================================================================
# Pytest Configuration
# ============================================================================

# Async test marker
pytest_plugins = ['pytest_asyncio']


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")
