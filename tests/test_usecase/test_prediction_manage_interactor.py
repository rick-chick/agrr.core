"""Tests for model management interactor."""

import pytest
from unittest.mock import AsyncMock

from agrr_core.usecase.interactors.prediction_manage_interactor import ModelManagementInteractor
from agrr_core.usecase.gateways.model_config_gateway import ModelConfigGateway
from agrr_core.usecase.gateways.prediction_model_gateway import PredictionModelGateway
from agrr_core.entity.exceptions.prediction_error import PredictionError


@pytest.fixture
def mock_gateways():
    """Mock gateways for testing."""
    model_config_gateway = AsyncMock(spec=ModelConfigGateway)
    prediction_model_gateway = AsyncMock(spec=PredictionModelGateway)
    
    return {
        'model_config_gateway': model_config_gateway,
        'prediction_model_gateway': prediction_model_gateway
    }


@pytest.fixture
def interactor(mock_gateways):
    """Create interactor with mocked dependencies."""
    return ModelManagementInteractor(
        model_config_gateway=mock_gateways['model_config_gateway'],
        prediction_model_gateway=mock_gateways['prediction_model_gateway']
    )


@pytest.mark.asyncio
async def test_get_available_models_success(interactor, mock_gateways):
    """Test successful retrieval of available models."""
    # Setup mock
    mock_models = ['Prophet', 'ARIMA', 'LSTM']
    mock_gateways['model_config_gateway'].get_available_models.return_value = mock_models
    
    # Execute
    result = await interactor.get_available_models()
    
    # Assertions
    assert result is not None
    assert len(result) == 3
    assert result[0] == {'name': 'Prophet', 'type': 'Prophet'}
    assert result[1] == {'name': 'ARIMA', 'type': 'ARIMA'}
    assert result[2] == {'name': 'LSTM', 'type': 'LSTM'}
    
    # Verify gateway call
    mock_gateways['model_config_gateway'].get_available_models.assert_called_once()


@pytest.mark.asyncio
async def test_get_available_models_empty(interactor, mock_gateways):
    """Test retrieval of available models when none exist."""
    # Setup mock to return empty list
    mock_gateways['model_config_gateway'].get_available_models.return_value = []
    
    # Execute
    result = await interactor.get_available_models()
    
    # Assertions
    assert result is not None
    assert len(result) == 0


@pytest.mark.asyncio
async def test_get_available_models_error(interactor, mock_gateways):
    """Test retrieval of available models with gateway error."""
    # Setup mock to raise exception
    mock_gateways['model_config_gateway'].get_available_models.side_effect = Exception("Gateway error")
    
    # Execute and expect exception
    with pytest.raises(PredictionError, match="Failed to get available models"):
        await interactor.get_available_models()


@pytest.mark.asyncio
async def test_get_model_info_success(interactor, mock_gateways):
    """Test successful retrieval of model info."""
    # Setup mock
    model_info = {
        'name': 'Prophet',
        'type': 'time_series',
        'description': 'Facebook Prophet time series forecasting',
        'parameters': ['seasonality', 'trend', 'holidays']
    }
    mock_gateways['prediction_model_gateway'].get_model_info.return_value = model_info
    
    # Execute
    result = await interactor.get_model_info('Prophet')
    
    # Assertions
    assert result is not None
    assert result['name'] == 'Prophet'
    assert result['type'] == 'time_series'
    assert result['description'] == 'Facebook Prophet time series forecasting'
    assert 'parameters' in result
    
    # Verify gateway call
    mock_gateways['prediction_model_gateway'].get_model_info.assert_called_once_with('Prophet')


@pytest.mark.asyncio
async def test_get_model_info_error(interactor, mock_gateways):
    """Test retrieval of model info with gateway error."""
    # Setup mock to raise exception
    mock_gateways['prediction_model_gateway'].get_model_info.side_effect = Exception("Model not found")
    
    # Execute and expect exception
    with pytest.raises(PredictionError, match="Failed to get model info for Prophet"):
        await interactor.get_model_info('Prophet')


@pytest.mark.asyncio
async def test_compare_models_not_implemented(interactor):
    """Test model comparison functionality (not yet implemented)."""
    # Execute and expect exception
    with pytest.raises(PredictionError, match="Model comparison not yet implemented"):
        await interactor.compare_models(
            historical_data=[],
            test_data=[],
            metrics=['temperature'],
            model_configs=[{'model_type': 'Prophet'}]
        )


@pytest.mark.asyncio
async def test_compare_models_with_parameters(interactor, mock_gateways):
    """Test model comparison with proper parameters."""
    # Setup mock to raise the expected exception
    mock_gateways['prediction_model_gateway'].get_model_info.side_effect = Exception("Not implemented")
    
    # Execute with various parameters
    historical_data = [{'time': '2024-01-01', 'value': 20.0}]
    test_data = [{'time': '2024-02-01', 'value': 25.0}]
    metrics = ['temperature', 'precipitation']
    model_configs = [
        {'model_type': 'Prophet'},
        {'model_type': 'ARIMA'}
    ]
    
    with pytest.raises(PredictionError, match="Model comparison not yet implemented"):
        await interactor.compare_models(
            historical_data=historical_data,
            test_data=test_data,
            metrics=metrics,
            model_configs=model_configs
        )
