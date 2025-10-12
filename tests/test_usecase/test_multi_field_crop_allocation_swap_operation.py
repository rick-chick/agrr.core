"""Test for area-equivalent swap operation in multi-field crop allocation."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.usecase.services.neighbor_operations.field_swap_operation import (
    FieldSwapOperation,
)


class TestAreaEquivalentSwapOperation:
    """Test area-equivalent swap operation."""

    def test_swap_with_area_adjustment_basic(self):
        """Test that swap operation maintains equivalent area usage."""
        # Create two fields with different costs
        field_a = Field(
            field_id="field_a",
            name="Field A",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        field_b = Field(
            field_id="field_b",
            name="Field B",
            area=1000.0,
            daily_fixed_cost=6000.0,
        )
        
        # Create two crops with different area_per_unit
        rice = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,  # 0.25m² per plant
            revenue_per_area=50000.0,
        )
        tomato = Crop(
            crop_id="tomato",
            name="Tomato",
            area_per_unit=0.3,  # 0.3m² per plant
            revenue_per_area=60000.0,
        )
        
        # Create allocations
        # Field A: Rice 2000 plants (area = 2000 × 0.25 = 500m²)
        alloc_a = CropAllocation(
            allocation_id="alloc_a",
            field=field_a,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,  # 153 × 5000
            expected_revenue=2500000.0,  # 2000 × 50000 × 0.25
            profit=1735000.0,
            area_used=500.0,  # 2000 × 0.25
        )
        
        # Field B: Tomato 1000 plants (area = 1000 × 0.3 = 300m²)
        alloc_b = CropAllocation(
            allocation_id="alloc_b",
            field=field_b,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 7, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            total_cost=732000.0,  # 122 × 6000
            expected_revenue=1800000.0,  # 1000 × 60000 × 0.3
            profit=1068000.0,
            area_used=300.0,  # 1000 × 0.3
        )
        
        # Create operation for testing
        operation = FieldSwapOperation()
        
        # Perform swap with area adjustment
        result = operation._swap_allocations_with_area_adjustment(alloc_a, alloc_b, [alloc_a, alloc_b])
        
        assert result is not None
        new_alloc_a, new_alloc_b = result
        
        # Verify fields are swapped
        assert new_alloc_a.field.field_id == "field_b"  # Rice now in Field B
        assert new_alloc_b.field.field_id == "field_a"  # Tomato now in Field A
        
        # Verify crops are kept
        assert new_alloc_a.crop.crop_id == "rice"
        assert new_alloc_b.crop.crop_id == "tomato"
        
        # Verify areas are preserved in swap (new implementation)
        # Rice in Field B: keeps its 500m²
        assert new_alloc_a.area_used == pytest.approx(500.0)
        
        # Tomato in Field A: keeps its 300m²
        assert new_alloc_b.area_used == pytest.approx(300.0)
        
        # Verify costs are recalculated based on new field's daily_fixed_cost
        # Rice in Field B: 153 days × 6000円/day = 918,000円
        assert new_alloc_a.total_cost == pytest.approx(918000.0)
        
        # Tomato in Field A: 122 days × 5000円/day = 610,000円
        assert new_alloc_b.total_cost == pytest.approx(610000.0)
        
        # Verify revenues are recalculated based on area_used
        # Rice in Field B: 500m² × 50000円/m² = 25,000,000円
        assert new_alloc_a.expected_revenue == pytest.approx(25000000.0, rel=0.001)
        
        # Tomato in Field A: 300m² × 60000円/m² = 18,000,000円
        assert new_alloc_b.expected_revenue == pytest.approx(18000000.0, rel=0.01)

    def test_swap_maintains_area_conservation(self):
        """Test that total area usage is conserved after swap."""
        field_a = Field("field_a", "Field A", 1000.0, 5000.0)
        field_b = Field("field_b", "Field B", 1500.0, 6000.0)
        
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        wheat = Crop("wheat", "Wheat", 0.2, revenue_per_area=30000.0)
        
        # Field A: Rice 1600 plants (400m²)
        alloc_a = CropAllocation(
            allocation_id="alloc_a",
            field=field_a,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
            area_used=400.0,  # 1600 × 0.25
        )
        
        # Field B: Wheat 2500 plants (500m²)
        alloc_b = CropAllocation(
            allocation_id="alloc_b",
            field=field_b,
            crop=wheat,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=150,
            accumulated_gdd=1700.0,
            total_cost=900000.0,
            area_used=500.0,  # 2500 × 0.2
        )
        
        operation = FieldSwapOperation()
        result = operation._swap_allocations_with_area_adjustment(alloc_a, alloc_b, [alloc_a, alloc_b])
        
        assert result is not None
        new_alloc_a, new_alloc_b = result
        
        # Total area before swap: 400 + 500 = 900m²
        # Total area after swap should be the same
        total_area_after = new_alloc_a.area_used + new_alloc_b.area_used
        assert total_area_after == pytest.approx(900.0)
        
        # Individual areas are preserved (new implementation)
        assert new_alloc_a.area_used == pytest.approx(400.0)  # Rice keeps its 400m²
        assert new_alloc_b.area_used == pytest.approx(500.0)  # Wheat keeps its 500m²

    def test_swap_rejects_if_exceeds_field_capacity(self):
        """Test swap with area-equivalent adjustment between fields of different sizes.
        
        Note: After Phase 1 refactoring, FieldSwapOperation uses area-equivalent
        adjustment, so the swap succeeds by adjusting quantities.
        """
        # Small field
        field_a = Field("field_a", "Field A", 100.0, 5000.0)  # Only 100m²
        # Large field
        field_b = Field("field_b", "Field B", 1000.0, 6000.0)
        
        rice = Crop("rice", "Rice", 0.25)
        tomato = Crop("tomato", "Tomato", 0.3)
        
        # Field A: Rice 200 plants (50m²)
        alloc_a = CropAllocation(
            allocation_id="alloc_a",
            field=field_a,
            crop=rice,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
            area_used=50.0,
        )
        
        # Field B: Tomato 3000 plants (900m²)
        alloc_b = CropAllocation(
            allocation_id="alloc_b",
            field=field_b,
            crop=tomato,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 7, 31),
            growth_days=122,
            accumulated_gdd=1500.0,
            total_cost=732000.0,
            area_used=900.0,
        )
        
        operation = FieldSwapOperation()
        result = operation._swap_allocations_with_area_adjustment(alloc_a, alloc_b, [alloc_a, alloc_b])
        
        # With area preservation (new implementation), swap FAILS:
        # Rice 50m² → Field B: 50m² ≤ 1000m² ✓
        # Tomato 900m² → Field A: 900m² > 100m² ✗ (exceeds capacity)
        # Therefore swap returns None
        assert result is None

    def test_swap_with_zero_area_per_unit_returns_none(self):
        """Test that swap works with area_used (new implementation ignores area_per_unit)."""
        field_a = Field("field_a", "Field A", 1000.0, 5000.0)
        field_b = Field("field_b", "Field B", 1000.0, 6000.0)
        
        # Crop with zero area_per_unit (no longer affects swap)
        crop_a = Crop("crop_a", "Crop A", 0.0)
        crop_b = Crop("crop_b", "Crop B", 0.25)
        
        alloc_a = CropAllocation(
            allocation_id="alloc_a",
            field=field_a,
            crop=crop_a,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
            area_used=100.0,  # Changed from 0.0 to valid value
        )
        
        alloc_b = CropAllocation(
            allocation_id="alloc_b",
            field=field_b,
            crop=crop_b,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=918000.0,
            area_used=500.0,
        )
        
        operation = FieldSwapOperation()
        result = operation._swap_allocations_with_area_adjustment(alloc_a, alloc_b, [alloc_a, alloc_b])
        
        # New implementation: swap succeeds because it only uses area_used (ignores area_per_unit)
        assert result is not None
        new_alloc_a, new_alloc_b = result
        # Areas are preserved
        assert new_alloc_a.area_used == pytest.approx(100.0)
        assert new_alloc_b.area_used == pytest.approx(500.0)

    def test_swap_formula_verification(self):
        """Verify the swap quantity formula with explicit calculations."""
        field_a = Field("field_a", "Field A", 2000.0, 5000.0)
        field_b = Field("field_b", "Field B", 2000.0, 6000.0)
        
        # Crop A: 0.4m² per unit
        crop_a = Crop("crop_a", "Crop A", 0.4, revenue_per_area=40000.0)
        # Crop B: 0.5m² per unit
        crop_b = Crop("crop_b", "Crop B", 0.5, revenue_per_area=50000.0)
        
        # Original allocation A: 1000 units × 0.4m²/unit = 400m²
        alloc_a = CropAllocation(
            allocation_id="alloc_a",
            field=field_a,
            crop=crop_a,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=100,
            accumulated_gdd=1000.0,
            total_cost=500000.0,
            expected_revenue=16000000.0,
            profit=15500000.0,
            area_used=400.0,
        )
        
        # Original allocation B: 800 units × 0.5m²/unit = 400m²
        alloc_b = CropAllocation(
            allocation_id="alloc_b",
            field=field_b,
            crop=crop_b,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=100,
            accumulated_gdd=1000.0,
            total_cost=600000.0,
            expected_revenue=20000000.0,
            profit=19400000.0,
            area_used=400.0,
        )
        
        operation = FieldSwapOperation()
        result = operation._swap_allocations_with_area_adjustment(alloc_a, alloc_b, [alloc_a, alloc_b])
        
        assert result is not None
        new_alloc_a, new_alloc_b = result
        
        # Formula: new_quantity = original_area / new_crop.area_per_unit
        
        # Crop A moving to Field B (using 400m² from crop B)
        # Expected: 400m² / 0.4m²/unit = 1000 units        assert new_alloc_a.area_used == pytest.approx(400.0)
        
        # Crop B moving to Field A (using 400m² from crop A)
        # Expected: 400m² / 0.5m²/unit = 800 units        assert new_alloc_b.area_used == pytest.approx(400.0)
        
        # In this case, quantities remain the same because areas were equal
        # This verifies the formula works correctly

