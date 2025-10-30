"""Unit tests for allocation utility functions."""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from agrr_core.usecase.services.allocation_utils import AllocationUtils
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop

class TestTimeOverlaps:
    """Test time overlap detection."""
    
    def test_overlapping_periods(self):
        """Test detection of overlapping periods."""
        start1 = datetime(2025, 1, 1)
        end1 = datetime(2025, 3, 1)
        start2 = datetime(2025, 2, 1)
        end2 = datetime(2025, 4, 1)
        
        assert AllocationUtils.time_overlaps(start1, end1, start2, end2) is True
    
    def test_non_overlapping_periods(self):
        """Test detection of non-overlapping periods."""
        start1 = datetime(2025, 1, 1)
        end1 = datetime(2025, 2, 1)
        start2 = datetime(2025, 3, 1)
        end2 = datetime(2025, 4, 1)
        
        assert AllocationUtils.time_overlaps(start1, end1, start2, end2) is False
    
    def test_adjacent_periods(self):
        """Test adjacent periods (end1 == start2).
        
        Note: In the current implementation, adjacent periods ARE considered
        overlapping because the check is: not (end1 < start2 or end2 < start1)
        When end1 == start2, end1 < start2 is False, so they overlap.
        
        This is intentional for crop allocation to avoid same-day conflicts.
        """
        start1 = datetime(2025, 1, 1)
        end1 = datetime(2025, 2, 1)
        start2 = datetime(2025, 2, 1)
        end2 = datetime(2025, 3, 1)
        
        # Adjacent periods DO overlap in current implementation
        assert AllocationUtils.time_overlaps(start1, end1, start2, end2) is True
    
    def test_contained_period(self):
        """Test period fully contained in another."""
        start1 = datetime(2025, 1, 1)
        end1 = datetime(2025, 4, 1)
        start2 = datetime(2025, 2, 1)
        end2 = datetime(2025, 3, 1)
        
        assert AllocationUtils.time_overlaps(start1, end1, start2, end2) is True

class TestAllocationOverlaps:
    """Test allocation overlap detection."""
    
    @pytest.fixture
    def mock_field(self):
        """Create mock field."""
        return Field(
            field_id='field1',
            name='Test Field',
            area=1000.0,
            daily_fixed_cost=100.0,
            location='Test Location',
        )
    
    @pytest.fixture
    def mock_crop(self):
        """Create mock crop."""
        return Crop(
            crop_id='crop1',
            name='Test Crop',
            area_per_unit=1.0,
            variety='Test Variety',
            revenue_per_area=1000.0,
        )
    
    def test_overlapping_allocations(self, mock_field, mock_crop):
        """Test detection of overlapping allocations."""
        alloc1 = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 3, 1),
            growth_days=60,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 2, 1),
            completion_date=datetime(2025, 4, 1),
            growth_days=60,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        assert AllocationUtils.allocation_overlaps(alloc1, alloc2) is True
    
    def test_non_overlapping_allocations(self, mock_field, mock_crop):
        """Test detection of non-overlapping allocations."""
        alloc1 = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 2, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 3, 1),
            completion_date=datetime(2025, 4, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        assert AllocationUtils.allocation_overlaps(alloc1, alloc2) is False

class TestIsFeasibleToAdd:
    """Test feasibility check."""
    
    @pytest.fixture
    def mock_field(self):
        return Field(
            field_id='field1',
            name='Test Field',
            area=1000.0,
            daily_fixed_cost=100.0,
            location='Test Location',
        )
    
    @pytest.fixture
    def mock_crop(self):
        return Crop(
            crop_id='crop1',
            name='Test Crop',
            area_per_unit=1.0,
            variety='Test Variety',
            revenue_per_area=1000.0,
        )
    
    def test_feasible_non_overlapping(self, mock_field, mock_crop):
        """Test feasibility with non-overlapping allocations."""
        alloc1 = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 2, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        new_alloc = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 3, 1),
            completion_date=datetime(2025, 4, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        assert AllocationUtils.is_feasible_to_add([alloc1], new_alloc) is True
    
    def test_not_feasible_overlapping(self, mock_field, mock_crop):
        """Test infeasibility with overlapping allocations."""
        alloc1 = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 3, 1),
            growth_days=60,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        new_alloc = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 2, 1),
            completion_date=datetime(2025, 4, 1),
            growth_days=60,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        assert AllocationUtils.is_feasible_to_add([alloc1], new_alloc) is False
    
    def test_feasible_different_fields(self, mock_crop):
        """Test feasibility with different fields (always feasible)."""
        field1 = Field(
            field_id='field1',
            name='Field 1',
            area=1000.0,
            daily_fixed_cost=100.0,
            location='Location 1',
        )
        
        field2 = Field(
            field_id='field2',
            name='Field 2',
            area=1000.0,
            daily_fixed_cost=100.0,
            location='Location 2',
        )
        
        alloc1 = CropAllocation(
            allocation_id=str(uuid4()),
            field=field1,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 3, 1),
            growth_days=60,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        new_alloc = CropAllocation(
            allocation_id=str(uuid4()),
            field=field2,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 2, 1),
            completion_date=datetime(2025, 4, 1),
            growth_days=60,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        # Different fields, so always feasible
        assert AllocationUtils.is_feasible_to_add([alloc1], new_alloc) is True

