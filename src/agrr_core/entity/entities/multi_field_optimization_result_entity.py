"""Multi-field optimization result entity.

Represents the complete optimization result across multiple fields,
including all field schedules and aggregate statistics.

This is the top-level entity that contains the final optimization solution.

Fields:
- optimization_id: Unique identifier for this optimization run
- field_schedules: List of field schedules (one per field)
- total_cost: Sum of all field costs
- total_revenue: Sum of all field revenues
- total_profit: Sum of all field profits
- crop_areas: Dictionary mapping crop_id to total area used (m²)
- optimization_time: Time taken to compute this solution (seconds)
- algorithm_used: Name of the algorithm used
- is_optimal: True if this is a proven optimal solution
"""

from dataclasses import dataclass
from typing import List, Dict

from agrr_core.entity.entities.field_schedule_entity import FieldSchedule


@dataclass(frozen=True)
class MultiFieldOptimizationResult:
    """Represents the complete optimization result across multiple fields."""

    optimization_id: str
    field_schedules: List[FieldSchedule]
    total_cost: float
    total_revenue: float
    total_profit: float
    crop_areas: Dict[str, float]
    optimization_time: float
    algorithm_used: str
    is_optimal: bool = False

    def __post_init__(self):
        """Validate optimization result invariants."""
        if self.total_cost < 0:
            raise ValueError(f"total_cost must be non-negative, got {self.total_cost}")
        
        if self.total_revenue < 0:
            raise ValueError(f"total_revenue must be non-negative, got {self.total_revenue}")
        
        if self.optimization_time < 0:
            raise ValueError(f"optimization_time must be non-negative, got {self.optimization_time}")
        
        # Verify crop areas are non-negative
        for crop_id, area in self.crop_areas.items():
            if area < 0:
                raise ValueError(f"crop_areas[{crop_id}] must be non-negative, got {area}")
        
        # Verify no duplicate fields
        field_ids = [schedule.field.field_id for schedule in self.field_schedules]
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("Duplicate fields found in field_schedules")

    @property
    def total_fields(self) -> int:
        """Return the total number of fields in this optimization."""
        return len(self.field_schedules)

    @property
    def total_allocations(self) -> int:
        """Return the total number of allocations across all fields."""
        return sum(schedule.allocation_count for schedule in self.field_schedules)

    @property
    def average_field_utilization(self) -> float:
        """Calculate average field utilization rate across all fields."""
        if not self.field_schedules:
            return 0.0
        return sum(schedule.utilization_rate for schedule in self.field_schedules) / len(self.field_schedules)

    @property
    def crop_diversity(self) -> int:
        """Return the total number of unique crops across all fields."""
        return len(self.crop_areas)

    @property
    def profit_rate(self) -> float:
        """Calculate overall profit rate (profit / cost)."""
        if self.total_cost == 0:
            return 0.0
        return self.total_profit / self.total_cost

