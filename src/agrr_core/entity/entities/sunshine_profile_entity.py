"""Sunshine profile entity defining sunshine requirements and judgments.

This entity encapsulates daily sunshine-hour requirements per crop and stage.
It provides deterministic checks usable by both rules and LLM-proposed configs.

Units & semantics
- Hours are float hours per day (h/day).
- Missing inputs and missing thresholds produce conservative False.

Field meanings
- minimum_sunshine_hours: Threshold below which the day is considered low-sun.
- target_sunshine_hours: Threshold at or above which the day is considered good-sun.

Invariants
- When both are provided: 0 <= minimum_sunshine_hours <= target_sunshine_hours
"""

from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class SunshineProfile:
    """Sunshine requirements for a crop at a given growth stage.

    Each method implements a simple threshold check. Use cases can combine these
    with temperature judgments to form daily assessments.
    """

    minimum_sunshine_hours: Optional[float] = None
    target_sunshine_hours: Optional[float] = None

    def is_low_sun(self, sunshine_hours: Optional[float]) -> bool:
        """Return True if the day is considered low-sun.

        Condition: sunshine_hours < minimum_sunshine_hours
        Missing input or missing threshold returns False.
        """
        if sunshine_hours is None or self.minimum_sunshine_hours is None:
            return False
        return sunshine_hours < self.minimum_sunshine_hours

    def is_good_sun(self, sunshine_hours: Optional[float]) -> bool:
        """Return True if the day meets or exceeds target sunshine.

        Condition: sunshine_hours >= target_sunshine_hours
        Missing input or missing threshold returns False.
        """
        if sunshine_hours is None or self.target_sunshine_hours is None:
            return False
        return sunshine_hours >= self.target_sunshine_hours

