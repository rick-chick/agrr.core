"""Test for optimization schedule gateway implementation.

Tests the gateway implementation that bridges UseCase and Framework layers
for schedule storage operations.
"""

import pytest
from datetime import datetime

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.entities.optimization_schedule_entity import (
    OptimizationSchedule,
)
from agrr_core.usecase.gateways.optimization_result_gateway import (
    OptimizationResultGateway,
)
from agrr_core.adapter.gateways.optimization_result_inmemory_gateway import (
    OptimizationResultInMemoryGateway,
)

class TestOptimizationScheduleGatewayImpl:
    """Test suite for optimization schedule gateway implementation."""

    def test_save_and_get_schedule(self):
        """Test saving and retrieving a schedule through gateway."""
        # Gateway directly implements the interface now
        gateway = OptimizationResultInMemoryGateway()
        
        # Create test results
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=100.0),
                is_optimal=False,
                base_temperature=10.0,
            ),
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 11),
                completion_date=datetime(2025, 1, 20),
                growth_days=10,
                accumulated_gdd=100.0,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=80.0),
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        # Save schedule through gateway using save()
        gateway.save("schedule_001", results, 1800.0)
        
        # Retrieve schedule through gateway using get()
        retrieved = gateway.get("schedule_001")
        
        assert retrieved is not None
        assert isinstance(retrieved, OptimizationSchedule)
        assert retrieved.schedule_id == "schedule_001"
        assert len(retrieved.selected_results) == 2
        assert retrieved.total_cost == 1800.0

    def test_get_all_schedules(self):
        """Test retrieving all schedules through gateway."""
        gateway = OptimizationResultInMemoryGateway()
        
        # Create test results
        results1 = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=100.0),
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
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=90.0),
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        # Save schedules using save()
        gateway.save("schedule_001", results1, 1000.0)
        gateway.save("schedule_002", results2, 900.0)
        
        # Retrieve all (includes schedules and intermediate results)
        all_results = gateway.get_all()
        all_schedules = [r for r in all_results if r.is_schedule]
        
        assert len(all_schedules) == 2
        assert all(isinstance(s, OptimizationSchedule) for s in all_schedules)
        schedule_ids = [s.schedule_id for s in all_schedules]
        assert "schedule_001" in schedule_ids
        assert "schedule_002" in schedule_ids

    def test_delete_schedule(self):
        """Test deleting a schedule through gateway."""
        gateway = OptimizationResultInMemoryGateway()
        
        # Create and save test result
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=100.0),
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        gateway.save("schedule_001", results, 1000.0)
        
        # Delete schedule using delete()
        deleted = gateway.delete("schedule_001")
        
        assert deleted is True
        
        # Verify it's gone
        retrieved = gateway.get("schedule_001")
        assert retrieved is None

    def test_clear_schedules(self):
        """Test clearing all schedules through gateway."""
        gateway = OptimizationResultInMemoryGateway()
        
        # Create and save test results
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2025, 1, 1),
                completion_date=datetime(2025, 1, 10),
                growth_days=10,
                accumulated_gdd=100.0,
                field=Field(field_id="test_field", name="Test", area=1000.0, daily_fixed_cost=100.0),
                is_optimal=False,
                base_temperature=10.0,
            ),
        ]
        
        gateway.save("schedule_001", results, 1000.0)
        gateway.save("schedule_002", results, 1000.0)
        
        # Clear all schedules
        gateway.clear_schedules()
        
        # Verify they're all gone
        all_results = gateway.get_all()
        all_schedules = [r for r in all_results if r.is_schedule]
        assert len(all_schedules) == 0
