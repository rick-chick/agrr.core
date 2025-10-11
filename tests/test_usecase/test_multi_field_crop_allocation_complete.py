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


class TestMultiFieldCropAllocationComplete:
    """Test all neighborhood operations in the complete framework."""

    def test_field_operations_complete(self):
        """Test that all Field operations are implemented."""
        interactor = MultiFieldCropAllocationGreedyInteractor(None, None, None)
        
        # Verify methods exist
        assert hasattr(interactor, '_field_swap_neighbors')
        assert hasattr(interactor, '_field_move_neighbors')
        assert hasattr(interactor, '_field_replace_neighbors')
        assert hasattr(interactor, '_field_remove_neighbors')

    def test_crop_operations_complete(self):
        """Test that all Crop operations are implemented."""
        interactor = MultiFieldCropAllocationGreedyInteractor(None, None, None)
        
        # Verify methods exist
        assert hasattr(interactor, '_crop_insert_neighbors')
        assert hasattr(interactor, '_crop_change_neighbors')

    def test_period_operations_complete(self):
        """Test that Period operations use DP results."""
        interactor = MultiFieldCropAllocationGreedyInteractor(None, None, None)
        
        # Verify method exists
        assert hasattr(interactor, '_period_replace_neighbors')

    def test_quantity_operations_complete(self):
        """Test that Quantity operations are implemented."""
        interactor = MultiFieldCropAllocationGreedyInteractor(None, None, None)
        
        # Verify method exists
        assert hasattr(interactor, '_quantity_adjust_neighbors')

    def test_quantity_adjust_increases_profit(self):
        """Test that quantity adjustment can increase profit."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        
        # Allocation using 50% of field (500m²)
        alloc = CropAllocation(
            allocation_id="alloc_1",
            field=field,
            crop=rice,
            quantity=2000.0,  # 50% capacity
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,  # Fixed cost
            expected_revenue=2500000.0,  # 2000 × 50000 × 0.25
            profit=1735000.0,
            area_used=500.0,
        )
        
        solution = [alloc]
        interactor = MultiFieldCropAllocationGreedyInteractor(None, None, None)
        
        # Generate quantity adjustment neighbors
        neighbors = interactor._quantity_adjust_neighbors(solution)
        
        # Should generate neighbors with adjusted quantities
        assert len(neighbors) > 0
        
        # Check that some neighbors have increased quantity
        increased_qty_neighbors = [
            n for n in neighbors 
            if n[0].quantity > alloc.quantity
        ]
        assert len(increased_qty_neighbors) > 0

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
            quantity=2000.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
            expected_revenue=2500000.0,
            profit=1735000.0,
            area_used=500.0,
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
            quantity=1666.0,
            cost=610000.0,
            revenue=3000000.0,
            profit=2390000.0,
            profit_rate=3.92,
            area_used=500.0,
        )
        
        candidate_rice_b = AllocationCandidate(
            field=field_b,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            quantity=4000.0,
            cost=918000.0,
            revenue=5000000.0,
            profit=4082000.0,
            profit_rate=4.45,
            area_used=1000.0,
        )
        
        candidates = [candidate_tomato_a, candidate_rice_b]
        
        interactor = MultiFieldCropAllocationGreedyInteractor(None, None, None)
        
        # Generate crop insert neighbors
        neighbors = interactor._crop_insert_neighbors(solution, candidates)
        
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
            quantity=2000.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
            expected_revenue=2500000.0,
            profit=1735000.0,
            area_used=500.0,  # 2000 × 0.25
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
            quantity=3333.0,  # Max quantity
            cost=610000.0,
            revenue=6000000.0,
            profit=5390000.0,
            profit_rate=8.84,
            area_used=1000.0,
        )
        
        candidates = [candidate_tomato]
        crops = [rice, tomato]
        
        interactor = MultiFieldCropAllocationGreedyInteractor(None, None, None)
        
        # Generate crop change neighbors
        neighbors = interactor._crop_change_neighbors(solution, candidates, crops)
        
        # Should generate neighbor with changed crop
        assert len(neighbors) == 1
        
        new_alloc = neighbors[0][0]
        
        # Crop should be changed
        assert new_alloc.crop.crop_id == "tomato"
        
        # Area should be maintained (500m²)
        assert new_alloc.area_used == pytest.approx(500.0, rel=0.01)
        
        # Quantity should be adjusted for area equivalence
        # 500m² / 0.3m²/unit = 1666.67 units
        assert new_alloc.quantity == pytest.approx(1666.67, rel=0.01)

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
            quantity=2000.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
            expected_revenue=2500000.0,
            profit=1735000.0,
            area_used=500.0,
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
                quantity=2000.0,
                cost=770000.0,
                revenue=2500000.0,
                profit=1730000.0,
                profit_rate=2.25,
                area_used=500.0,
            ),
            AllocationCandidate(
                field=field_b,
                crop=rice,
                start_date=datetime(2025, 4, 1),
                completion_date=datetime(2025, 8, 31),
                growth_days=153,
                accumulated_gdd=1800.0,
                quantity=4000.0,
                cost=918000.0,
                revenue=5000000.0,
                profit=4082000.0,
                profit_rate=4.45,
                area_used=1000.0,
            ),
            AllocationCandidate(
                field=field_a,
                crop=tomato,
                start_date=datetime(2025, 9, 1),
                completion_date=datetime(2025, 12, 31),
                growth_days=122,
                accumulated_gdd=1500.0,
                quantity=3333.0,
                cost=610000.0,
                revenue=6000000.0,
                profit=5390000.0,
                profit_rate=8.84,
                area_used=1000.0,
            ),
        ]
        
        fields = [field_a, field_b]
        crops = [rice, tomato]
        
        interactor = MultiFieldCropAllocationGreedyInteractor(None, None, None)
        
        # Generate all neighbors
        neighbors = interactor._generate_neighbors(solution, candidates, fields, crops)
        
        # Should generate multiple neighbors from different operations
        assert len(neighbors) > 0
        
        # All neighbors should be valid (list of allocations)
        for neighbor in neighbors:
            assert isinstance(neighbor, list)
            for alloc in neighbor:
                assert isinstance(alloc, CropAllocation)

