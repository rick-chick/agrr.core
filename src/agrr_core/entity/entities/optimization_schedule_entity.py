"""Optimization schedule entity.

Represents optimization results with optional schedule metadata.
This entity serves as a unified container for both:
- Intermediate optimization results (total_cost = None)
- Scheduled non-overlapping periods (total_cost = float)

Fields
- schedule_id: Unique identifier for this optimization result/schedule
- selected_results: List of optimization intermediate results
- total_cost: Total cost of all selected results (None for intermediate results, float for schedules)
"""

from dataclasses import dataclass
from typing import List, Optional

from agrr_core.entity.entities.optimization_intermediate_result_entity import (
    OptimizationIntermediateResult,
)

@dataclass(frozen=True)
class OptimizationSchedule:
    """Unified entity for optimization results and schedules.
    
    This entity can represent:
    1. Intermediate optimization results (total_cost = None)
    2. Scheduled non-overlapping periods (total_cost = float)
    """

    schedule_id: str
    selected_results: List[OptimizationIntermediateResult]
    total_cost: Optional[float] = None

    def __post_init__(self):
        """Validate invariants."""
        if not self.schedule_id:
            raise ValueError("schedule_id must not be empty")
        
        if not isinstance(self.selected_results, list):
            raise TypeError(
                f"selected_results must be a list, got {type(self.selected_results).__name__}"
            )
        
        if self.total_cost is not None and self.total_cost < 0.0:
            raise ValueError(
                f"total_cost must be non-negative, got {self.total_cost}"
            )
        
        # Verify all results have completion_date
        for i, result in enumerate(self.selected_results):
            if result.completion_date is None:
                raise ValueError(
                    f"Result at index {i} has no completion_date"
                )
        
        # Verify all results are non-overlapping
        if len(self.selected_results) > 1:
            sorted_results = sorted(self.selected_results, key=lambda x: x.start_date)
            for i in range(len(sorted_results) - 1):
                if sorted_results[i].completion_date > sorted_results[i + 1].start_date:
                    raise ValueError(
                        f"Results overlap: result {i} ends at {sorted_results[i].completion_date}, "
                        f"but result {i+1} starts at {sorted_results[i + 1].start_date}"
                    )

    @property
    def period_count(self) -> int:
        """Return the number of selected periods."""
        return len(self.selected_results)

    @property
    def is_schedule(self) -> bool:
        """Return True if this is a schedule (has total_cost)."""
        return self.total_cost is not None
