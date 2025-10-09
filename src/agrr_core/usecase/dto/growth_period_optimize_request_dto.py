"""Optimal growth period calculation request DTO.

This DTO carries the input parameters needed to find the optimal growth period
that minimizes total cost based on daily fixed costs.

The optimization finds the best cultivation start date that:
1. Starts on or after evaluation_period_start
2. Completes cultivation by evaluation_period_end (completion deadline)
3. Minimizes total cost

Fields
- crop_id: Crop identifier (e.g., "rice", "tomato")
- variety: Optional variety/cultivar
- evaluation_period_start: Earliest possible start date for cultivation
- evaluation_period_end: Completion deadline (cultivation must finish by this date)
- weather_data_file: Path to weather data file (JSON or CSV)
- field_id: Field identifier (optional, for retrieving daily_fixed_cost from field data)
- daily_fixed_cost: Daily fixed cost (optional, used if field_id is not provided)
- crop_requirement_file: Path to crop requirement file (optional)

Note: Either field_id or daily_fixed_cost must be provided.

Example:
    evaluation_period_start = 2024-04-01
    evaluation_period_end = 2024-06-30
    
    System will evaluate all start dates from 4/1 onwards and find the optimal
    start date where cultivation completes by 6/30 with minimum cost.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OptimalGrowthPeriodRequestDTO:
    """Request DTO for optimal growth period calculation use case."""

    crop_id: str
    variety: Optional[str]
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    weather_data_file: str
    field_id: Optional[str] = None  # Field identifier (for retrieving daily_fixed_cost)
    daily_fixed_cost: Optional[float] = None  # Daily fixed cost (currency/day)
    crop_requirement_file: Optional[str] = None  # Path to crop requirement file (optional)

    def __post_init__(self):
        """Validate input parameters."""
        if self.evaluation_period_start > self.evaluation_period_end:
            raise ValueError(
                f"evaluation_period_start must be before or equal to evaluation_period_end, "
                f"got {self.evaluation_period_start} > {self.evaluation_period_end}"
            )
        
        # Either field_id or daily_fixed_cost must be provided
        if self.field_id is None and self.daily_fixed_cost is None:
            raise ValueError("Either field_id or daily_fixed_cost must be provided")
        
        # If both are provided, field_id takes precedence (daily_fixed_cost will be overridden)
        
        if self.daily_fixed_cost is not None and self.daily_fixed_cost < 0:
            raise ValueError(f"daily_fixed_cost must be non-negative, got {self.daily_fixed_cost}")

