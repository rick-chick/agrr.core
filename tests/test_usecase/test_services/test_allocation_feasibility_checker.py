"""Tests for AllocationFeasibilityChecker."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.allocation_feasibility_checker import (
    AllocationFeasibilityChecker,
)

@pytest.mark.unit
class TestIsFeasible:
    """Tests for is_feasible method."""
    
    def test_is_feasible_empty_solution(self):
        """Test that empty solution is feasible."""
        checker = AllocationFeasibilityChecker()
        assert checker.is_feasible([]) is True
    
    def test_is_feasible_single_allocation(self):
        """Test that single allocation is always feasible."""
        checker = AllocationFeasibilityChecker()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=15000.0,
            expected_revenue=250000.0,
            profit=235000.0,
            area_used=250.0,
        )
        
        assert checker.is_feasible([alloc]) is True
    
    def test_is_feasible_non_overlapping_allocations(self):
        """Test feasible solution with non-overlapping allocations."""
        checker = AllocationFeasibilityChecker()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,            start_date=datetime(2024, 7, 1),  # After alloc1
            completion_date=datetime(2024, 9, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        assert checker.is_feasible([alloc1, alloc2]) is True
    
    def test_is_feasible_overlapping_allocations(self):
        """Test infeasible solution with overlapping allocations."""
        checker = AllocationFeasibilityChecker()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,            start_date=datetime(2024, 6, 1),  # Overlaps with alloc1
            completion_date=datetime(2024, 9, 30),
            growth_days=120,
            accumulated_gdd=1200.0,
            total_cost=12000.0,
            expected_revenue=250000.0,
            profit=238000.0,
            area_used=250.0,
        )
        
        assert checker.is_feasible([alloc1, alloc2]) is False
    
    def test_is_feasible_different_fields_can_overlap(self):
        """Test that allocations in different fields can overlap in time."""
        checker = AllocationFeasibilityChecker()
        
        field1 = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        field2 = Field("f2", "Field 2", 800.0, 4500.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field2,  # Different field
            crop=crop,            start_date=datetime(2024, 5, 1),  # Overlaps in time
            completion_date=datetime(2024, 7, 31),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=200000.0,
            profit=191000.0,
            area_used=200.0,
        )
        
        assert checker.is_feasible([alloc1, alloc2]) is True

@pytest.mark.unit
class TestCheckTimeConstraints:
    """Tests for _check_time_constraints method."""
    
    def test_check_time_constraints_no_overlap(self):
        """Test time constraints check with non-overlapping allocations."""
        checker = AllocationFeasibilityChecker()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 3, 31),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        assert checker._check_time_constraints([alloc1, alloc2]) is True
    
    def test_check_time_constraints_with_overlap(self):
        """Test time constraints check with overlapping allocations."""
        checker = AllocationFeasibilityChecker()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,            start_date=datetime(2024, 6, 1),  # Overlaps
            completion_date=datetime(2024, 9, 30),
            growth_days=120,
            accumulated_gdd=1200.0,
            total_cost=12000.0,
            expected_revenue=250000.0,
            profit=238000.0,
            area_used=250.0,
        )
        
        assert checker._check_time_constraints([alloc1, alloc2]) is False

@pytest.mark.unit
class TestCheckAreaConstraints:
    """Tests for _check_area_constraints method."""
    
    def test_check_area_constraints_within_capacity(self):
        """Test area constraints when within field capacity."""
        checker = AllocationFeasibilityChecker()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        # Two allocations using 500m² total (< 1000m²)
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 3, 31),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        assert checker._check_area_constraints([alloc1, alloc2]) is True
    
    def test_check_area_constraints_exceeds_capacity(self):
        """Test area constraints when exceeding field capacity."""
        checker = AllocationFeasibilityChecker()
        
        field = Field("f1", "Field 1", 500.0, 5000.0, fallow_period_days=0)  # Small field
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        # Two allocations using 600m² total (> 500m²)
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,            start_date=datetime(2024, 1, 1),
            completion_date=datetime(2024, 3, 31),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=300000.0,
            profit=291000.0,
            area_used=300.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=300000.0,
            profit=291000.0,
            area_used=300.0,
        )
        
        assert checker._check_area_constraints([alloc1, alloc2]) is False
    
    def test_check_area_constraints_at_capacity(self):
        """Test that allocations at exactly field capacity pass."""
        checker = AllocationFeasibilityChecker()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        # Allocation using exactly 1000m² (100% of capacity)
        alloc = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=15000.0,
            expected_revenue=1000000.0,
            profit=985000.0,
            area_used=1000.0,  # Exactly at capacity
        )
        
        # Should pass
        assert checker._check_area_constraints([alloc]) is True
    
    def test_check_area_constraints_multiple_fields(self):
        """Test area constraints across multiple fields."""
        checker = AllocationFeasibilityChecker()
        
        field1 = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        field2 = Field("f2", "Field 2", 800.0, 4500.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=15000.0,
            expected_revenue=750000.0,
            profit=735000.0,
            area_used=750.0,  # 75% of field1
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field2,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=15000.0,
            expected_revenue=600000.0,
            profit=585000.0,
            area_used=600.0,  # 75% of field2
        )
        
        assert checker._check_area_constraints([alloc1, alloc2]) is True

@pytest.mark.unit
class TestComplexScenarios:
    """Tests for complex feasibility scenarios."""
    
    def test_multiple_crops_same_field_sequential(self):
        """Test feasibility with multiple crops in same field sequentially."""
        checker = AllocationFeasibilityChecker()
        
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        rice = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        wheat = Crop("wheat", "Wheat", 0.3, revenue_per_area=8000.0)
        
        # Rice in spring
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=rice,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 7, 31),
            growth_days=120,
            accumulated_gdd=1200.0,
            total_cost=12000.0,
            expected_revenue=500000.0,
            profit=488000.0,
            area_used=500.0,
        )
        
        # Wheat in autumn (after rice)
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=wheat,            start_date=datetime(2024, 8, 1),
            completion_date=datetime(2024, 11, 30),
            growth_days=120,
            accumulated_gdd=1100.0,
            total_cost=12000.0,
            expected_revenue=400000.0,
            profit=388000.0,
            area_used=500.0,
        )
        
        assert checker.is_feasible([alloc1, alloc2]) is True
    
    def test_multiple_fields_same_time(self):
        """Test feasibility with same time period across different fields."""
        checker = AllocationFeasibilityChecker()
        
        field1 = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        field2 = Field("f2", "Field 2", 800.0, 4500.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        # Same time period but different fields
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field1,
            crop=crop,            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=15000.0,
            expected_revenue=500000.0,
            profit=485000.0,
            area_used=500.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field2,  # Different field
            crop=crop,            start_date=datetime(2024, 4, 1),  # Same time
            completion_date=datetime(2024, 8, 31),
            growth_days=150,
            accumulated_gdd=1500.0,
            total_cost=15000.0,
            expected_revenue=400000.0,
            profit=385000.0,
            area_used=400.0,
        )
        
        assert checker.is_feasible([alloc1, alloc2]) is True

@pytest.mark.unit
class TestFallowPeriodConstraints:
    """Tests for fallow period constraint validation."""
    
    def test_is_feasible_with_fallow_period_no_overlap(self):
        """Test that allocations respect fallow period when they don't overlap."""
        checker = AllocationFeasibilityChecker()
        
        # Field with 28-day fallow period
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=28)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        # First allocation ends June 30
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        # Second allocation starts July 29 (28 days after June 30 + 1 day)
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,
            start_date=datetime(2024, 7, 29),  # Respects 28-day fallow
            completion_date=datetime(2024, 10, 31),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        assert checker.is_feasible([alloc1, alloc2]) is True
    
    def test_is_feasible_with_fallow_period_overlap(self):
        """Test that allocations violating fallow period are infeasible."""
        checker = AllocationFeasibilityChecker()
        
        # Field with 28-day fallow period
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=28)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        # First allocation ends June 30
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        # Second allocation starts July 15 (violates 28-day fallow)
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,
            start_date=datetime(2024, 7, 15),  # Too soon! Needs to wait until July 29
            completion_date=datetime(2024, 10, 31),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        assert checker.is_feasible([alloc1, alloc2]) is False
    
    def test_is_feasible_with_zero_fallow_period(self):
        """Test that zero fallow period allows immediate sequential planting."""
        checker = AllocationFeasibilityChecker()
        
        # Field with no fallow period
        field = Field("f1", "Field 1", 1000.0, 5000.0, fallow_period_days=0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
        
        # First allocation ends June 30
        alloc1 = CropAllocation(
            allocation_id="alloc1",
            field=field,
            crop=crop,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        # Second allocation can start immediately on July 1
        alloc2 = CropAllocation(
            allocation_id="alloc2",
            field=field,
            crop=crop,
            start_date=datetime(2024, 7, 1),  # No fallow needed
            completion_date=datetime(2024, 9, 30),
            growth_days=90,
            accumulated_gdd=900.0,
            total_cost=9000.0,
            expected_revenue=250000.0,
            profit=241000.0,
            area_used=250.0,
        )
        
        assert checker.is_feasible([alloc1, alloc2]) is True

