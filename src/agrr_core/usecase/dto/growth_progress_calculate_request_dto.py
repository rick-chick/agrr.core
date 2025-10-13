"""Growth progress calculation request DTO.

This DTO carries the input parameters needed to calculate growth progress
from a given start date using weather data.

Fields
- crop_id: Crop identifier (e.g., "rice", "tomato")
- variety: Optional variety/cultivar
- start_date: Growth start date (sowing/planting date)

Note:
- Weather data is NOT in this DTO
- It is obtained by Interactor via Gateway that was initialized with appropriate repository
- File path is injected at Framework layer (Repository initialization), not UseCase layer
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class GrowthProgressCalculateRequestDTO:
    """Request DTO for growth progress calculation use case."""

    crop_id: str
    variety: Optional[str]
    start_date: datetime

