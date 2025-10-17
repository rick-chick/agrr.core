"""Field schedule entity.

Represents the complete cultivation schedule for a single field,
including all crop allocations over time.

This entity aggregates allocations and provides summary statistics
for a field's utilization and profitability.

Fields:
- field: Field entity
- allocations: List of crop allocations for this field
- total_area_used: Total area used (considering all allocations)
- total_cost: Sum of all allocation costs
- total_revenue: Sum of all allocation revenues
- total_profit: Sum of all allocation profits
- utilization_rate: Field utilization rate as percentage
"""

from dataclasses import dataclass
from typing import List

from agrr_core.entity.entities.field_entity import Field
from agrr_core.entity.entities.crop_allocation_entity import CropAllocation


@dataclass(frozen=True)
class FieldSchedule:
    """Represents the complete cultivation schedule for a single field."""

    field: Field
    allocations: List[CropAllocation]
    total_area_used: float
    total_cost: float
    total_revenue: float
    total_profit: float
    utilization_rate: float

    def __post_init__(self):
        """Validate field schedule invariants."""
        if self.total_area_used < 0:
            raise ValueError(f"total_area_used must be non-negative, got {self.total_area_used}")
        
        if self.total_cost < 0:
            raise ValueError(f"total_cost must be non-negative, got {self.total_cost}")
        
        if self.total_revenue < 0:
            raise ValueError(f"total_revenue must be non-negative, got {self.total_revenue}")
        
        # Note: utilization_rate can exceed 100% when multiple crops are grown sequentially
        # (time-integrated utilization), so we only check for non-negative
        if self.utilization_rate < 0:
            raise ValueError(f"utilization_rate must be non-negative, got {self.utilization_rate}")
        
        # Verify all allocations belong to this field
        for allocation in self.allocations:
            if allocation.field.field_id != self.field.field_id:
                raise ValueError(
                    f"Allocation {allocation.allocation_id} belongs to field {allocation.field.field_id}, "
                    f"not {self.field.field_id}"
                )
        
        # Verify no time overlaps between allocations (including fallow period)
        for i, alloc1 in enumerate(self.allocations):
            for alloc2 in self.allocations[i + 1:]:
                if alloc1.overlaps_with_fallow(alloc2):
                    raise ValueError(
                        f"Allocations {alloc1.allocation_id} and {alloc2.allocation_id} overlap "
                        f"(considering {alloc1.field.fallow_period_days}-day fallow period)"
                    )

    @property
    def allocation_count(self) -> int:
        """Return the number of allocations in this schedule."""
        return len(self.allocations)

    @property
    def crop_diversity(self) -> int:
        """Return the number of unique crops in this schedule."""
        return len(set(alloc.crop.crop_id for alloc in self.allocations))

    @property
    def average_profit_per_allocation(self) -> float:
        """Calculate average profit per allocation."""
        if not self.allocations:
            return 0.0
        return self.total_profit / len(self.allocations)

