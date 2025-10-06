"""Crop entity.

Represents a crop (and optionally a variety) as a stable identifier used to
associate stage requirements and assessments. This entity intentionally holds
no thresholds; thresholds live in the requirement/profile entities.

Fields
- crop_id: Stable string identifier (e.g., "rice", "tomato")
- name: Human-readable crop name (e.g., "Rice")
- variety: Optional variety/cultivar label (e.g., "Koshihikari")
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Crop:
    """Represents a crop with optional variety information."""

    crop_id: str
    name: str
    variety: Optional[str] = None


