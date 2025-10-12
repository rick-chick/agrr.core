"""Optimal growth period calculation request DTO.

This DTO carries the input parameters needed to find the optimal growth period
that minimizes total cost based on field's daily fixed costs.

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
- field: Field entity containing field information including daily_fixed_cost
- crop_requirement_file: Path to crop requirement file (optional)

Example:
    evaluation_period_start = 2024-04-01
    evaluation_period_end = 2024-06-30
    
    System will evaluate all start dates from 4/1 onwards and find the optimal
    start date where cultivation completes by 6/30 with minimum cost.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from agrr_core.entity.entities.field_entity import Field


@dataclass
class OptimalGrowthPeriodRequestDTO:
    """Request DTO for optimal growth period calculation use case."""

    crop_id: str
    variety: Optional[str]
    evaluation_period_start: datetime
    evaluation_period_end: datetime
    weather_data_file: str
    field: Field  # Field entity containing area, daily_fixed_cost, etc.
    crop_requirement_file: Optional[str] = None  # Path to crop requirement file (optional)

    def __post_init__(self):
        """Validate input parameters."""
        if self.evaluation_period_start > self.evaluation_period_end:
            raise ValueError(
                f"evaluation_period_start must be before or equal to evaluation_period_end, "
                f"got {self.evaluation_period_start} > {self.evaluation_period_end}"
            )

