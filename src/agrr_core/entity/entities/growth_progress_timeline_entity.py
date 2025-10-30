"""Growth progress timeline entity.

Represents the complete timeline of growth progress from start date to harvest,
binding a crop to its daily progress records.

Fields
- crop: The crop being tracked
- start_date: Growth start date (sowing/planting date)
- progress_list: Ordered list of daily growth progress records
- yield_factor: Cumulative yield reduction factor from temperature stress (0-1)
               1.0 = no yield impact, 0.0 = total crop failure
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.growth_progress_entity import GrowthProgress

@dataclass(frozen=True)
class GrowthProgressTimeline:
    """Associates a crop with its daily growth progress timeline.
    
    Invariants
    - progress_list should be ordered by date (ascending)
    - All progress records must have the same total_required_gdd
    - yield_factor must be between 0.0 and 1.0 if provided
    """

    crop: Crop
    start_date: datetime
    progress_list: List[GrowthProgress]
    yield_factor: Optional[float] = None  # Yield impact from temperature stress

    def get_final_progress(self) -> GrowthProgress:
        """Return the last progress record in the timeline."""
        if not self.progress_list:
            raise ValueError("progress_list is empty")
        return self.progress_list[-1]

    def is_harvest_ready(self) -> bool:
        """Return True if the final progress indicates completion."""
        if not self.progress_list:
            return False
        return self.get_final_progress().is_complete
    
    def get_yield_loss_percentage(self) -> float:
        """Return yield loss percentage from temperature stress.
        
        Returns:
            Yield loss percentage (0-100):
            - 0% = no yield loss
            - 10% = 10% yield reduction
            - 100% = complete crop failure
        """
        if self.yield_factor is None:
            return 0.0  # No stress data available
        return (1.0 - self.yield_factor) * 100.0

