"""Growth progress entity.

Represents the growth progress on a specific date, including cumulative GDD,
growth percentage, and the current growth stage.

Fields
- date: The date of this progress record
- cumulative_gdd: Accumulated growing degree days up to this date (°C·day)
- total_required_gdd: Total GDD required for complete growth cycle (°C·day)
- growth_percentage: Progress percentage (0.0 to 100.0)
- current_stage: The growth stage at this date
- is_complete: True if growth has reached 100% (harvest ready)
"""

from dataclasses import dataclass
from datetime import datetime

from agrr_core.entity.entities.growth_stage_entity import GrowthStage


@dataclass(frozen=True)
class GrowthProgress:
    """Represents growth progress at a specific date.
    
    Growth percentage is calculated as:
    (cumulative_gdd / total_required_gdd) * 100
    """

    date: datetime
    cumulative_gdd: float
    total_required_gdd: float
    growth_percentage: float  # 0.0 ~ 100.0
    current_stage: GrowthStage
    is_complete: bool

    def __post_init__(self):
        """Validate invariants."""
        if self.growth_percentage < 0.0 or self.growth_percentage > 100.0:
            raise ValueError(
                f"growth_percentage must be between 0.0 and 100.0, got {self.growth_percentage}"
            )
        if self.cumulative_gdd < 0.0:
            raise ValueError(
                f"cumulative_gdd must be non-negative, got {self.cumulative_gdd}"
            )
        if self.total_required_gdd <= 0.0:
            raise ValueError(
                f"total_required_gdd must be positive, got {self.total_required_gdd}"
            )

