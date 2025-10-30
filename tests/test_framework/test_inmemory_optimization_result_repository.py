"""Tests for OptimizationResultInMemoryGateway."""

import pytest
from datetime import datetime

from agrr_core.adapter.gateways.optimization_result_inmemory_gateway import (
    OptimizationResultInMemoryGateway,
)
from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.entities.optimization_schedule_entity import (
    OptimizationSchedule,
)
from agrr_core.entity.entities.field_entity import Field

class TestOptimizationResultInMemoryGateway:
    """Test cases for OptimizationResultInMemoryGateway."""

    def test_save_and_get(self):
        """Test saving and retrieving optimization results."""
        repository = OptimizationResultInMemoryGateway()
        
        field = Field(field_id="test_field", name="Test Field", area=1000.0, daily_fixed_cost=5000.0)  # 530000 / 106 = 5000
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                field=field,
                is_optimal=True,
                base_temperature=10.0,
            )
        ]
        
        optimization_id = "test_opt_1"
        repository.save(optimization_id, results)
        
        retrieved = repository.get(optimization_id)
        assert retrieved is not None
        assert isinstance(retrieved, OptimizationSchedule)
        assert retrieved.schedule_id == optimization_id
        assert len(retrieved.selected_results) == 1
        assert retrieved.selected_results[0].start_date == datetime(2024, 4, 1)
        assert retrieved.selected_results[0].accumulated_gdd == 1500.0
        assert retrieved.selected_results[0].total_cost == 530000.0  # Calculated from field

    def test_get_nonexistent(self):
        """Test retrieving non-existent optimization results."""
        repository = OptimizationResultInMemoryGateway()
        
        retrieved = repository.get("nonexistent")
        assert retrieved is None

    def test_get_all(self):
        """Test retrieving all optimization results."""
        repository = OptimizationResultInMemoryGateway()
        
        field1 = Field(field_id="test_field_1", name="Field 1", area=1000.0, daily_fixed_cost=5000.0)
        field2 = Field(field_id="test_field_2", name="Field 2", area=1000.0, daily_fixed_cost=5000.0)
        
        results1 = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                field=field1,
                is_optimal=True,
                base_temperature=10.0,
            )
        ]
        
        results2 = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 5, 1),
                completion_date=datetime(2024, 8, 15),
                growth_days=107,
                accumulated_gdd=1600.0,
                field=field2,
                is_optimal=False,
                base_temperature=10.0,
            )
        ]
        
        repository.save("opt_1", results1)
        repository.save("opt_2", results2)
        
        all_results = repository.get_all()
        assert len(all_results) == 2
        assert all(isinstance(r, OptimizationSchedule) for r in all_results)
        
        # Check that both IDs exist
        schedule_ids = [r.schedule_id for r in all_results]
        assert "opt_1" in schedule_ids
        assert "opt_2" in schedule_ids
        
        # Check results content
        opt1_result = next(r for r in all_results if r.schedule_id == "opt_1")
        assert opt1_result.selected_results == results1

    def test_delete_existing(self):
        """Test deleting existing optimization results."""
        repository = OptimizationResultInMemoryGateway()
        
        field = Field(field_id="test_field", name="Test Field", area=1000.0, daily_fixed_cost=5000.0)
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                field=field,
                is_optimal=True,
                base_temperature=10.0,
            )
        ]
        
        optimization_id = "test_opt"
        repository.save(optimization_id, results)
        
        deleted = repository.delete(optimization_id)
        assert deleted is True
        
        retrieved = repository.get(optimization_id)
        assert retrieved is None

    def test_delete_nonexistent(self):
        """Test deleting non-existent optimization results."""
        repository = OptimizationResultInMemoryGateway()
        
        deleted = repository.delete("nonexistent")
        assert deleted is False

    def test_clear(self):
        """Test clearing all optimization results."""
        repository = OptimizationResultInMemoryGateway()
        
        field1 = Field(field_id="test_field_1", name="Field 1", area=1000.0, daily_fixed_cost=5000.0)
        field2 = Field(field_id="test_field_2", name="Field 2", area=1000.0, daily_fixed_cost=5000.0)
        
        results1 = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                field=field1,
                is_optimal=True,
                base_temperature=10.0,
            )
        ]
        
        results2 = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 5, 1),
                completion_date=datetime(2024, 8, 15),
                growth_days=107,
                accumulated_gdd=1600.0,
                field=field2,
                is_optimal=False,
                base_temperature=10.0,
            )
        ]
        
        repository.save("opt_1", results1)
        repository.save("opt_2", results2)
        
        repository.clear()
        
        all_results = repository.get_all()
        assert len(all_results) == 0

    def test_overwrite_existing(self):
        """Test overwriting existing optimization results."""
        repository = OptimizationResultInMemoryGateway()
        
        field1 = Field(field_id="test_field_1", name="Field 1", area=1000.0, daily_fixed_cost=5000.0)
        field2 = Field(field_id="test_field_2", name="Field 2", area=1000.0, daily_fixed_cost=5000.0)
        
        results1 = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                field=field1,
                is_optimal=True,
                base_temperature=10.0,
            )
        ]
        
        results2 = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 5, 1),
                completion_date=datetime(2024, 8, 15),
                growth_days=107,
                accumulated_gdd=1600.0,
                field=field2,
                is_optimal=False,
                base_temperature=10.0,
            )
        ]
        
        optimization_id = "test_opt"
        repository.save(optimization_id, results1)
        repository.save(optimization_id, results2)
        
        retrieved = repository.get(optimization_id)
        assert retrieved is not None
        assert retrieved.selected_results == results2
