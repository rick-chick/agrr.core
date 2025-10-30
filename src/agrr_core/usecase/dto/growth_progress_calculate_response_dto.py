"""Growth progress calculation response DTO.

This DTO carries the calculated growth progress timeline back to the presenter.

Fields
- crop_name: Human-readable crop name
- variety: Variety/cultivar if specified
- start_date: Growth start date
- progress_records: List of daily progress records
  Each record contains: date, cumulative_gdd, growth_percentage, stage_name, is_complete
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass
class GrowthProgressRecordDTO:
    """Single progress record for a specific date."""

    date: datetime
    cumulative_gdd: float
    total_required_gdd: float
    growth_percentage: float
    stage_name: str
    is_complete: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "date": self.date.isoformat(),
            "cumulative_gdd": self.cumulative_gdd,
            "total_required_gdd": self.total_required_gdd,
            "growth_percentage": self.growth_percentage,
            "stage_name": self.stage_name,
            "is_complete": self.is_complete,
        }

@dataclass
class GrowthProgressCalculateResponseDTO:
    """Response DTO containing growth progress timeline."""

    crop_name: str
    variety: Optional[str]
    start_date: datetime
    progress_records: List[GrowthProgressRecordDTO]
    yield_factor: Optional[float] = None  # Cumulative yield impact (0-1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "crop_name": self.crop_name,
            "variety": self.variety,
            "start_date": self.start_date.isoformat(),
            "progress_records": [record.to_dict() for record in self.progress_records],
            "yield_factor": self.yield_factor,
            "yield_loss_percentage": (1.0 - self.yield_factor) * 100.0 if self.yield_factor else 0.0,
        }

