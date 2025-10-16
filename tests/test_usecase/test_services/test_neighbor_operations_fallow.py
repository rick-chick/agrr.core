"""Test neighbor operations respect fallow period constraints.

This test ensures all neighbor operations (crop insert, period replace, etc.)
properly consider fallow periods when generating neighbors.
"""

import pytest
from datetime import datetime, timedelta

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.neighbor_operations.crop_insert_operation import CropInsertOperation
from agrr_core.usecase.services.neighbor_operations.period_replace_operation import PeriodReplaceOperation
from agrr_core.usecase.dto.optimization_config import OptimizationConfig


@pytest.fixture
def field_with_fallow():
    """Field with 28-day fallow period."""
    return Field(
        field_id="field_01",
        name="Test Field",
        area=1000.0,
        daily_fixed_cost=5000.0,
        location="Test",
        fallow_period_days=28
    )


@pytest.fixture
def crop_a():
    """Crop A."""
    return Crop(
        crop_id="crop_a",
        name="Crop A",
        area_per_unit=1.0,
        variety="Variety A",
        revenue_per_area=10000.0,
        max_revenue=None,
        groups=["GroupA"]
    )


@pytest.fixture
def crop_b():
    """Crop B."""
    return Crop(
        crop_id="crop_b",
        name="Crop B",
        area_per_unit=1.0,
        variety="Variety B",
        revenue_per_area=12000.0,
        max_revenue=None,
        groups=["GroupB"]
    )


class MockCandidate:
    """Mock allocation candidate."""
    def __init__(self, field, crop, start_date, completion_date, area_used=500.0):
        self.field = field
        self.crop = crop
        self.start_date = start_date
        self.completion_date = completion_date
        self.growth_days = (completion_date - start_date).days
        self.accumulated_gdd = 1000.0
        self.area_used = area_used
    
    @property
    def cost(self):
        return self.growth_days * self.field.daily_fixed_cost
    
    @property
    def revenue(self):
        return self.area_used * self.crop.revenue_per_area
    
    @property
    def profit(self):
        return self.revenue - self.cost


class TestCropInsertOperationFallowPeriod:
    """Test CropInsertOperation respects fallow period."""
    
    def test_insert_violates_fallow_period_should_be_rejected(
        self, field_with_fallow, crop_a, crop_b
    ):
        """Test that crop insert is rejected when it violates fallow period.
        
        Scenario:
        - Crop A: Apr 1 - Jun 30 (90 days)
        - Field fallow period: 28 days
        - Crop A ends with fallow: Jul 28
        - Candidate Crop B: Jul 1 - Sep 30 (violates fallow - starts before Jul 28)
        
        Expected: Crop B insert should be rejected
        """
        # Existing allocation: Crop A (Apr 1 - Jun 30)
        existing_alloc = CropAllocation(
            allocation_id="alloc_01",
            field=field_with_fallow,
            crop=crop_a,
            area_used=500.0,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=5000000.0,
            profit=4550000.0
        )
        
        # Candidate: Crop B (Jul 1 - Sep 30) - violates 28-day fallow period
        candidate = MockCandidate(
            field=field_with_fallow,
            crop=crop_b,
            start_date=datetime(2024, 7, 1),  # Too early! Should be Jul 28+
            completion_date=datetime(2024, 9, 30),
            area_used=500.0
        )
        
        # Execute operation
        operation = CropInsertOperation()
        solution = [existing_alloc]
        context = {
            "candidates": [candidate],
            "config": OptimizationConfig()
        }
        
        neighbors = operation.generate_neighbors(solution, context)
        
        # Verify: No neighbors should be generated (fallow period violation)
        assert len(neighbors) == 0, (
            "Crop insert should be rejected when it violates fallow period. "
            f"Crop A ends Jun 30 + 28 days fallow = Jul 28. "
            f"Candidate starts Jul 1 (too early!)"
        )
    
    def test_insert_respects_fallow_period_should_be_accepted(
        self, field_with_fallow, crop_a, crop_b
    ):
        """Test that crop insert is accepted when it respects fallow period.
        
        Scenario:
        - Crop A: Apr 1 - Jun 30 (90 days)
        - Field fallow period: 28 days
        - Crop A ends with fallow: Jul 28
        - Candidate Crop B: Jul 28 - Oct 31 (respects fallow)
        
        Expected: Crop B insert should be accepted
        """
        # Existing allocation: Crop A (Apr 1 - Jun 30)
        existing_alloc = CropAllocation(
            allocation_id="alloc_01",
            field=field_with_fallow,
            crop=crop_a,
            area_used=500.0,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=5000000.0,
            profit=4550000.0
        )
        
        # Candidate: Crop B (Jul 28 - Oct 31) - respects 28-day fallow period
        candidate = MockCandidate(
            field=field_with_fallow,
            crop=crop_b,
            start_date=datetime(2024, 7, 28),  # Correct! Jun 30 + 28 days
            completion_date=datetime(2024, 10, 31),
            area_used=500.0
        )
        
        # Execute operation
        operation = CropInsertOperation()
        solution = [existing_alloc]
        context = {
            "candidates": [candidate],
            "config": OptimizationConfig()
        }
        
        neighbors = operation.generate_neighbors(solution, context)
        
        # Verify: One neighbor should be generated (fallow period respected)
        assert len(neighbors) == 1, (
            "Crop insert should be accepted when it respects fallow period. "
            f"Crop A ends Jun 30 + 28 days fallow = Jul 28. "
            f"Candidate starts Jul 28 (correct!)"
        )
        
        # Verify the neighbor includes both allocations
        assert len(neighbors[0]) == 2
        assert neighbors[0][0] == existing_alloc
        assert neighbors[0][1].crop.crop_id == crop_b.crop_id


