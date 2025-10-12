"""Tests for CropAllocation entity."""

import pytest
from datetime import datetime

from agrr_core.entity.entities.crop_allocation_entity import CropAllocation
from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop


class TestCropAllocationEntity:
    """Test CropAllocation entity."""

    def test_creation_with_valid_parameters(self):
        """Test creating a valid crop allocation."""
        field = Field(
            field_id="field_001",
            name="田んぼ1号",
            area=1000.0,
            daily_fixed_cost=5000.0,
        )
        crop = Crop(
            crop_id="rice",
            name="Rice",
            area_per_unit=0.25,
            variety="Koshihikari",
            revenue_per_area=50000.0,
        )
        
        allocation = CropAllocation(
            allocation_id="alloc_001",
            field=field,
            crop=crop,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,  # 153 days × 5000
            expected_revenue=25000000.0,  # 500 × 50000
            profit=24235000.0,
        )
        
        assert allocation.allocation_id == "alloc_001"
        assert allocation.field == field
        assert allocation.crop == crop
        assert allocation.area_used == 500.0
        assert allocation.growth_days == 153
        assert allocation.profit == 24235000.0

    def test_profit_rate_calculation(self):
        """Test profit rate property."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("rice", "Rice", 0.25, revenue_per_area=50000.0)
        
        allocation = CropAllocation(
            allocation_id="alloc_001",
            field=field,
            crop=crop,
            area_used=250.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=100000.0,
            expected_revenue=12500000.0,  # 250 × 50000
            profit=12400000.0,
        )
        
        # Profit rate = profit / cost = 12400000 / 100000 = 124.0 (12400%)
        assert allocation.profit_rate == 124.0

    def test_field_utilization_rate(self):
        """Test field utilization rate calculation."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("rice", "Rice", 0.25)
        
        allocation = CropAllocation(
            allocation_id="alloc_001",
            field=field,
            crop=crop,
            area_used=500.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
        )
        
        # Utilization = 500 / 1000 = 50%
        assert allocation.field_utilization_rate == 50.0

    def test_overlaps_with_same_field(self):
        """Test time overlap detection for same field."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop1 = Crop("rice", "Rice", 0.25)
        crop2 = Crop("tomato", "Tomato", 0.3)
        
        alloc1 = CropAllocation(
            allocation_id="alloc_001",
            field=field,
            crop=crop1,
            area_used=250.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
        )
        
        # Overlapping allocation
        alloc2 = CropAllocation(
            allocation_id="alloc_002",
            field=field,
            crop=crop2,
            area_used=300.0,
            start_date=datetime(2025, 6, 1),  # Overlaps with alloc1
            completion_date=datetime(2025, 10, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
        )
        
        assert alloc1.overlaps_with(alloc2)
        assert alloc2.overlaps_with(alloc1)

    def test_no_overlap_different_fields(self):
        """Test that allocations in different fields don't overlap."""
        field1 = Field("f1", "Field 1", 1000.0, 5000.0)
        field2 = Field("f2", "Field 2", 1500.0, 6000.0)
        crop = Crop("rice", "Rice", 0.25)
        
        alloc1 = CropAllocation(
            allocation_id="alloc_001",
            field=field1,
            crop=crop,
            area_used=250.0,
            start_date=datetime(2025, 4, 1),
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=765000.0,
        )
        
        alloc2 = CropAllocation(
            allocation_id="alloc_002",
            field=field2,  # Different field
            crop=crop,
            area_used=250.0,
            start_date=datetime(2025, 4, 1),  # Same period
            completion_date=datetime(2025, 8, 31),
            growth_days=153,
            accumulated_gdd=1800.0,
            total_cost=918000.0,
        )
        
        # Different fields, so no overlap
        assert not alloc1.overlaps_with(alloc2)

    def test_invalid_area_used(self):
        """Test that negative area_used raises error."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("rice", "Rice", 0.25)
        
        with pytest.raises(ValueError, match="area_used must be positive"):
            CropAllocation(
                allocation_id="alloc_001",
                field=field,
                crop=crop,
                area_used=-25.0,  # Invalid
                start_date=datetime(2025, 4, 1),
                completion_date=datetime(2025, 8, 31),
                growth_days=153,
                accumulated_gdd=1800.0,
                total_cost=765000.0,
            )

    def test_invalid_dates(self):
        """Test that completion_date before start_date raises error."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("rice", "Rice", 0.25)
        
        with pytest.raises(ValueError, match="completion_date .* must be after"):
            CropAllocation(
                allocation_id="alloc_001",
                field=field,
                crop=crop,
                area_used=250.0,
                start_date=datetime(2025, 8, 31),
                completion_date=datetime(2025, 4, 1),  # Before start_date
                growth_days=153,
                accumulated_gdd=1800.0,
                total_cost=765000.0,
            )

    def test_area_exceeds_field_area(self):
        """Test that area_used exceeding field area raises error."""
        field = Field("f1", "Field 1", 1000.0, 5000.0)
        crop = Crop("rice", "Rice", 0.25)
        
        with pytest.raises(ValueError, match="area_used .* exceeds field area"):
            CropAllocation(
                allocation_id="alloc_001",
                field=field,
                crop=crop,
                area_used=2000.0,  # Exceeds field.area (1000.0)
                start_date=datetime(2025, 4, 1),
                completion_date=datetime(2025, 8, 31),
                growth_days=153,
                accumulated_gdd=1800.0,
                total_cost=765000.0,
            )

