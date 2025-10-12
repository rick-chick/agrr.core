"""Optimization intermediate result entity.

Represents the intermediate results of growth period optimization,
including start date, completion date, accumulated GDD, cost, and other metrics
for each candidate start date.

Fields
- start_date: Cultivation start date
- completion_date: Date when growth reaches 100% (None if not completed)
- growth_days: Number of days from start to completion (None if not completed)
- accumulated_gdd: Total accumulated growing degree days (°C·day)
- total_cost: Total cost for this period (None if not completed or deadline exceeded)
- is_optimal: True if this is the optimal candidate
- base_temperature: Base temperature used for GDD calculation (°C)
- revenue: Optional revenue for profit calculation
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from agrr_core.entity.value_objects.optimization_objective import OptimizationMetrics


@dataclass(frozen=True)
class OptimizationIntermediateResult:
    """Represents intermediate results for a single candidate start date in optimization.
    
    This entity captures all relevant metrics calculated during the optimization process,
    including temporal, thermal, and cost information.
    
    Implements Optimizable protocol for unified optimization.
    """

    start_date: datetime
    completion_date: Optional[datetime]
    growth_days: Optional[int]
    accumulated_gdd: float
    total_cost: Optional[float]
    is_optimal: bool
    base_temperature: float
    revenue: Optional[float] = None  # Optional revenue for profit calculation

    def __post_init__(self):
        """Validate invariants."""
        if self.accumulated_gdd < 0.0:
            raise ValueError(
                f"accumulated_gdd must be non-negative, got {self.accumulated_gdd}"
            )
        
        if self.growth_days is not None and self.growth_days < 0:
            raise ValueError(
                f"growth_days must be non-negative, got {self.growth_days}"
            )
        
        if self.total_cost is not None and self.total_cost < 0.0:
            raise ValueError(
                f"total_cost must be non-negative, got {self.total_cost}"
            )
        
        if self.revenue is not None and self.revenue < 0.0:
            raise ValueError(
                f"revenue must be non-negative, got {self.revenue}"
            )
        
        # If completed, completion_date and growth_days should be set
        if self.completion_date is not None:
            if self.completion_date < self.start_date:
                raise ValueError(
                    f"completion_date ({self.completion_date}) must be after or equal to start_date ({self.start_date})"
                )
    
    def get_metrics(self) -> OptimizationMetrics:
        """Get optimization metrics (implements Optimizable protocol).
        
        Returns:
            OptimizationMetrics for this result
            
        Raises:
            ValueError: If total_cost is None (invalid result)
        """
        if self.total_cost is None:
            raise ValueError("Cannot get metrics for result without total_cost")
        
        return OptimizationMetrics(
            cost=self.total_cost,
            revenue=self.revenue
        )

