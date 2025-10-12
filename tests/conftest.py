"""Pytest configuration and shared fixtures."""

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
from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
    CropRequirementAggregate,
)


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


# ==== Crop requirement crafting (LLM-backed) fixtures ====

@pytest.fixture
def sample_crop_requirement_aggregate() -> CropRequirementAggregate:
    """Build a simple aggregate for testing crafting use case."""
    crop = Crop(crop_id="tomato", name="Tomato", area_per_unit=0.5, variety=None)  # No specific variety
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
    return CropRequirementAggregate(crop=crop, stage_requirements=[sr])


@pytest.fixture
def mock_crop_requirement_gateway(sample_crop_requirement_aggregate):
    gateway = AsyncMock()
    gateway.craft.return_value = sample_crop_requirement_aggregate
    
    # Mock 3-step methods
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
def mock_crop_requirement_output_port():
    port = MagicMock()
    port.format_success.side_effect = lambda data: {"success": True, "data": data}
    port.format_error.side_effect = lambda msg, error_code="CROP_REQUIREMENT_ERROR": {
        "success": False,
        "error": msg,
        "code": error_code,
    }
    return port


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
def mock_http_service():
    """Mock HTTP service for testing."""
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


# ==== Growth progress calculation fixtures ====

@pytest.fixture
def mock_growth_progress_crop_requirement_gateway():
    """Mock CropRequirementGateway for growth progress tests."""
    from agrr_core.entity.entities.crop_entity import Crop
    from agrr_core.entity.entities.growth_stage_entity import GrowthStage
    from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
    from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
    from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
    from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
    from agrr_core.entity.entities.crop_requirement_aggregate_entity import (
        CropRequirementAggregate,
    )
    
    gateway = AsyncMock()
    
    # Default mock aggregate
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
    aggregate = CropRequirementAggregate(crop=crop, stage_requirements=[sr])
    
    gateway.craft.return_value = aggregate
    return gateway


@pytest.fixture
def mock_growth_progress_weather_gateway():
    """Mock WeatherGateway for growth progress tests."""
    from agrr_core.entity.entities.weather_entity import WeatherData
    from datetime import datetime
    
    gateway = AsyncMock()
    
    # Default mock weather data
    weather_data = [
        WeatherData(
            time=datetime(2024, 5, 1),
            temperature_2m_mean=25.0,
            temperature_2m_max=30.0,
            temperature_2m_min=20.0,
        ),
        WeatherData(
            time=datetime(2024, 5, 2),
            temperature_2m_mean=25.0,
            temperature_2m_max=30.0,
            temperature_2m_min=20.0,
        ),
    ]
    
    gateway.get.return_value = weather_data
    return gateway


@pytest.fixture
def mock_growth_progress_presenter():
    """Mock GrowthProgressCalculateOutputPort for tests."""
    presenter = MagicMock()
    presenter.present = MagicMock()
    return presenter


@pytest.fixture
def mock_file_repository():
    """Mock file repository for testing."""
    repository = AsyncMock()
    repository.exists.return_value = True
    repository.read.return_value = '{"data": [{"time": "2024-01-01", "temperature_2m_max": 25.0}]}'
    repository.write.return_value = None
    repository.delete.return_value = None
    return repository


@pytest.fixture
def mock_interaction_rule_gateway():
    """Mock InteractionRuleGateway for testing."""
    gateway = AsyncMock()
    gateway.get_rules.return_value = []
    return gateway




# Async test marker
pytest_plugins = ['pytest_asyncio']


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "asyncio: mark test as async")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")