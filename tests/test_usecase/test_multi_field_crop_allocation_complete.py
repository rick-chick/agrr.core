"""Complete test for multi-field crop allocation with all neighborhood operations."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.interactors.multi_field_crop_allocation_greedy_interactor import (
    MultiFieldCropAllocationGreedyInteractor,
    AllocationCandidate,
)
from agrr_core.usecase.dto.optimization_config import OptimizationConfig
from agrr_core.usecase.services.neighbor_operations import (
    FieldSwapOperation,
    FieldMoveOperation,
    FieldReplaceOperation,
    FieldRemoveOperation,
    CropInsertOperation,
    CropChangeOperation,
    PeriodReplaceOperation,
    AreaAdjustOperation,
)


class TestMultiFieldCropAllocationComplete:
    """Test all neighborhood operations in the complete framework."""

    def test_field_operations_complete(self):
        """Test that all Field operations are implemented."""
        # Verify operation classes exist (Phase 1 refactoring)
        field_swap = FieldSwapOperation()
        field_move = FieldMoveOperation()
        field_replace = FieldReplaceOperation()
        field_remove = FieldRemoveOperation()
        
        # Verify operation names
        assert field_swap.operation_name == "field_swap"
        assert field_move.operation_name == "field_move"
        assert field_replace.operation_name == "field_replace"
        assert field_remove.operation_name == "field_remove"

    def test_crop_operations_complete(self):
        """Test that all Crop operations are implemented."""
        # Verify operation classes exist (Phase 1 refactoring)
        crop_insert = CropInsertOperation()
        crop_change = CropChangeOperation()
        
        # Verify operation names
        assert crop_insert.operation_name == "crop_insert"
        assert crop_change.operation_name == "crop_change"

    def test_period_operations_complete(self):
        """Test that Period operations use DP results."""
        # Verify operation class exists (Phase 1 refactoring)
        period_replace = PeriodReplaceOperation()
        assert period_replace.operation_name == "period_replace"

    def test_area_operations_complete(self):
        """Test that Area operations are implemented."""
        # Verify operation class exists
        area_adjust = AreaAdjustOperation()
        assert area_adjust.operation_name == "area_adjust"

    def test_area_adjust_increases_profit(self):
        """Test that area adjustment can increase profit."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        
        # Allocation using 50% of field (500m²)
        alloc = CropAllocation(
            allocation_id="alloc_1",
            field=field,
            crop=rice,
            area_used=500.0,  # 50% of field area
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,  # Fixed cost
            expected_revenue=25000000.0,  # 500 × 50000
            profit=24235000.0,
        )
        
        solution = [alloc]
        
        # Use AreaAdjustOperation
        operation = AreaAdjustOperation()
        config = OptimizationConfig()
        context = {"config": config}
        
        # Generate area adjustment neighbors
        neighbors = operation.generate_neighbors(solution, context)
        
        # Should generate neighbors with adjusted areas
        assert len(neighbors) > 0
        
        # Check that some neighbors have increased area
        increased_area_neighbors = [
            n for n in neighbors 
            if n[0].area_used > alloc.area_used
        ]
        assert len(increased_area_neighbors) > 0

    def test_crop_insert_adds_new_allocation(self):
        """Test that crop insert adds new allocations."""
        field_a = Field("f1", "Field A", 1000.0, 5000.0)
        field_b = Field("f2", "Field B", 1000.0, 6000.0)
        
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        tomato = Crop("tomato", "Tomato", 0.3, revenue_per_area=60000.0)
        
        # Current solution: Only Rice in Field A
        alloc_current = CropAllocation(
            allocation_id="alloc_1",
            field=field_a,
            crop=rice,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
            expected_revenue=25000000.0,  # 500 × 50000
            profit=24235000.0,
        )
        
        solution = [alloc_current]
        
        # Unused candidates
        candidate_tomato_a = AllocationCandidate(
            field=field_a,
            crop=tomato,
            start_date=datetime(2025, 9, 1),  # Different period
            completion_date=datetime(2025, 12, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            area_used=500.0,
        )
        
        candidate_rice_b = AllocationCandidate(
            field=field_b,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            area_used=1000.0,
        )
        
        candidates = [candidate_tomato_a, candidate_rice_b]
        
        # Use CropInsertOperation (Phase 1 refactoring)
        operation = CropInsertOperation()
        config = OptimizationConfig()
        context = {"candidates": candidates, "config": config}
        
        # Generate crop insert neighbors
        neighbors = operation.generate_neighbors(solution, context)
        
        # Should generate neighbors with inserted allocations
        assert len(neighbors) == 2  # Both unused candidates can be inserted
        
        # Check that neighbors have more allocations
        for neighbor in neighbors:
            assert len(neighbor) == 2  # Original + 1 inserted

    def test_crop_change_maintains_area(self):
        """Test that crop change maintains area equivalence."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        tomato = Crop("tomato", "Tomato", 0.3, revenue_per_area=60000.0)
        
        # Current: Rice
        alloc = CropAllocation(
            allocation_id="alloc_1",
            field=field,
            crop=rice,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
            expected_revenue=25000000.0,  # 500 × 50000
            profit=24235000.0,
        )
        
        solution = [alloc]
        
        # Candidate for Tomato on same field
        candidate_tomato = AllocationCandidate(
            field=field,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 7, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            area_used=1000.0,
        )
        
        candidates = [candidate_tomato]
        crops = [rice, tomato]
        
        # Use CropChangeOperation (Phase 1 refactoring)
        operation = CropChangeOperation()
        context = {"candidates": candidates, "crops": crops}
        
        # Generate crop change neighbors
        neighbors = operation.generate_neighbors(solution, context)
        
        # Should generate neighbor with changed crop
        assert len(neighbors) == 1
        
        new_alloc = neighbors[0][0]
        
        # Crop should be changed
        assert new_alloc.crop.crop_id == "tomato"
        
        # Area should be maintained (500m²)
        assert new_alloc.area_used == pytest.approx(500.0, rel=0.01)

    def test_all_operations_generate_valid_neighbors(self):
        """Test that all operations generate valid neighbor solutions."""
        # Setup
        field_a = Field("f1", "Field A", 1000.0, 5000.0)
        field_b = Field("f2", "Field B", 1000.0, 6000.0)
        
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        tomato = Crop("tomato", "Tomato", 0.3, revenue_per_area=60000.0)
        
        alloc_a = CropAllocation(
            allocation_id="alloc_a",
            field=field_a,
            crop=rice,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
            expected_revenue=25000000.0,  # 500 × 50000
            profit=24235000.0,
        )
        
        solution = [alloc_a]
        
        # Create candidates
        candidates = [
            AllocationCandidate(
                field=field_a,
                crop=rice,
                start_date=datetime(2025, 4, 15),
                completion_date=datetime(2025, 9, 15),
                growth_days=154,
                accumulated_gdd=1820.0,
                area_used=500.0,
            ),
            AllocationCandidate(
                field=field_b,
                crop=rice,
                start_date=datetime(2025, 4, 1),
                completion_date=datetime(2025, 8, 31),
                growth_days=153,
                accumulated_gdd=1800.0,
                area_used=1000.0,
            ),
            AllocationCandidate(
                field=field_a,
                crop=tomato,
                start_date=datetime(2025, 9, 1),
                completion_date=datetime(2025, 12, 31),
                growth_days=122,
                accumulated_gdd=1500.0,
                area_used=1000.0,
            ),
        ]
        
        fields = [field_a, field_b]
        crops = [rice, tomato]
        
        # Use NeighborGeneratorService (Phase 1 refactoring)
        config = OptimizationConfig(enable_neighbor_sampling=False)
        interactor = MultiFieldCropAllocationGreedyInteractor(None, None, None, config=config)
        
        # Generate all neighbors using NeighborGeneratorService
        neighbors = interactor.neighbor_generator.generate_neighbors(
            solution=solution,
            candidates=candidates,
            fields=fields,
            crops=crops,
        )
        
        # Should generate multiple neighbors from different operations
        assert len(neighbors) > 0
        
        # All neighbors should be valid (list of allocations)
        for neighbor in neighbors:
            assert isinstance(neighbor, list)
            for alloc in neighbor:
                assert isinstance(alloc, CropAllocation)

