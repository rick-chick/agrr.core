"""Test for in-memory optimization schedule repository.

Tests the storage and retrieval of optimization schedules.
"""

import pytest
from datetime import datetime

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.entities.optimization_schedule_entity import (
    OptimizationSchedule,
)
from agrr_core.entity.entities.field_entity import Field
from agrr_core.adapter.gateways.optimization_result_inmemory_gateway import (
    OptimizationResultInMemoryGateway,
)

class TestInMemoryOptimizationScheduleRepository:
    """Test suite for in-memory optimization schedule repository."""

    def test_save_and_get_schedule(self):
        """Test saving and retrieving a schedule."""
        repository = OptimizationResultInMemoryGateway()
        
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)  # 1000 / 10 = 100
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=80.0)   # 800 / 10 = 80
        
        # Create test results
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field1,
                is_optimal=False,
                base_temperature=10.0,
            ),
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 11),
                completion_date=datetime(2025, 1, 20),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field2,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        # Save schedule using save() with total_cost
        repository.save("schedule_001", results, 1800.0)
        
        # Retrieve schedule using get()
        retrieved = repository.get("schedule_001")
        
        assert retrieved is not None
        assert isinstance(retrieved, OptimizationSchedule)
        assert retrieved.schedule_id == "schedule_001"
        assert len(retrieved.selected_results) == 2
        assert retrieved.total_cost == 1800.0
        assert retrieved.selected_results[0].total_cost == 1000.0
        assert retrieved.selected_results[1].total_cost == 800.0

    def test_get_nonexistent_schedule(self):
        """Test retrieving a schedule that doesn't exist."""
        repository = OptimizationResultInMemoryGateway()
        
        result = repository.get("nonexistent")
        
        assert result is None

    def test_get_all_schedules(self):
        """Test retrieving all schedules."""
        repository = OptimizationResultInMemoryGateway()
        
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=90.0)
        
        # Create test results
        results1 = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field1,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        results2 = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 2, 1),
                completion_date=datetime(2025, 2, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field2,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        # Save schedules using save() with total_cost
        repository.save("schedule_001", results1, 1000.0)
        repository.save("schedule_002", results2, 900.0)
        
        # Retrieve all (filter schedules with is_schedule)
        all_results = repository.get_all()
        all_schedules = [r for r in all_results if r.is_schedule]
        
        assert len(all_schedules) == 2
        assert all(isinstance(s, OptimizationSchedule) for s in all_schedules)
        schedule_ids = [s.schedule_id for s in all_schedules]
        assert "schedule_001" in schedule_ids
        assert "schedule_002" in schedule_ids

    def test_delete_schedule(self):
        """Test deleting a schedule."""
        repository = OptimizationResultInMemoryGateway()
        
        field = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        
        # Create and save test result
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        repository.save("schedule_001", results, 1000.0)
        
        # Delete schedule using delete()
        deleted = repository.delete("schedule_001")
        
        assert deleted is True
        
        # Verify it's gone
        retrieved = repository.get("schedule_001")
        assert retrieved is None

    def test_delete_nonexistent_schedule(self):
        """Test deleting a schedule that doesn't exist."""
        repository = OptimizationResultInMemoryGateway()
        
        deleted = repository.delete("nonexistent")
        
        assert deleted is False

    def test_clear_schedules(self):
        """Test clearing all schedules."""
        repository = OptimizationResultInMemoryGateway()
        
        field = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        
        # Create and save test results
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        repository.save("schedule_001", results, 1000.0)
        repository.save("schedule_002", results, 1000.0)
        
        # Clear all schedules
        repository.clear_schedules()
        
        # Verify they're all gone
        all_results = repository.get_all()
        all_schedules = [r for r in all_results if r.is_schedule]
        assert len(all_schedules) == 0

    def test_schedules_and_results_separate(self):
        """Test that schedules and results storage are separate."""
        repository = OptimizationResultInMemoryGateway()
        
        field1 = Field(field_id="field_1", name="Field 1", area=1000.0, daily_fixed_cost=100.0)
        field2 = Field(field_id="field_2", name="Field 2", area=1000.0, daily_fixed_cost=90.0)
        
        # Save optimization results
        optimization_results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field1,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        repository.save("opt_001", optimization_results)
        
        # Save schedule
        schedule_results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 2, 1),
                completion_date=datetime(2025, 2, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=field2,
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        repository.save("schedule_001", schedule_results, 900.0)
        
        # Verify both exist independently
        opt_retrieved = repository.get("opt_001")
        schedule_retrieved = repository.get("schedule_001")
        
        assert opt_retrieved is not None
        assert isinstance(opt_retrieved, OptimizationSchedule)
        assert len(opt_retrieved.selected_results) == 1
        assert opt_retrieved.selected_results[0].total_cost == 1000.0
        assert opt_retrieved.total_cost is None  # Intermediate result, not a schedule
        
        assert schedule_retrieved is not None
        assert isinstance(schedule_retrieved, OptimizationSchedule)
        assert schedule_retrieved.schedule_id == "schedule_001"
        assert len(schedule_retrieved.selected_results) == 1
        assert schedule_retrieved.total_cost == 900.0  # Schedule has total_cost
        
        # Clear schedules should not affect optimization results
        repository.clear_schedules()
        
        opt_retrieved_after = repository.get("opt_001")
        assert opt_retrieved_after is not None
