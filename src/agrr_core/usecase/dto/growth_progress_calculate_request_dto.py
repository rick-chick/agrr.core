"""Growth progress calculation request DTO.

This DTO carries the input parameters needed to calculate growth progress
from a given start date using weather data.

Fields
- crop_id: Crop identifier (e.g., "rice", "tomato")
- variety: Optional variety/cultivar
- start_date: Growth start date (sowing/planting date)
- weather_data_file: Path to weather data file (JSON or CSV)
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
    weather_data_file: str  # Path to weather data file (JSON or CSV)

