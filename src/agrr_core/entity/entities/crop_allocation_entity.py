"""Crop allocation entity.

Represents a single allocation decision: which crop to plant, in which field,
when to start, and how much to produce.

This is a core entity for multi-field, multi-crop optimization.

Fields:
- allocation_id: Unique identifier for this allocation
- field: Field entity where the crop is allocated
- crop: Crop entity to be planted
- quantity: Number of units to produce (e.g., number of plants)
- start_date: Cultivation start date
- completion_date: Date when cultivation completes (harvest date)
- growth_days: Number of days from start to completion
- accumulated_gdd: Total accumulated growing degree days
- total_cost: Total cost for this allocation (growth_days × field.daily_fixed_cost)
- expected_revenue: Expected revenue from this allocation (quantity × crop.revenue_per_area × crop.area_per_unit)
- profit: Expected profit (expected_revenue - total_cost)
- area_used: Field area used by this allocation (quantity × crop.area_per_unit)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_entity import Crop


@dataclass(frozen=True)
class CropAllocation:
    """Represents allocation of a specific crop to a specific field with timing and quantity."""

    allocation_id: str
    field: Field
    crop: Crop
    quantity: float
    start_date: datetime
    completion_date: datetime
    growth_days: int
    accumulated_gdd: float
    total_cost: float
    expected_revenue: Optional[float] = None
    profit: Optional[float] = None
    area_used: float = 0.0

    def __post_init__(self):
        """Validate allocation invariants."""
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive, got {self.quantity}")
        
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
        
        if self.area_used < 0:
            raise ValueError(f"area_used must be non-negative, got {self.area_used}")
        
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

