"""Tests for InMemoryOptimizationResultRepository."""

import pytest
from datetime import datetime

from agrr_core.framework.repositories.inmemory_optimization_result_repository import (
    InMemoryOptimizationResultRepository,
)
from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)
from agrr_core.entity.entities.optimization_schedule_entity import (
    OptimizationSchedule,
)


@pytest.mark.asyncio
class TestInMemoryOptimizationResultRepository:
    """Test cases for InMemoryOptimizationResultRepository."""

    async def test_save_and_get(self):
        """Test saving and retrieving optimization results."""
        repository = InMemoryOptimizationResultRepository()
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                total_cost=530000.0,
                is_optimal=True,
                base_temperature=10.0,
            )
        ]
        
        optimization_id = "test_opt_1"
        await repository.save(optimization_id, results)
        
        retrieved = await repository.get(optimization_id)
        assert retrieved is not None
        assert isinstance(retrieved, OptimizationSchedule)
        assert retrieved.schedule_id == optimization_id
        assert len(retrieved.selected_results) == 1
        assert retrieved.selected_results[0].start_date == datetime(2024, 4, 1)
        assert retrieved.total_cost is None  # No total_cost for intermediate results
        assert retrieved.selected_results[0].accumulated_gdd == 1500.0

    async def test_get_nonexistent(self):
        """Test retrieving non-existent optimization results."""
        repository = InMemoryOptimizationResultRepository()
        
        retrieved = await repository.get("nonexistent")
        assert retrieved is None

    async def test_get_all(self):
        """Test retrieving all optimization results."""
        repository = InMemoryOptimizationResultRepository()
        
        results1 = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                total_cost=530000.0,
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
                total_cost=535000.0,
                is_optimal=False,
                base_temperature=10.0,
            )
        ]
        
        await repository.save("opt_1", results1)
        await repository.save("opt_2", results2)
        
        all_results = await repository.get_all()
        assert len(all_results) == 2
        assert all(isinstance(r, OptimizationSchedule) for r in all_results)
        
        # Check that both IDs exist
        schedule_ids = [r.schedule_id for r in all_results]
        assert "opt_1" in schedule_ids
        assert "opt_2" in schedule_ids
        
        # Check results content
        opt1_result = next(r for r in all_results if r.schedule_id == "opt_1")
        assert opt1_result.selected_results == results1

    async def test_delete_existing(self):
        """Test deleting existing optimization results."""
        repository = InMemoryOptimizationResultRepository()
        
        results = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                total_cost=530000.0,
                is_optimal=True,
                base_temperature=10.0,
            )
        ]
        
        optimization_id = "test_opt"
        await repository.save(optimization_id, results)
        
        deleted = await repository.delete(optimization_id)
        assert deleted is True
        
        retrieved = await repository.get(optimization_id)
        assert retrieved is None

    async def test_delete_nonexistent(self):
        """Test deleting non-existent optimization results."""
        repository = InMemoryOptimizationResultRepository()
        
        deleted = await repository.delete("nonexistent")
        assert deleted is False

    async def test_clear(self):
        """Test clearing all optimization results."""
        repository = InMemoryOptimizationResultRepository()
        
        results1 = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                total_cost=530000.0,
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
                total_cost=535000.0,
                is_optimal=False,
                base_temperature=10.0,
            )
        ]
        
        await repository.save("opt_1", results1)
        await repository.save("opt_2", results2)
        
        await repository.clear()
        
        all_results = await repository.get_all()
        assert len(all_results) == 0

    async def test_overwrite_existing(self):
        """Test overwriting existing optimization results."""
        repository = InMemoryOptimizationResultRepository()
        
        results1 = [
            OptimizationIntermediateResult(
                start_date=datetime(2024, 4, 1),
                completion_date=datetime(2024, 7, 15),
                growth_days=106,
                accumulated_gdd=1500.0,
                total_cost=530000.0,
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
                total_cost=535000.0,
                is_optimal=False,
                base_temperature=10.0,
            )
        ]
        
        optimization_id = "test_opt"
        await repository.save(optimization_id, results1)
        await repository.save(optimization_id, results2)
        
        retrieved = await repository.get(optimization_id)
        assert retrieved is not None
        assert retrieved.selected_results == results2

