"""Crop allocation entity.

Represents a single allocation decision: which crop to plant, in which field,
when to start, and how much area to use.

This is a core entity for multi-field, multi-crop optimization.

Fields:
- allocation_id: Unique identifier for this allocation
- field: Field entity where the crop is allocated
- crop: Crop entity to be planted
- area_used: Field area used by this allocation (m²)
- start_date: Cultivation start date
- completion_date: Date when cultivation completes (harvest date)
- growth_days: Number of days from start to completion
- accumulated_gdd: Total accumulated growing degree days
- total_cost: Total cost for this allocation (growth_days × field.daily_fixed_cost)
- expected_revenue: Expected revenue from this allocation (area_used × crop.revenue_per_area)
- profit: Expected profit (expected_revenue - total_cost)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop


@dataclass(frozen=True)
class CropAllocation:
    """Represents allocation of a specific crop to a specific field with timing and area."""

    allocation_id: str
    field: Field
    crop: Crop
    area_used: float
    start_date: datetime
    completion_date: datetime
    growth_days: int
    accumulated_gdd: float
    total_cost: float
    expected_revenue: Optional[float] = None
    profit: Optional[float] = None

    def __post_init__(self):
        """Validate allocation invariants."""
        if self.area_used <= 0:
            raise ValueError(f"area_used must be positive, got {self.area_used}")
        
        if self.growth_days < 0:
            raise ValueError(f"growth_days must be non-negative, got {self.growth_days}")
        
        if self.total_cost < 0:
            raise ValueError(f"total_cost must be non-negative, got {self.total_cost}")
        
        if self.accumulated_gdd < 0:
            raise ValueError(f"accumulated_gdd must be non-negative, got {self.accumulated_gdd}")
        
        if self.completion_date < self.start_date:
            raise ValueError(
                f"completion_date ({self.completion_date}) must be after or equal to start_date ({self.start_date})"
            )
        
        # Area check: ensure allocated area doesn't exceed field area
        if self.area_used > self.field.area:
            raise ValueError(
                f"area_used ({self.area_used}m²) exceeds field area ({self.field.area}m²)"
            )
        
        # Profit validation if both revenue and profit are provided
        if self.expected_revenue is not None and self.profit is not None:
            expected_profit = self.expected_revenue - self.total_cost
            if abs(self.profit - expected_profit) > 0.01:  # Allow small floating point error
                raise ValueError(
                    f"profit ({self.profit}) doesn't match revenue-cost ({expected_profit})"
                )

    @property
    def profit_rate(self) -> float:
        """Calculate profit rate (profit / cost).
        
        Returns:
            Profit rate as a percentage. Returns 0 if cost is 0.
        """
        if self.total_cost == 0:
            return 0.0
        return (self.profit / self.total_cost) if self.profit is not None else 0.0

    @property
    def field_utilization_rate(self) -> float:
        """Calculate how much of the field area is used by this allocation.
        
        Returns:
            Utilization rate as a percentage (0-100).
        """
        if self.field.area == 0:
            return 0.0
        return (self.area_used / self.field.area) * 100.0

    def overlaps_with(self, other: "CropAllocation") -> bool:
        """Check if this allocation overlaps in time with another allocation in the same field.
        
        Args:
            other: Another allocation to check overlap with
            
        Returns:
            True if allocations overlap in the same field, False otherwise
        """
        # Only check overlap if both allocations are in the same field
        if self.field.field_id != other.field.field_id:
            return False
        
        # Check time overlap: two intervals overlap if one starts before the other ends
        return not (self.completion_date < other.start_date or other.completion_date < self.start_date)

    def overlaps_with_fallow(self, other: "CropAllocation") -> bool:
        """Check if this allocation overlaps with another including fallow period.
        
        This method checks if two allocations violate the fallow period constraint.
        The fallow period is the required rest period for the soil after crop harvest.
        
        Args:
            other: Another allocation to check overlap with
            
        Returns:
            True if allocations overlap considering fallow period, False otherwise
            
        Example:
            If alloc1 completes on June 30 and field has 28-day fallow period,
            alloc2 must start on or after July 28.
        """
        from datetime import timedelta
        
        # Only check overlap if both allocations are in the same field
        if self.field.field_id != other.field.field_id:
            return False
        
        # Calculate end dates including fallow period
        self_end_with_fallow = self.completion_date + timedelta(
            days=self.field.fallow_period_days
        )
        other_end_with_fallow = other.completion_date + timedelta(
            days=other.field.fallow_period_days
        )
        
        # Check overlap with fallow periods included
        return not (self_end_with_fallow <= other.start_date or 
                    other_end_with_fallow <= self.start_date)

