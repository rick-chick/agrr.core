"""Test to verify that neighbor operations work correctly without unused calculations.

This test verifies that removing unused revenue/profit calculations from neighbor operations
does not change the behavior, since these values are recalculated in the main loop anyway.

Strategy:
1. Create test scenarios with specific allocations
2. Generate neighbors using each operation
3. Verify that the neighbor structure (number of neighbors, allocation IDs, dates, etc.) 
   remains the same before and after removing unused calculations
4. Note: We don't assert on revenue/profit values in the operations themselves,
   since those are expected to be recalculated by OptimizationMetrics later
"""

import pytest
from datetime import datetime, timedelta
import uuid

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.usecase.services.neighbor_operations.field_swap_operation import FieldSwapOperation
from agrr_core.usecase.services.neighbor_operations.crop_change_operation import CropChangeOperation
from agrr_core.usecase.services.neighbor_operations.period_replace_operation import PeriodReplaceOperation
from agrr_core.usecase.services.neighbor_operations.area_adjust_operation import AreaAdjustOperation
from agrr_core.usecase.services.neighbor_operations.field_move_operation import FieldMoveOperation
from agrr_core.usecase.dto.optimization_config import OptimizationConfig

@pytest.fixture
def field_a():
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
def field_b():
    """Field B with 28-day fallow period."""
    return Field(
        field_id="field_b",
        name="Field B",
        area=1000.0,
        daily_fixed_cost=6000.0,
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
    """Mock allocation candidate for testing."""
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
        if self.crop.revenue_per_area is not None:
            return self.area_used * self.crop.revenue_per_area
        return None
    
    @property
    def profit(self):
        if self.revenue is not None:
            return self.revenue - self.cost
        return None
    
    @property
    def profit_rate(self):
        if self.cost > 0:
            return self.profit / self.cost
        return 0.0

def create_allocation(field, crop, start_date, completion_date, area_used=500.0):
    """Helper to create a CropAllocation for testing."""
    growth_days = (completion_date - start_date).days
    cost = growth_days * field.daily_fixed_cost
    revenue = area_used * crop.revenue_per_area if crop.revenue_per_area else None
    profit = (revenue - cost) if revenue is not None else None
    
    return CropAllocation(
        allocation_id=str(uuid.uuid4()),
        field=field,
        crop=crop,
        area_used=area_used,
        start_date=start_date,
        completion_date=completion_date,
        growth_days=growth_days,
        accumulated_gdd=1000.0,
        total_cost=cost,
        expected_revenue=revenue,
        profit=profit,
    )

class TestFieldSwapOperation:
    """Test FieldSwapOperation neighbor generation."""
    
    def test_swap_generates_correct_number_of_neighbors(self, field_a, field_b, crop_tomato, crop_lettuce):
        """Test that swap operation generates the expected number of neighbors."""
        # Create two allocations in different fields
        alloc1 = create_allocation(
            field_a, crop_tomato,
            datetime(2024, 4, 1), datetime(2024, 6, 30),
            area_used=400.0
        )
        alloc2 = create_allocation(
            field_b, crop_lettuce,
            datetime(2024, 5, 1), datetime(2024, 7, 31),
            area_used=300.0
        )
        solution = [alloc1, alloc2]
        
        operation = FieldSwapOperation()
        neighbors = operation.generate_neighbors(solution, {})
        
        # Should generate 1 neighbor (swap alloc1 and alloc2)
        # BASELINE: Record current behavior
        assert len(neighbors) == 1
        assert len(neighbors[0]) == 2
        
        # Verify structure (not exact revenue/profit values)
        neighbor = neighbors[0]
        # First allocation should now be in field_b
        assert neighbor[0].field.field_id == field_b.field_id
        assert neighbor[0].crop.crop_id == crop_tomato.crop_id
        # Second allocation should now be in field_a
        assert neighbor[1].field.field_id == field_a.field_id
        assert neighbor[1].crop.crop_id == crop_lettuce.crop_id

class TestCropChangeOperation:
    """Test CropChangeOperation neighbor generation."""
    
    def test_crop_change_generates_neighbors_with_correct_structure(
        self, field_a, crop_tomato, crop_lettuce, crop_carrot
    ):
        """Test that crop change generates neighbors with correct structure."""
        # Create allocation
        alloc = create_allocation(
            field_a, crop_tomato,
            datetime(2024, 4, 1), datetime(2024, 6, 30),
            area_used=500.0
        )
        solution = [alloc]
        
        # Create candidates for different crops in same field
        candidates = [
            MockCandidate(field_a, crop_lettuce, datetime(2024, 4, 5), datetime(2024, 7, 5)),
            MockCandidate(field_a, crop_carrot, datetime(2024, 4, 10), datetime(2024, 7, 10)),
        ]
        
        crops = [crop_tomato, crop_lettuce, crop_carrot]
        context = {"candidates": candidates, "crops": crops}
        
        operation = CropChangeOperation()
        neighbors = operation.generate_neighbors(solution, context)
        
        # BASELINE: Should generate 2 neighbors (one for each alternative crop)
        assert len(neighbors) == 2
        
        # All neighbors should have same field but different crop
        for neighbor in neighbors:
            assert len(neighbor) == 1
            assert neighbor[0].field.field_id == field_a.field_id
            assert neighbor[0].crop.crop_id != crop_tomato.crop_id

class TestPeriodReplaceOperation:
    """Test PeriodReplaceOperation neighbor generation."""
    
    def test_period_replace_generates_neighbors_with_alternative_periods(
        self, field_a, crop_tomato
    ):
        """Test that period replace generates neighbors for alternative periods."""
        # Create allocation
        alloc = create_allocation(
            field_a, crop_tomato,
            datetime(2024, 4, 1), datetime(2024, 6, 30),
            area_used=500.0
        )
        solution = [alloc]
        
        # Create candidates with alternative periods for same field+crop
        candidates = [
            MockCandidate(field_a, crop_tomato, datetime(2024, 4, 1), datetime(2024, 6, 30)),  # Same (should be skipped)
            MockCandidate(field_a, crop_tomato, datetime(2024, 5, 1), datetime(2024, 7, 31)),  # Alternative 1
            MockCandidate(field_a, crop_tomato, datetime(2024, 5, 15), datetime(2024, 8, 15)), # Alternative 2
        ]
        
        config = OptimizationConfig(max_period_replace_alternatives=3)
        context = {"candidates": candidates, "config": config}
        
        operation = PeriodReplaceOperation()
        neighbors = operation.generate_neighbors(solution, context)
        
        # BASELINE: Should generate 2 neighbors (alternative periods, excluding same period)
        assert len(neighbors) == 2
        
        # All neighbors should have same field+crop but different dates
        for neighbor in neighbors:
            assert len(neighbor) == 1
            assert neighbor[0].field.field_id == field_a.field_id
            assert neighbor[0].crop.crop_id == crop_tomato.crop_id
            assert neighbor[0].start_date != alloc.start_date

class TestAreaAdjustOperation:
    """Test AreaAdjustOperation neighbor generation."""
    
    def test_area_adjust_generates_neighbors_with_different_areas(self, field_a, crop_tomato):
        """Test that area adjust generates neighbors with different areas."""
        # Create allocation
        alloc = create_allocation(
            field_a, crop_tomato,
            datetime(2024, 4, 1), datetime(2024, 6, 30),
            area_used=500.0
        )
        solution = [alloc]
        
        config = OptimizationConfig(area_adjustment_multipliers=[0.8, 1.2])
        context = {"config": config}
        
        operation = AreaAdjustOperation()
        neighbors = operation.generate_neighbors(solution, context)
        
        # BASELINE: Should generate 2 neighbors (0.8x and 1.2x)
        assert len(neighbors) == 2
        
        # Verify areas are adjusted
        areas = [neighbor[0].area_used for neighbor in neighbors]
        expected_areas = [500.0 * 0.8, 500.0 * 1.2]
        assert sorted(areas) == sorted(expected_areas)

class TestFieldMoveOperation:
    """Test FieldMoveOperation neighbor generation."""
    
    def test_field_move_generates_neighbors_to_different_fields(
        self, field_a, field_b, crop_tomato
    ):
        """Test that field move generates neighbors moving to different fields."""
        # Create allocation in field_a
        alloc = create_allocation(
            field_a, crop_tomato,
            datetime(2024, 4, 1), datetime(2024, 6, 30),
            area_used=400.0
        )
        solution = [alloc]
        
        # Create candidate for field_b with same crop
        candidates = [
            MockCandidate(field_b, crop_tomato, datetime(2024, 4, 5), datetime(2024, 7, 5), area_used=400.0),
        ]
        
        fields = [field_a, field_b]
        context = {"candidates": candidates, "fields": fields}
        
        operation = FieldMoveOperation()
        neighbors = operation.generate_neighbors(solution, context)
        
        # BASELINE: Should generate 1 neighbor (move to field_b)
        assert len(neighbors) == 1
        
        # Verify moved to field_b
        neighbor = neighbors[0]
        assert len(neighbor) == 1
        assert neighbor[0].field.field_id == field_b.field_id
        assert neighbor[0].crop.crop_id == crop_tomato.crop_id

class TestNeighborOperationsConsistency:
    """Integration test to verify neighbor operations produce consistent results."""
    
    def test_all_operations_generate_valid_neighbors(
        self, field_a, field_b, crop_tomato, crop_lettuce, crop_carrot
    ):
        """Test that all operations generate valid neighbor structures."""
        # Create a complex solution
        alloc1 = create_allocation(field_a, crop_tomato, datetime(2024, 4, 1), datetime(2024, 6, 30), 400.0)
        alloc2 = create_allocation(field_b, crop_lettuce, datetime(2024, 5, 1), datetime(2024, 7, 31), 300.0)
        solution = [alloc1, alloc2]
        
        # Create candidates
        candidates = [
            MockCandidate(field_a, crop_tomato, datetime(2024, 4, 1), datetime(2024, 6, 30)),
            MockCandidate(field_a, crop_lettuce, datetime(2024, 4, 5), datetime(2024, 7, 5)),
            MockCandidate(field_b, crop_tomato, datetime(2024, 5, 1), datetime(2024, 7, 31)),
            MockCandidate(field_b, crop_carrot, datetime(2024, 5, 10), datetime(2024, 8, 10)),
        ]
        
        crops = [crop_tomato, crop_lettuce, crop_carrot]
        fields = [field_a, field_b]
        config = OptimizationConfig()
        
        context = {
            "candidates": candidates,
            "crops": crops,
            "fields": fields,
            "config": config
        }
        
        # Test all operations
        operations = [
            ("FieldSwap", FieldSwapOperation()),
            ("CropChange", CropChangeOperation()),
            ("PeriodReplace", PeriodReplaceOperation()),
            ("AreaAdjust", AreaAdjustOperation()),
            ("FieldMove", FieldMoveOperation()),
        ]
        
        total_neighbors = 0
        for op_name, operation in operations:
            neighbors = operation.generate_neighbors(solution, context)
            total_neighbors += len(neighbors)
            
            # BASELINE: All neighbors should be valid
            for neighbor in neighbors:
                # Each neighbor should be a list of allocations
                assert isinstance(neighbor, list)
                # Each allocation should have required fields
                for alloc in neighbor:
                    assert hasattr(alloc, 'field')
                    assert hasattr(alloc, 'crop')
                    assert hasattr(alloc, 'start_date')
                    assert hasattr(alloc, 'completion_date')
                    assert hasattr(alloc, 'area_used')
                    # Note: We don't assert specific revenue/profit values
                    # because those are meant to be recalculated later
        
        # BASELINE: Total number of neighbors generated (current behavior)
        # This will vary based on the specific implementation
        # Recording the current value to detect changes
        assert total_neighbors > 0  # At least some neighbors should be generated
        print(f"\n📊 BASELINE: Total neighbors generated = {total_neighbors}")

