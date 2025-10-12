"""Test for optimization intermediate result scheduling interactor.

Tests the weighted interval scheduling algorithm that finds the minimum cost
combination of non-overlapping optimization results.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.entities.field_entity import Field
from agrr_core.usecase.interactors.optimization_intermediate_result_schedule_interactor import (
    OptimizationIntermediateResultScheduleInteractor,
)
from agrr_core.usecase.dto.optimization_intermediate_result_schedule_request_dto import (
    OptimizationIntermediateResultScheduleRequestDTO,
)


class TestOptimizationIntermediateResultScheduleInteractor:
    """Test suite for optimization intermediate result scheduling."""

    @pytest.mark.asyncio
    async def test_empty_input(self):
        """Test with empty list of results."""
        interactor = OptimizationIntermediateResultScheduleInteractor()
        request = OptimizationIntermediateResultScheduleRequestDTO(results=[])
        
        response = await interactor.execute(request)
        
        assert response.total_cost == 0.0
        assert response.selected_results == []

    @pytest.mark.asyncio
    async def test_single_result(self):
        """Test with single valid result."""
        field = Field(field_id="field_1", name="Test Field", area=1000.0, daily_fixed_cost=100.0)
        
        result = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 1, 10),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field,
            is_optimal=False,
            base_temperature=10.0,
        )
        
        interactor = OptimizationIntermediateResultScheduleInteractor()
        request = OptimizationIntermediateResultScheduleRequestDTO(results=[result])
        
        response = await interactor.execute(request)
        
        assert response.total_cost == 1000.0
        assert len(response.selected_results) == 1
        assert response.selected_results[0].start_date == datetime(2025, 1, 1)

    @pytest.mark.asyncio
    async def test_non_overlapping_results_select_all(self):
        """Test with multiple non-overlapping results - should select all."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=80.0)
        field3 = Field(field_id="field_3", name="Field 3", area=1000.0, daily_fixed_cost=90.0)
        
        result1 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 1, 10),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field1,
            is_optimal=False,
            base_temperature=10.0,
        )
        result2 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 11),
            completion_date=datetime(2025, 1, 20),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field2,
            is_optimal=False,
            base_temperature=10.0,
        )
        result3 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 21),
            completion_date=datetime(2025, 1, 30),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field3,
            is_optimal=False,
            base_temperature=10.0,
        )
        
        interactor = OptimizationIntermediateResultScheduleInteractor()
        request = OptimizationIntermediateResultScheduleRequestDTO(
            results=[result1, result2, result3]
        )
        
        response = await interactor.execute(request)
        
        assert response.total_cost == 2700.0  # 1000 + 800 + 900
        assert len(response.selected_results) == 3

    @pytest.mark.asyncio
    async def test_overlapping_results_select_cheaper(self):
        """Test with overlapping results - should select cheaper one."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=133.33)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=75.0)
        
        # Expensive result
        result1 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 1, 15),
            growth_days=15,
            accumulated_gdd=100.0,
            field=field1,
            is_optimal=False,
            base_temperature=10.0,
        )
        # Cheaper result overlapping with result1
        result2 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 5),
            completion_date=datetime(2025, 1, 20),
            growth_days=16,
            accumulated_gdd=100.0,
            field=field2,
            is_optimal=False,
            base_temperature=10.0,
        )
        
        interactor = OptimizationIntermediateResultScheduleInteractor()
        request = OptimizationIntermediateResultScheduleRequestDTO(
            results=[result1, result2]
        )
        
        response = await interactor.execute(request)
        
        assert response.total_cost == 1200.0  # Select cheaper result2
        assert len(response.selected_results) == 1
        assert response.selected_results[0].start_date == datetime(2025, 1, 5)

    @pytest.mark.asyncio
    async def test_complex_scheduling(self):
        """Test complex case with multiple overlapping periods."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=72.73)
        field3 = Field(field_id="field_3", name="Field 3", area=1000.0, daily_fixed_cost=60.0)
        field4 = Field(field_id="field_4", name="Field 4", area=1000.0, daily_fixed_cost=70.0)
        
        # Period 1: Jan 1-10, cost 1000
        result1 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 1, 10),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field1,
            is_optimal=False,
            base_temperature=10.0,
        )
        # Period 2: Jan 5-15, cost 800 (overlaps with 1)
        result2 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 5),
            completion_date=datetime(2025, 1, 15),
            growth_days=11,
            accumulated_gdd=110.0,
            field=field2,
            is_optimal=False,
            base_temperature=10.0,
        )
        # Period 3: Jan 11-20, cost 600 (no overlap with 1, can combine with 1)
        result3 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 11),
            completion_date=datetime(2025, 1, 20),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field3,
            is_optimal=False,
            base_temperature=10.0,
        )
        # Period 4: Jan 21-30, cost 700 (no overlap with any above)
        result4 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 21),
            completion_date=datetime(2025, 1, 30),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field4,
            is_optimal=False,
            base_temperature=10.0,
        )
        
        interactor = OptimizationIntermediateResultScheduleInteractor()
        request = OptimizationIntermediateResultScheduleRequestDTO(
            results=[result1, result2, result3, result4]
        )
        
        response = await interactor.execute(request)
        
        # Possible combinations:
        # - result1 (1000) + result3 (600) + result4 (700) = 2300 (3 periods, result2 overlaps with 1 and 3)
        # - result2 (800) + result4 (700) = 1500 (2 periods, result2 overlaps with 1 and 3)
        # - result3 (600) + result4 (700) = 1300 (2 periods, result3 overlaps with 2)
        # Algorithm prioritizes: max periods, then min cost
        # Best combination: result1 + result3 + result4 = 2300 (3 periods, maximum coverage)
        assert response.total_cost == 2300.0
        assert len(response.selected_results) == 3
        assert response.selected_results[0].start_date == datetime(2025, 1, 1)
        assert response.selected_results[1].start_date == datetime(2025, 1, 11)
        assert response.selected_results[2].start_date == datetime(2025, 1, 21)

    @pytest.mark.asyncio
    async def test_filter_incomplete_results(self):
        """Test that incomplete results (None completion_date or cost) are filtered."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        
        # Valid result
        result1 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 1, 10),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field1,
            is_optimal=False,
            base_temperature=10.0,
        )
        # Incomplete - no completion date
        result2 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 5),
            completion_date=None,
            growth_days=None,
            accumulated_gdd=50.0,
            field=None,
            is_optimal=False,
            base_temperature=10.0,
        )
        # Incomplete - no field
        result3 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 15),
            completion_date=datetime(2025, 1, 20),
            growth_days=6,
            accumulated_gdd=60.0,
            field=None,
            is_optimal=False,
            base_temperature=10.0,
        )
        
        interactor = OptimizationIntermediateResultScheduleInteractor()
        request = OptimizationIntermediateResultScheduleRequestDTO(
            results=[result1, result2, result3]
        )
        
        response = await interactor.execute(request)
        
        # Only result1 should be selected
        assert response.total_cost == 1000.0
        assert len(response.selected_results) == 1
        assert response.selected_results[0].start_date == datetime(2025, 1, 1)

    @pytest.mark.asyncio
    async def test_same_start_date_boundary(self):
        """Test boundary case where completion_date equals next start_date."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=80.0)
        
        # Result1 ends on Jan 10
        result1 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 1, 10),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field1,
            is_optimal=False,
            base_temperature=10.0,
        )
        # Result2 starts on Jan 10 (same day as result1 ends)
        result2 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 10),
            completion_date=datetime(2025, 1, 20),
            growth_days=10,
            accumulated_gdd=110.0,
            field=field2,
            is_optimal=False,
            base_temperature=10.0,
        )
        
        interactor = OptimizationIntermediateResultScheduleInteractor()
        request = OptimizationIntermediateResultScheduleRequestDTO(
            results=[result1, result2]
        )
        
        response = await interactor.execute(request)
        
        # Should select both (boundary case: end <= start means non-overlapping)
        assert response.total_cost == 1800.0
        assert len(response.selected_results) == 2

    @pytest.mark.asyncio
    async def test_unordered_input(self):
        """Test that algorithm works with unordered input."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=70.0)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=100.0)
        field3 = Field(field_id="field_3", name="Field 3", area=1000.0, daily_fixed_cost=60.0)
        
        # Input in non-chronological order
        result1 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 21),
            completion_date=datetime(2025, 1, 30),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field1,
            is_optimal=False,
            base_temperature=10.0,
        )
        result2 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 1, 10),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field2,
            is_optimal=False,
            base_temperature=10.0,
        )
        result3 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 11),
            completion_date=datetime(2025, 1, 20),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field3,
            is_optimal=False,
            base_temperature=10.0,
        )
        
        interactor = OptimizationIntermediateResultScheduleInteractor()
        request = OptimizationIntermediateResultScheduleRequestDTO(
            results=[result1, result2, result3]
        )
        
        response = await interactor.execute(request)
        
        # Should still find optimal: all three non-overlapping
        assert response.total_cost == 2300.0
        assert len(response.selected_results) == 3

    @pytest.mark.asyncio
    async def test_save_schedule_with_gateway(self):
        """Test that schedule is saved when gateway is provided."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=80.0)
        
        # Create mock gateway
        mock_gateway = AsyncMock()
        
        # Create interactor with gateway
        interactor = OptimizationIntermediateResultScheduleInteractor(
            optimization_result_gateway=mock_gateway
        )
        
        # Create test data
        result1 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 1, 10),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field1,
            is_optimal=False,
            base_temperature=10.0,
        )
        result2 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 11),
            completion_date=datetime(2025, 1, 20),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field2,
            is_optimal=False,
            base_temperature=10.0,
        )
        
        request = OptimizationIntermediateResultScheduleRequestDTO(
            results=[result1, result2]
        )
        
        # Execute with schedule_id
        response = await interactor.execute(request, schedule_id="test_schedule_001")
        
        # Verify gateway.save was called
        mock_gateway.save.assert_called_once()
        call_args = mock_gateway.save.call_args
        
        # Check keyword arguments
        assert call_args.kwargs["optimization_id"] == "test_schedule_001"
        assert len(call_args.kwargs["results"]) == 2
        assert call_args.kwargs["total_cost"] == 1800.0
        
        # Verify response
        assert response.total_cost == 1800.0
        assert len(response.selected_results) == 2

    @pytest.mark.asyncio
    async def test_no_save_without_schedule_id(self):
        """Test that schedule is not saved when schedule_id is not provided."""
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        
        # Create mock gateway
        mock_gateway = AsyncMock()
        
        # Create interactor with gateway
        interactor = OptimizationIntermediateResultScheduleInteractor(
            optimization_result_gateway=mock_gateway
        )
        
        # Create test data
        result1 = OptimizationIntermediateResult(
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 1, 10),
            growth_days=10,
            accumulated_gdd=100.0,
            field=field1,
            is_optimal=False,
            base_temperature=10.0,
        )
        
        request = OptimizationIntermediateResultScheduleRequestDTO(results=[result1])
        
        # Execute without schedule_id
        response = await interactor.execute(request)
        
        # Verify gateway.save_schedule was NOT called
        mock_gateway.save_schedule.assert_not_called()
        
        # Verify response
        assert response.total_cost == 1000.0
