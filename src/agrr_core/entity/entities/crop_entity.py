"""Crop entity.

Represents a crop (and optionally a variety) as a stable identifier used to
associate stage requirements and assessments. This entity intentionally holds
no thresholds; thresholds live in the requirement/profile entities.

Fields
- crop_id: Stable string identifier (e.g., "rice", "tomato")
- name: Human-readable crop name (e.g., "Rice")
- area_per_unit: Area occupied per unit of crop in square meters (m²)
- variety: Optional variety/cultivar label (e.g., "Koshihikari")
- revenue_per_area: Optional revenue per square meter (e.g., yen/m²)
- max_revenue: Optional maximum revenue constraint (e.g., yen)
  This represents business constraints such as market demand limits or contract caps.
  Directly specifying revenue limit is simpler than calculating from quantity constraints.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Crop:
    """Represents a crop with optional variety and revenue information."""

    crop_id: str
    name: str
    area_per_unit: float
    variety: Optional[str] = None
    revenue_per_area: Optional[float] = None
    max_revenue: Optional[float] = None