class TestPeriodReplaceOperationFallowPeriod:
    """Test PeriodReplaceOperation respects fallow period."""
    
    def test_period_replace_violates_fallow_should_be_rejected(
        self, field_with_fallow, crop_a, crop_b
    ):
        """Test that period replace is rejected when new period violates fallow.
        
        Scenario:
        - Existing allocations in same field:
          - Alloc 1 (Crop A): Apr 1 - Jun 30
          - Alloc 2 (Crop B): Aug 1 - Oct 31
        - Replace Alloc 2 period with: Jul 1 - Sep 30 (violates fallow from Alloc 1)
        
        Expected: Period replace should maintain fallow constraint check
        """
        # Existing allocations
        alloc1 = CropAllocation(
            allocation_id="alloc_01",
            field=field_with_fallow,
            crop=crop_a,
            area_used=500.0,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=5000000.0,
            profit=4550000.0
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc_02",
            field=field_with_fallow,
            crop=crop_b,
            area_used=500.0,
            start_date=datetime(2024, 8, 1),
            completion_date=datetime(2024, 10, 31),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=6000000.0,
            profit=5550000.0
        )
        
        # Candidate with bad period (Jul 1 - Sep 30) - violates fallow from alloc1
        bad_candidate = MockCandidate(
            field=field_with_fallow,
            crop=crop_b,
            start_date=datetime(2024, 7, 1),  # Too early!
            completion_date=datetime(2024, 9, 30),
            area_used=500.0
        )
        
        # Execute operation
        operation = PeriodReplaceOperation()
        solution = [alloc1, alloc2]
        context = {
            "candidates": [bad_candidate],
            "config": OptimizationConfig()
        }
        
        # Note: Current implementation doesn't check fallow period
        # This test documents the bug
        neighbors = operation.generate_neighbors(solution, context)
        
        # Current behavior: generates neighbor (BUG!)
        # Expected behavior after fix: should check fallow and reject
        
        # This test will FAIL initially (expected), then PASS after fix
        if len(neighbors) > 0:
            # If neighbor generated, it should NOT violate fallow period
            neighbor_alloc1 = neighbors[0][0]
            neighbor_alloc2 = neighbors[0][1]
            
            # Check fallow period violation
            violates_fallow = neighbor_alloc1.overlaps_with_fallow(neighbor_alloc2)
            
            pytest.fail(
                f"Period replace generated neighbor that violates fallow period! "
                f"Alloc1 ends {neighbor_alloc1.completion_date}, "
                f"Alloc2 starts {neighbor_alloc2.start_date}, "
                f"fallow period: {field_with_fallow.fallow_period_days} days"
            )

