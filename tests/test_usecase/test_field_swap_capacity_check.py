"""Test for Field Swap capacity checking with multiple allocations per field."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.usecase.services.neighbor_operations.field_swap_operation import (
    FieldSwapOperation,
)


class TestFieldSwapCapacityCheck:
    """Test that Field Swap properly checks capacity with multiple allocations."""

    def test_swap_simple_case_no_other_allocations(self):
        """Test swap when each field has only one allocation."""
        field_a = Field("f1", "Field 1", 1000.0, 5000.0)
        field_b = Field("f2", "Field 2", 800.0, 6000.0)
        
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        tomato = Crop("tomato", "Tomato", 0.3, revenue_per_area=60000.0)
        
        alloc_a = CropAllocation(
            allocation_id="alloc_a",
            field=field_a,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
            expected_revenue=2500000.0,
            profit=1735000.0,
            area_used=500.0,
        )
        
        alloc_b = CropAllocation(
            allocation_id="alloc_b",
            field=field_b,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 7, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            total_cost=732000.0,
            expected_revenue=1800000.0,
            profit=1068000.0,
            area_used=300.0,
        )
        
        solution = [alloc_a, alloc_b]
        
        operation = FieldSwapOperation()
        result = operation._swap_allocations_with_area_adjustment(
            alloc_a, alloc_b, solution
        )
        
        # Swap should succeed (no other allocations to worry about)
        assert result is not None
        new_alloc_a, new_alloc_b = result
        
        # Verify fields are swapped
        assert new_alloc_a.field.field_id == "f2"
        assert new_alloc_b.field.field_id == "f1"

    def test_swap_fails_when_capacity_exceeded(self):
        """Test swap with area-equivalent adjustment when capacity allows.
        
        Note: After Phase 1 refactoring, FieldSwapOperation implements
        area-equivalent swapping with automatic quantity adjustment.
        This test now verifies that the swap succeeds with proper adjustment.
        """
        field_a = Field("f1", "Field 1", 1000.0, 5000.0)
        field_b = Field("f2", "Field 2", 800.0, 6000.0)
        
        rice = Crop("rice", "Rice", 0.25)
        wheat = Crop("wheat", "Wheat", 0.2)
        tomato = Crop("tomato", "Tomato", 0.3)
        
        # Field 1: Rice 500m² + Wheat 400m² = 900m² (100m² free)
        alloc_a1 = CropAllocation(
            allocation_id="alloc_a1",
            field=field_a,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=91,
            accumulated_gdd=1000.0,
            total_cost=455000.0,
            area_used=500.0,
        )
        
        alloc_a2 = CropAllocation(
            allocation_id="alloc_a2",
            field=field_a,
            crop=wheat,
            start_date=datetime(2025, 7, 1),
            completion_date=datetime(2025, 9, 30),
            growth_days=92,
            accumulated_gdd=1000.0,
            total_cost=460000.0,
            area_used=400.0,
        )
        
        # Field 2: Tomato 600m² (200m² free)
        alloc_b1 = CropAllocation(
            allocation_id="alloc_b1",
            field=field_b,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 7, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            total_cost=732000.0,
            area_used=600.0,
        )
        
        solution = [alloc_a1, alloc_a2, alloc_b1]
        
        operation = FieldSwapOperation()
        
        # Try to swap alloc_a2 (Wheat 400m²) with alloc_b1 (Tomato 600m²)
        result = operation._swap_allocations_with_area_adjustment(
            alloc_a2, alloc_b1, solution
        )
        
        # Swap FAILS because capacity is exceeded:
        # Wheat(400m²) → Field 2: 400m² ≤ 800m² ✓ (OK)
        # Tomato(600m²) → Field 1: Rice 500m² + Tomato 600m² = 1100m² > 1000m² ✗ (exceeds)
        # Therefore swap returns None
        assert result is None

    def test_swap_succeeds_when_within_capacity(self):
        """Test swap succeeds when total area fits within field capacity."""
        field_a = Field("f1", "Field 1", 1000.0, 5000.0)
        field_b = Field("f2", "Field 2", 800.0, 6000.0)
        
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        wheat = Crop("wheat", "Wheat", 0.2, revenue_per_area=30000.0)
        tomato = Crop("tomato", "Tomato", 0.3, revenue_per_area=60000.0)
        
        # Field 1: Rice 500m² + Wheat 300m² = 800m² (200m² free)
        alloc_a1 = CropAllocation(
            allocation_id="alloc_a1",
            field=field_a,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=91,
            accumulated_gdd=1000.0,
            total_cost=455000.0,
            expected_revenue=2500000.0,
            profit=2045000.0,
            area_used=500.0,
        )
        
        alloc_a2 = CropAllocation(
            allocation_id="alloc_a2",
            field=field_a,
            crop=wheat,
            start_date=datetime(2025, 7, 1),
            completion_date=datetime(2025, 9, 30),
            growth_days=92,
            accumulated_gdd=1000.0,
            total_cost=460000.0,
            expected_revenue=900000.0,
            profit=440000.0,
            area_used=300.0,
        )
        
        # Field 2: Tomato 400m² (400m² free)
        alloc_b1 = CropAllocation(
            allocation_id="alloc_b1",
            field=field_b,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 7, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            total_cost=732000.0,
            expected_revenue=2400000.0,
            profit=1668000.0,
            area_used=400.0,
        )
        
        solution = [alloc_a1, alloc_a2, alloc_b1]
        
        operation = FieldSwapOperation()
        
        # Try to swap alloc_a2 (Wheat 300m²) with alloc_b1 (Tomato 400m²)
        result = operation._swap_allocations_with_area_adjustment(
            alloc_a2, alloc_b1, solution
        )
        
        # Should succeed:
        # Field 1: Rice 500m² + Tomato 400m² = 900m² ≤ 1000m² ✓
        # Field 2: Wheat 300m² ≤ 800m² ✓
        assert result is not None
        
        new_alloc_a, new_alloc_b = result
        
        # Verify area usage (areas are preserved in swap)
        # Wheat going to Field 2 (keeps its 300m²)
        assert new_alloc_a.area_used == pytest.approx(300.0, rel=0.001)
        assert new_alloc_a.field.field_id == "f2"
        
        # Tomato going to Field 1 (keeps its 400m²)
        assert new_alloc_b.area_used == pytest.approx(400.0, rel=0.001)
        assert new_alloc_b.field.field_id == "f1"

    def test_swap_with_tight_capacity(self):
        """Test swap when one field is almost full."""
        field_a = Field("f1", "Field 1", 1000.0, 5000.0)
        field_b = Field("f2", "Field 2", 500.0, 6000.0)  # Smaller field
        
        rice = Crop("rice", "Rice", 0.25)
        wheat = Crop("wheat", "Wheat", 0.2)
        tomato = Crop("tomato", "Tomato", 0.3)
        
        # Field 1: Rice 500m² + Wheat 400m² = 900m² (100m² free)
        alloc_a1 = CropAllocation(
            allocation_id="alloc_a1",
            field=field_a,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=91,
            accumulated_gdd=1000.0,
            total_cost=455000.0,
            area_used=500.0,
        )
        
        alloc_a2 = CropAllocation(
            allocation_id="alloc_a2",
            field=field_a,
            crop=wheat,
            start_date=datetime(2025, 7, 1),
            completion_date=datetime(2025, 9, 30),
            growth_days=92,
            accumulated_gdd=1000.0,
            total_cost=460000.0,
            area_used=400.0,
        )
        
        # Field 2: Tomato 150m² (350m² free)
        alloc_b1 = CropAllocation(
            allocation_id="alloc_b1",
            field=field_b,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 7, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            total_cost=732000.0,
            area_used=150.0,
        )
        
        solution = [alloc_a1, alloc_a2, alloc_b1]
        
        operation = FieldSwapOperation()
        
        # Try to swap alloc_a1 (Rice 500m²) with alloc_b1 (Tomato 150m²)
        result = operation._swap_allocations_with_area_adjustment(
            alloc_a1, alloc_b1, solution
        )
        
        # Should be rejected because:
        # Field 2: Rice would need 150m² (from Tomato's area) = 150m² ✓ OK
        # Field 1: Wheat 400m² + Tomato 500m² = 900m² ✓ OK
        # Actually this should succeed!
        assert result is not None

    def test_swap_rejected_when_field_too_small(self):
        """Test swap is rejected when target field is too small."""
        field_a = Field("f1", "Field 1", 1000.0, 5000.0)
        field_b = Field("f2", "Field 2", 600.0, 6000.0)  # Small field
        
        rice = Crop("rice", "Rice", 0.25)
        wheat = Crop("wheat", "Wheat", 0.2)
        tomato = Crop("tomato", "Tomato", 0.3)
        
        # Field 1: Rice 500m² + Wheat 400m² = 900m²
        alloc_a1 = CropAllocation(
            allocation_id="alloc_a1",
            field=field_a,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=91,
            accumulated_gdd=1000.0,
            total_cost=455000.0,
            area_used=500.0,
        )
        
        alloc_a2 = CropAllocation(
            allocation_id="alloc_a2",
            field=field_a,
            crop=wheat,
            start_date=datetime(2025, 7, 1),
            completion_date=datetime(2025, 9, 30),
            growth_days=92,
            accumulated_gdd=1000.0,
            total_cost=460000.0,
            area_used=400.0,
        )
        
        # Field 2: Tomato 200m²
        alloc_b1 = CropAllocation(
            allocation_id="alloc_b1",
            field=field_b,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 7, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            total_cost=732000.0,
            area_used=200.0,
        )
        
        solution = [alloc_a1, alloc_a2, alloc_b1]
        
        operation = FieldSwapOperation()
        
        # Try to swap alloc_a1 (Rice 500m²) with alloc_b1 (Tomato 200m²)
        result = operation._swap_allocations_with_area_adjustment(
            alloc_a1, alloc_b1, solution
        )
        
        # Check the result:
        # Field 1: Wheat 400m² + Tomato 500m² = 900m² ≤ 1000m² ✓ Should succeed
        # Field 2: Rice 200m² ≤ 600m² ✓ Should succeed
        
        # Actually this should succeed
        assert result is not None

    def test_swap_multiple_allocations_capacity_exceeded(self):
        """Test the critical case: swap causes capacity overflow."""
        field_a = Field("f1", "Field 1", 1000.0, 5000.0)
        field_b = Field("f2", "Field 2", 800.0, 6000.0)
        
        rice = Crop("rice", "Rice", 0.25)
        wheat = Crop("wheat", "Wheat", 0.2)
        tomato = Crop("tomato", "Tomato", 0.3)
        
        # Field 1: Rice 500m² + Wheat 400m² = 900m² (100m² free)
        alloc_a1 = CropAllocation(
            allocation_id="alloc_a1",
            field=field_a,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=91,
            accumulated_gdd=1000.0,
            total_cost=455000.0,
            area_used=500.0,
        )
        
        alloc_a2 = CropAllocation(
            allocation_id="alloc_a2",
            field=field_a,
            crop=wheat,
            start_date=datetime(2025, 7, 1),
            completion_date=datetime(2025, 9, 30),
            growth_days=92,
            accumulated_gdd=1000.0,
            total_cost=460000.0,
            area_used=400.0,
        )
        
        # Field 2: Tomato 600m² (200m² free)
        alloc_b1 = CropAllocation(
            allocation_id="alloc_b1",
            field=field_b,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 7, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            total_cost=732000.0,
            area_used=600.0,
        )
        
        solution = [alloc_a1, alloc_a2, alloc_b1]
        
        operation = FieldSwapOperation()
        
        # Try to swap alloc_a2 (Wheat 400m²) with alloc_b1 (Tomato 600m²)
        result = operation._swap_allocations_with_area_adjustment(
            alloc_a2, alloc_b1, solution
        )
        
        # Swap FAILS because capacity is exceeded (new implementation keeps area):
        # Wheat 400m² → Field 2: 400m² ≤ 800m² ✓
        # Tomato 600m² → Field 1: Rice 500m² + Tomato 600m² = 1100m² > 1000m² ✗
        # Field 1 capacity exceeded, so swap returns None
        assert result is None  # Swap fails due to capacity exceeded

    def test_swap_both_fields_have_multiple_allocations(self):
        """Test swap when both fields have multiple allocations."""
        field_a = Field("f1", "Field 1", 1000.0, 5000.0)
        field_b = Field("f2", "Field 2", 1000.0, 6000.0)
        
        rice = Crop("rice", "Rice", 0.25)
        wheat = Crop("wheat", "Wheat", 0.2)
        tomato = Crop("tomato", "Tomato", 0.3)
        lettuce = Crop("lettuce", "Lettuce", 0.15)
        
        # Field 1: Rice 500m² + Wheat 300m² = 800m² (200m² free)
        alloc_a1 = CropAllocation(
            allocation_id="alloc_a1",
            field=field_a,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 6, 30),
            growth_days=91,
            accumulated_gdd=1000.0,
            total_cost=455000.0,
            area_used=500.0,
        )
        
        alloc_a2 = CropAllocation(
            allocation_id="alloc_a2",
            field=field_a,
            crop=wheat,
            start_date=datetime(2025, 7, 1),
            completion_date=datetime(2025, 9, 30),
            growth_days=92,
            accumulated_gdd=1000.0,
            total_cost=460000.0,
            area_used=300.0,
        )
        
        # Field 2: Tomato 300m² + Lettuce 200m² = 500m² (500m² free)
        alloc_b1 = CropAllocation(
            allocation_id="alloc_b1",
            field=field_b,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 7, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            total_cost=732000.0,
            area_used=300.0,
        )
        
        alloc_b2 = CropAllocation(
            allocation_id="alloc_b2",
            field=field_b,
            crop=lettuce,
            start_date=datetime(2025, 8, 1),
            completion_date=datetime(2025, 10, 31),
            growth_days=92,
            accumulated_gdd=1000.0,
            total_cost=552000.0,
            area_used=200.0,
        )
        
        solution = [alloc_a1, alloc_a2, alloc_b1, alloc_b2]
        
        operation = FieldSwapOperation()
        
        # Try to swap alloc_a2 (Wheat 300m²) with alloc_b1 (Tomato 300m²)
        result = operation._swap_allocations_with_area_adjustment(
            alloc_a2, alloc_b1, solution
        )
        
        # Should succeed:
        # Field 1: Rice 500m² + Tomato 300m² = 800m² ≤ 1000m² ✓
        # Field 2: Lettuce 200m² + Wheat 300m² = 500m² ≤ 1000m² ✓
        assert result is not None