class TestCalculateFieldUsage:
    """Test field usage calculation."""
    
    @pytest.fixture
    def mock_field(self):
        return Field(
            field_id='field1',
            name='Test Field',
            area=1000.0,
            daily_fixed_cost=100.0,
            location='Test Location',
        )
    
    @pytest.fixture
    def mock_crop(self):
        return Crop(
            crop_id='crop1',
            name='Test Crop',
            area_per_unit=1.0,
            variety='Test Variety',
            revenue_per_area=1000.0,
        )
    
    def test_single_allocation(self, mock_field, mock_crop):
        """Test usage calculation with single allocation."""
        alloc = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 2, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        usage = AllocationUtils.calculate_field_usage([alloc])
        
        assert 'field1' in usage
        assert usage['field1']['used_area'] == 200.0
        assert usage['field1']['allocation_count'] == 1
        assert len(usage['field1']['allocations']) == 1
    
    def test_multiple_allocations(self, mock_field, mock_crop):
        """Test usage calculation with multiple allocations."""
        alloc1 = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 2, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=300.0,
            start_date=datetime(2025, 3, 1),
            completion_date=datetime(2025, 4, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=7500.0,
            expected_revenue=15000.0,
            profit=7500.0,
        )
        
        usage = AllocationUtils.calculate_field_usage([alloc1, alloc2])
        
        assert usage['field1']['used_area'] == 500.0
        assert usage['field1']['allocation_count'] == 2

class TestCalculateTotalProfit:
    """Test profit calculation."""
    
    @pytest.fixture
    def mock_field(self):
        return Field(
            field_id='field1',
            name='Test Field',
            area=1000.0,
            daily_fixed_cost=100.0,
            location='Test Location',
        )
    
    @pytest.fixture
    def mock_crop(self):
        return Crop(
            crop_id='crop1',
            name='Test Crop',
            area_per_unit=1.0,
            variety='Test Variety',
            revenue_per_area=1000.0,
        )
    
    def test_total_profit(self, mock_field, mock_crop):
        """Test total profit calculation."""
        alloc1 = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 2, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id=str(uuid4()),
            field=mock_field,
            crop=mock_crop,
            area_used=300.0,
            start_date=datetime(2025, 3, 1),
            completion_date=datetime(2025, 4, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=7500.0,
            expected_revenue=15000.0,
            profit=7500.0,
        )
        
        total_profit = AllocationUtils.calculate_total_profit([alloc1, alloc2])
        
        assert total_profit == 12500.0

class TestRemoveAllocations:
    """Test allocation removal."""
    
    @pytest.fixture
    def mock_field(self):
        return Field(
            field_id='field1',
            name='Test Field',
            area=1000.0,
            daily_fixed_cost=100.0,
            location='Test Location',
        )
    
    @pytest.fixture
    def mock_crop(self):
        return Crop(
            crop_id='crop1',
            name='Test Crop',
            area_per_unit=1.0,
            variety='Test Variety',
            revenue_per_area=1000.0,
        )
    
    def test_remove_allocations(self, mock_field, mock_crop):
        """Test removing specific allocations."""
        alloc1 = CropAllocation(
            allocation_id='alloc1',
            field=mock_field,
            crop=mock_crop,
            area_used=200.0,
            start_date=datetime(2025, 1, 1),
            completion_date=datetime(2025, 2, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=5000.0,
            expected_revenue=10000.0,
            profit=5000.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id='alloc2',
            field=mock_field,
            crop=mock_crop,
            area_used=300.0,
            start_date=datetime(2025, 3, 1),
            completion_date=datetime(2025, 4, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=7500.0,
            expected_revenue=15000.0,
            profit=7500.0,
        )
        
        alloc3 = CropAllocation(
            allocation_id='alloc3',
            field=mock_field,
            crop=mock_crop,
            area_used=100.0,
            start_date=datetime(2025, 5, 1),
            completion_date=datetime(2025, 6, 1),
            growth_days=31,
            accumulated_gdd=500.0,
            total_cost=2500.0,
            expected_revenue=5000.0,
            profit=2500.0,
        )
        
        solution = [alloc1, alloc2, alloc3]
        remaining = AllocationUtils.remove_allocations(solution, [alloc2])
        
        assert len(remaining) == 2
        assert alloc1 in remaining
        assert alloc2 not in remaining
        assert alloc3 in remaining

