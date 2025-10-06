"""Assessment result entity.

Immutable container for daily assessment results. Values are basic primitives
to simplify serialization and inter-layer boundaries.

Fields
- date_iso: ISO-8601 date string corresponding to the weather observation.
- ok_temperature / low_temp_stress / high_temp_stress / frost_risk / sterility_risk:
  Temperature-related flags.
- low_sun / good_sun: Sunshine-related flags.
- gdd_of_the_day: Daily degree-days computed from mean temperature and base.
- gdd_cumulative: Cumulative degree-days within the current stage.
- daily_temperature_range: (t_max - t_min) if available; else None.
- photo_thermal_index: (t_mean * sunshine_hours) if available; else None.
"""

from dataclasses import dataclass
from typing import Optional

from agrr_core.entity.entities.weather_entity import WeatherData


@dataclass(frozen=True)
class AssessmentResult:
    """Holds daily assessment flags and indices for a stage."""

    date_iso: str
    ok_temperature: bool
    low_temp_stress: bool
    high_temp_stress: bool
    frost_risk: bool
    sterility_risk: bool
    low_sun: bool
    good_sun: bool
    gdd_of_the_day: float
    gdd_cumulative: float
    daily_temperature_range: Optional[float]
    photo_thermal_index: Optional[float]


