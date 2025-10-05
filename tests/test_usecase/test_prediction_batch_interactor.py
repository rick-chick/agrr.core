"""Tests for batch prediction interactor."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from agrr_core.usecase.interactors.prediction_batch_interactor import BatchPredictionInteractor
from agrr_core.usecase.ports.input.multi_metric_prediction_input_port import MultiMetricPredictionInputPort
from agrr_core.usecase.dto.prediction_config_dto import PredictionConfigDTO
from agrr_core.usecase.dto.batch_prediction_request_dto import BatchPredictionRequestDTO
from agrr_core.usecase.dto.multi_metric_prediction_request_dto import MultiMetricPredictionRequestDTO
from agrr_core.usecase.dto.advanced_prediction_response_dto import AdvancedPredictionResponseDTO


@pytest.fixture
def mock_multi_metric_interactor():
    """Mock multi-metric prediction interactor."""
    return AsyncMock(spec=MultiMetricPredictionInputPort)


@pytest.fixture
def interactor(mock_multi_metric_interactor):
    """Create interactor with mocked dependencies."""
    return BatchPredictionInteractor(
        multi_metric_prediction_interactor=mock_multi_metric_interactor
    )


@pytest.fixture
def sample_request():
    """Sample batch prediction request."""
    config = PredictionConfigDTO(
        model_type='Prophet',
        seasonality=True,
        trend=True,
        custom_params={},
        confidence_level=0.95,
        validation_split=0.2
    )
    
    locations = [
        {'lat': 35.6762, 'lon': 139.6503, 'name': 'Tokyo'},
        {'lat': 40.7128, 'lon': -74.0060, 'name': 'New York'},
        {'lat': 51.5074, 'lon': -0.1278, 'name': 'London'}
    ]
    
    return BatchPredictionRequestDTO(
        locations=locations,
        start_date='2024-01-01',
        end_date='2024-01-31',
        prediction_days=7,
        metrics=['temperature', 'precipitation'],
        config=config
    )


@pytest.fixture
def sample_prediction_response():
    """Sample prediction response."""
    return AdvancedPredictionResponseDTO(
        historical_data=[],
        forecasts={},
        model_metrics={},
        prediction_metadata={}
    )


@pytest.mark.asyncio
async def test_execute_success(interactor, sample_request, sample_prediction_response, mock_multi_metric_interactor):
    """Test successful batch prediction execution."""
    # Setup mock to return successful predictions
    mock_multi_metric_interactor.execute.return_value = sample_prediction_response
    
    # Execute
    result = await interactor.execute(sample_request)
    
    # Assertions
    assert result is not None
    assert len(result.results) == 3  # All 3 locations should succeed
    assert len(result.errors) == 0
    assert result.summary['total_locations'] == 3
    assert result.summary['successful_predictions'] == 3
    assert result.summary['failed_predictions'] == 0
    assert result.processing_time > 0
    
    # Verify multi-metric interactor was called for each location
    assert mock_multi_metric_interactor.execute.call_count == 3


@pytest.mark.asyncio
async def test_execute_partial_success(interactor, sample_request, sample_prediction_response, mock_multi_metric_interactor):
    """Test batch prediction with partial success."""
    # Setup mock to succeed for first location, fail for others
    def side_effect(request):
        if request.latitude == 35.6762:  # Tokyo
            return sample_prediction_response
        else:
            raise Exception("Prediction failed")
    
    mock_multi_metric_interactor.execute.side_effect = side_effect
    
    # Execute
    result = await interactor.execute(sample_request)
    
    # Assertions
    assert result is not None
    assert len(result.results) == 1  # Only Tokyo should succeed
    assert len(result.errors) == 2   # New York and London should fail
    assert result.summary['total_locations'] == 3
    assert result.summary['successful_predictions'] == 1
    assert result.summary['failed_predictions'] == 2
    
    # Check error details
    error_locations = [error['location']['name'] for error in result.errors]
    assert 'New York' in error_locations
    assert 'London' in error_locations


@pytest.mark.asyncio
async def test_execute_all_failures(interactor, sample_request, mock_multi_metric_interactor):
    """Test batch prediction with all failures."""
    # Setup mock to fail for all locations
    mock_multi_metric_interactor.execute.side_effect = Exception("All predictions failed")
    
    # Execute
    result = await interactor.execute(sample_request)
    
    # Assertions
    assert result is not None
    assert len(result.results) == 0
    assert len(result.errors) == 3  # All locations should fail
    assert result.summary['total_locations'] == 3
    assert result.summary['successful_predictions'] == 0
    assert result.summary['failed_predictions'] == 3
    
    # Check all errors have the same message
    for error in result.errors:
        assert error['error'] == "All predictions failed"
        assert error['status'] == 'failed'


@pytest.mark.asyncio
async def test_execute_empty_locations(interactor, mock_multi_metric_interactor):
    """Test batch prediction with empty locations list."""
    config = PredictionConfigDTO(
        model_type='Prophet',
        seasonality=True,
        trend=True,
        custom_params={},
        confidence_level=0.95,
        validation_split=0.2
    )
    
    empty_request = BatchPredictionRequestDTO(
        locations=[],
        start_date='2024-01-01',
        end_date='2024-01-31',
        prediction_days=7,
        metrics=['temperature'],
        config=config
    )
    
    # Execute
    result = await interactor.execute(empty_request)
    
    # Assertions
    assert result is not None
    assert len(result.results) == 0
    assert len(result.errors) == 0
    assert result.summary['total_locations'] == 0
    assert result.summary['successful_predictions'] == 0
    assert result.summary['failed_predictions'] == 0
    
    # Verify multi-metric interactor was not called
    mock_multi_metric_interactor.execute.assert_not_called()
