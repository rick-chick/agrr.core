"""Optimal growth period calculation request DTO.

This DTO carries the input parameters needed to find the optimal growth period
that minimizes total cost based on daily fixed costs.

Fields
- crop_id: Crop identifier (e.g., "rice", "tomato")
- variety: Optional variety/cultivar
- candidate_start_dates: List of candidate start dates to evaluate
- weather_data_file: Path to weather data file (JSON or CSV)
- daily_fixed_cost: Daily fixed cost (e.g., greenhouse management, labor)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class OptimalGrowthPeriodRequestDTO:
    """Request DTO for optimal growth period calculation use case."""

    crop_id: str
    variety: Optional[str]
    candidate_start_dates: List[datetime]
    weather_data_file: str
    daily_fixed_cost: float  # Daily fixed cost (currency/day)

    def __post_init__(self):
        """Validate input parameters."""
        if not self.candidate_start_dates:
            raise ValueError("candidate_start_dates must not be empty")
        if self.daily_fixed_cost < 0:
            raise ValueError(f"daily_fixed_cost must be non-negative, got {self.daily_fixed_cost}")

