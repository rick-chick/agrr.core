"""Thermal requirement entity defining GDD needs and helpers.

This entity represents the growing degree days (GDD) needed to complete a
growth stage. It intentionally does not compute daily GDD; that is handled by
`TemperatureProfile.daily_gdd` using the configured base temperature.

Units & semantics
- required_gdd is expressed in degree-days (°C·day).
- harvest_start_gdd is optional and only used for harvest stage of fruiting crops.
- `is_met` returns True when the cumulative GDD has reached the requirement.
"""

from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class ThermalRequirement:
    """Required growing degree days for a stage to complete.

    Fields:
    - required_gdd: Total GDD to complete the stage (°C·day)
    - harvest_start_gdd: Optional GDD to initial harvest (°C·day)
        * Only applicable to harvest stage of fruiting crops
        * For other stages (germination, vegetative, etc.), leave as None
        * For fruiting crops: harvest_start_gdd < required_gdd
    
    For fruiting vegetables (tomato, eggplant, cucumber, etc.):
    - harvest_start_gdd: GDD when first harvest becomes possible
    - required_gdd: GDD when harvest period ends (maximum yield)
    - Harvest duration = required_gdd - harvest_start_gdd
    
    For other crops (rice, wheat, leafy vegetables):
    - harvest_start_gdd is None (not applicable)
    - required_gdd: GDD to maturity/harvest

    Typical flow: sum(`TemperatureProfile.daily_gdd`) across days within the
    stage, then call `is_met` with the cumulative total.
    """

    required_gdd: float
    harvest_start_gdd: Optional[float] = None

    def __post_init__(self) -> None:
        """Validate thermal requirements."""
        if self.required_gdd <= 0:
            raise ValueError(f"required_gdd must be positive, got {self.required_gdd}")
        
        if self.harvest_start_gdd is not None:
            if self.harvest_start_gdd <= 0:
                raise ValueError(
                    f"harvest_start_gdd must be positive, got {self.harvest_start_gdd}"
                )
            if self.harvest_start_gdd >= self.required_gdd:
                raise ValueError(
                    f"harvest_start_gdd ({self.harvest_start_gdd}) must be less than "
                    f"required_gdd ({self.required_gdd})"
                )

    def is_met(self, cumulative_gdd: float) -> bool:
        """Return True if cumulative GDD meets/exceeds the requirement.

        Args:
            cumulative_gdd: Accumulated degree-days within the stage (°C·day).
        """
        return cumulative_gdd >= self.required_gdd

    def is_harvest_started(self, cumulative_gdd: float) -> bool:
        """Return True if harvest has started (for fruiting crops).
        
        For harvest stage with harvest_start_gdd:
        - Returns True when cumulative_gdd >= harvest_start_gdd
        
        For other stages (harvest_start_gdd is None):
        - Returns same as is_met() (stage completion)
        
        Args:
            cumulative_gdd: Accumulated degree-days within the stage (°C·day).
        """
        if self.harvest_start_gdd is None:
            return self.is_met(cumulative_gdd)
        return cumulative_gdd >= self.harvest_start_gdd

