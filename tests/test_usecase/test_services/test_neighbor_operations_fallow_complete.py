"""Complete test coverage for fallow period constraints in all neighbor operations.

This test ensures ALL neighbor operations properly consider fallow periods.
"""

import pytest
from datetime import datetime, timedelta

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.neighbor_operations.field_swap_operation import FieldSwapOperation
from agrr_core.usecase.services.neighbor_operations.crop_change_operation import CropChangeOperation
from agrr_core.usecase.dto.optimization_config import OptimizationConfig

@pytest.fixture
def field_a_with_fallow():
    """Field A with 28-day fallow period."""
    return Field(
        field_id="field_a",
        name="Field A",
        area=1000.0,
        daily_fixed_cost=5000.0,
        location="Test",
        fallow_period_days=28
    )

@pytest.fixture
def field_b_with_fallow():
    """Field B with 28-day fallow period."""
    return Field(
        field_id="field_b",
        name="Field B",
        area=1000.0,
        daily_fixed_cost=5000.0,
        location="Test",
        fallow_period_days=28
    )

@pytest.fixture
def crop_tomato():
    """Tomato crop."""
    return Crop(
        crop_id="tomato",
        name="Tomato",
        area_per_unit=1.0,
        variety="Variety A",
        revenue_per_area=10000.0,
        max_revenue=None,
        groups=["Solanaceae"]
    )

@pytest.fixture
def crop_lettuce():
    """Lettuce crop."""
    return Crop(
        crop_id="lettuce",
        name="Lettuce",
        area_per_unit=1.0,
        variety="Variety B",
        revenue_per_area=12000.0,
        max_revenue=None,
        groups=["Asteraceae"]
    )

@pytest.fixture
def crop_carrot():
    """Carrot crop."""
    return Crop(
        crop_id="carrot",
        name="Carrot",
        area_per_unit=1.0,
        variety="Variety C",
        revenue_per_area=8000.0,
        max_revenue=None,
        groups=["Apiaceae"]
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

class TestFieldSwapOperationFallowPeriod:
    """Test FieldSwapOperation respects fallow period."""
    
    def test_swap_violates_fallow_in_target_field_should_fail(
        self, field_a_with_fallow, field_b_with_fallow, crop_tomato, crop_lettuce
    ):
        """Test that field swap is rejected when it violates fallow period in target field.
        
        Scenario:
        Field A:
        - Alloc1 (Tomato): Apr 1 - Jun 30
        - (We want to swap Alloc1 to Field B)
        
        Field B:
        - Alloc2 (Lettuce): May 1 - Jul 31 (existing)
        - (If we swap Alloc1 here, it would overlap with Alloc2 + fallow period)
        
        Expected: Swap should check fallow period and reject if violation
        """
        # Field A: Alloc1 (Tomato, Apr 1 - Jun 30)
        alloc1 = CropAllocation(
            allocation_id="alloc_01",
            field=field_a_with_fallow,
            crop=crop_tomato,
            area_used=500.0,
            start_date=datetime(2024, 4, 1),
            completion_date=datetime(2024, 6, 30),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=5000000.0,
            profit=4550000.0
        )
        
        # Field B: Alloc2 (Lettuce, May 1 - Jul 31)
        alloc2 = CropAllocation(
            allocation_id="alloc_02",
            field=field_b_with_fallow,
            crop=crop_lettuce,
            area_used=500.0,
            start_date=datetime(2024, 5, 1),
            completion_date=datetime(2024, 7, 31),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=6000000.0,
            profit=5550000.0
        )
        
        solution = [alloc1, alloc2]
        
        # Execute swap operation
        operation = FieldSwapOperation()
        neighbors = operation.generate_neighbors(solution, {})
        
        # Check if any neighbor violates fallow period
        for neighbor in neighbors:
            # Group by field
            field_allocations = {}
            for alloc in neighbor:
                if alloc.field.field_id not in field_allocations:
                    field_allocations[alloc.field.field_id] = []
                field_allocations[alloc.field.field_id].append(alloc)
            
            # Check for violations in each field
            for field_id, allocs in field_allocations.items():
                for i, a1 in enumerate(allocs):
                    for a2 in allocs[i+1:]:
                        if a1.overlaps_with_fallow(a2):
                            pytest.fail(
                                f"Field swap generated neighbor that violates fallow period! "
                                f"Field {field_id}: Alloc1 ({a1.start_date} - {a1.completion_date}), "
                                f"Alloc2 ({a2.start_date} - {a2.completion_date}), "
                                f"fallow: {a1.field.fallow_period_days} days"
                            )

class TestCropChangeOperationFallowPeriod:
    """Test CropChangeOperation respects fallow period."""
    
    def test_crop_change_violates_fallow_should_fail(
        self, field_a_with_fallow, crop_tomato, crop_lettuce, crop_carrot
    ):
        """Test that crop change is rejected when new period violates fallow.
        
        Scenario:
        Field A:
        - Alloc1 (Tomato): Apr 1 - Jun 30
        - Alloc2 (Lettuce): Oct 1 - Dec 31
        
        Change Alloc2's crop to Carrot with period: Jul 1 - Sep 30
        This would violate fallow period from Alloc1 (Jun 30 + 28 days = Jul 28)
        
        Expected: Crop change should check fallow and reject if violation
        """
        # Field A allocations
        alloc1 = CropAllocation(
            allocation_id="alloc_01",
            field=field_a_with_fallow,
            crop=crop_tomato,
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
            field=field_a_with_fallow,
            crop=crop_lettuce,
            area_used=500.0,
            start_date=datetime(2024, 10, 1),
            completion_date=datetime(2024, 12, 31),
            growth_days=90,
            accumulated_gdd=1000.0,
            total_cost=450000.0,
            expected_revenue=6000000.0,
            profit=5550000.0
        )
        
        solution = [alloc1, alloc2]
        
        # Candidate: Carrot in Field A (Jul 1 - Sep 30) - violates fallow
        candidate_carrot = MockCandidate(
            field=field_a_with_fallow,
            crop=crop_carrot,
            start_date=datetime(2024, 7, 1),  # Too early!
            completion_date=datetime(2024, 9, 30),
            area_used=500.0
        )
        
        # Execute crop change operation
        operation = CropChangeOperation()
        context = {
            "candidates": [candidate_carrot],
            "crops": [crop_tomato, crop_lettuce, crop_carrot]
        }
        
        neighbors = operation.generate_neighbors(solution, context)
        
        # Check if any neighbor violates fallow period
        for neighbor in neighbors:
            # Group by field
            field_allocations = {}
            for alloc in neighbor:
                if alloc.field.field_id not in field_allocations:
                    field_allocations[alloc.field.field_id] = []
                field_allocations[alloc.field.field_id].append(alloc)
            
            # Check for violations in each field
            for field_id, allocs in field_allocations.items():
                for i, a1 in enumerate(allocs):
                    for a2 in allocs[i+1:]:
                        if a1.overlaps_with_fallow(a2):
                            pytest.fail(
                                f"Crop change generated neighbor that violates fallow period! "
                                f"Field {field_id}: Alloc1 ({a1.crop.name}: {a1.start_date} - {a1.completion_date}), "
                                f"Alloc2 ({a2.crop.name}: {a2.start_date} - {a2.completion_date}), "
                                f"fallow: {a1.field.fallow_period_days} days"
                            )

