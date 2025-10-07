"""Growth progress timeline entity.

Represents the complete timeline of growth progress from start date to harvest,
binding a crop to its daily progress records.

Fields
- crop: The crop being tracked
- start_date: Growth start date (sowing/planting date)
- progress_list: Ordered list of daily growth progress records
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List

from agrr_core.entity.entities.crop_entity import Crop
from agrr_core.entity.entities.growth_progress_entity import GrowthProgress


@dataclass(frozen=True)
class GrowthProgressTimeline:
    """Associates a crop with its daily growth progress timeline.
    
    Invariants
    - progress_list should be ordered by date (ascending)
    - All progress records must have the same total_required_gdd
    """

    crop: Crop
    start_date: datetime
    progress_list: List[GrowthProgress]

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

