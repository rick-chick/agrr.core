"""Integration test for error handling in multi-field crop allocation.

Tests that partial crop failures are handled gracefully using actual test data.
"""

import pytest
from datetime import datetime

from agrr_core.framework.repositories.file_repository import FileRepository
from agrr_core.adapter.gateways.crop_profile_file_gateway import CropProfileFileGateway
from agrr_core.adapter.gateways.weather_file_gateway import WeatherFileGateway
from agrr_core.adapter.gateways.field_file_gateway import FieldFileGateway
from agrr_core.adapter.gateways.crop_profile_inmemory_gateway import CropProfileInMemoryGateway
from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
)
from agrr_core.usecase.dto.multi_field_crop_allocation_request_dto import (
    MultiFieldCropAllocationRequestDTO,
)


@pytest.mark.asyncio
async def test_partial_crop_failure_continues_with_real_data():
    """Test that allocation continues when some crops cannot complete growth.
    
    Using test_data with autumn start:
    - ナス (base_temp=10°C): Cannot complete in available period
    - ほうれん草 (base_temp=0°C): Can complete even in winter
    """
    file_repo = FileRepository()
    
    # Setup gateways with test data
    crop_gateway = CropProfileFileGateway(
        file_repository=file_repo,
        file_path="test_data/allocation_crops_1760447748.json"
    )
    
    weather_gateway = WeatherFileGateway(
        file_repository=file_repo,
        file_path="test_data/allocation_weather_1760447748.json"
    )
    
    
    field_gateway = FieldFileGateway(
        file_repository=file_repo,
        file_path="test_data/allocation_fields_1760447748.json"
    )
    
    
    # Internal crop profile gateway
    crop_profile_gateway_internal = CropProfileInMemoryGateway()
    
    # Create interactor
    interactor = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
    )
    
    # Execute with autumn start (summer crops will fail, winter crops should succeed)
    request = MultiFieldCropAllocationRequestDTO(
        field_ids=["field_1", "field_2", "field_3", "field_4"],
        planning_period_start=datetime(2025, 9, 1),
        planning_period_end=datetime(2026, 12, 29),
        optimization_objective="maximize_profit",
    )
    
    # Should not raise exception (partial success)
    result = await interactor.execute(request)
    
    # Verify result exists
    assert result is not None
    assert result.optimization_result is not None
    
    # Verify we have allocations
    assert len(result.optimization_result.field_schedules) > 0
    
    # Verify some crop was allocated (winter crops)
    total_allocations = sum(len(schedule.allocations) for schedule in result.optimization_result.field_schedules)
    assert total_allocations > 0
    
    # Verify profit is positive
    assert result.optimization_result.total_profit > 0


@pytest.mark.asyncio
async def test_all_crops_fail_raises_error_with_real_data():
    """Test that appropriate error is raised when all crops fail.
    
    Using test_data with very late start (near end of weather data):
    - All crops: Cannot complete due to insufficient remaining data
    """
    file_repo = FileRepository()
    
    # Setup gateways
    crop_gateway = CropProfileFileGateway(
        file_repository=file_repo,
        file_path="test_data/allocation_crops_1760447748.json"
    )
    
    weather_gateway = WeatherFileGateway(
        file_repository=file_repo,
        file_path="test_data/allocation_weather_1760447748.json"
    )
    
    
    field_gateway = FieldFileGateway(
        file_repository=file_repo,
        file_path="test_data/allocation_fields_1760447748.json"
    )
    
    
    # Internal crop profile gateway
    crop_profile_gateway_internal = CropProfileInMemoryGateway()
    
    # Create interactor
    interactor = MultiFieldCropAllocationGreedyInteractor(
        field_gateway=field_gateway,
        crop_gateway=crop_gateway,
        weather_gateway=weather_gateway,
        crop_profile_gateway_internal=crop_profile_gateway_internal,
    )
    
    # Execute with very late start (all crops will fail)
    request = MultiFieldCropAllocationRequestDTO(
        field_ids=["field_1", "field_2", "field_3", "field_4"],
        planning_period_start=datetime(2026, 11, 1),
        planning_period_end=datetime(2026, 12, 29),
        optimization_objective="maximize_profit",
    )
    
    # Should raise ValueError with helpful message
    with pytest.raises(ValueError) as exc_info:
        await interactor.execute(request)
    
    error_message = str(exc_info.value)
    assert "No valid allocation candidates" in error_message
    assert "Possible causes:" in error_message

