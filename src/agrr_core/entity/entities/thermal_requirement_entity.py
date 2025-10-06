"""Thermal requirement entity defining GDD needs and helpers.

This entity represents the growing degree days (GDD) needed to complete a
growth stage. It intentionally does not compute daily GDD; that is handled by
`TemperatureProfile.daily_gdd` using the configured base temperature.

Units & semantics
- required_gdd is expressed in degree-days (°C·day).
- `is_met` returns True when the cumulative GDD has reached the requirement.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThermalRequirement:
    """Required growing degree days for a stage to complete.

    Typical flow: sum(`TemperatureProfile.daily_gdd`) across days within the
    stage, then call `is_met` with the cumulative total.
    """

    required_gdd: float

    def is_met(self, cumulative_gdd: float) -> bool:
        """Return True if cumulative GDD meets/exceeds the requirement.

        Args:
            cumulative_gdd: Accumulated degree-days within the stage (°C·day).
        """
        return cumulative_gdd >= self.required_gdd


