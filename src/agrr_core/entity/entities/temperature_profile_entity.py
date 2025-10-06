"""Temperature profile entity defining thresholds and judgments.

This entity encapsulates crop- and growth-stage-specific temperature thresholds
and provides pure, side-effect-free judgment helpers used by use cases.

Design goals
- Keep domain logic close to the data model (entity), not in controllers.
- Make each method deterministic and easily testable with scalar inputs.
- Avoid external dependencies to preserve portability (LLM-friendly).

Units & semantics
- All temperatures are degrees Celsius (float).
- Returns from boolean judgments are `True` when the condition holds, otherwise `False`.
- Missing observations (None) yield conservative `False` for risk/fitness tests and 0.0 for GDD.

Field meanings
- base_temperature: GDD base (a.k.a. lower developmental threshold).
- optimal_min/optimal_max: temperature range considered suitable for growth at the stage.
- low_stress_threshold: mean temperature below this implies low-temperature stress.
- high_stress_threshold: mean temperature above this implies high-temperature stress.
- frost_threshold: minimum temperature at or below this implies frost risk.
- sterility_risk_threshold: maximum temperature at or above this implies sterility risk
  (only relevant for sensitive stages such as flowering; optional).

Invariants
- optimal_min <= optimal_max
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TemperatureProfile:
    """Temperature thresholds for a crop at a given growth stage.

    Methods implement simple rule-based judgments so that an upstream LLM can
    propose thresholds per crop/stage, and downstream use cases can evaluate
    daily weather without patching or external services.
    """

    base_temperature: float  # GDD base
    optimal_min: float
    optimal_max: float
    low_stress_threshold: float
    high_stress_threshold: float
    frost_threshold: float
    sterility_risk_threshold: Optional[float] = None

    def is_ok_temperature(self, t_mean: Optional[float]) -> bool:
        """Return True if mean temperature is within the optimal range.

        Args:
            t_mean: Daily mean temperature in °C.

        Returns:
            bool: True if optimal_min <= t_mean <= optimal_max, else False.
            Missing input (None) returns False.
        """
        if t_mean is None:
            return False
        return self.optimal_min <= t_mean <= self.optimal_max

    def is_low_temp_stress(self, t_mean: Optional[float]) -> bool:
        """Return True if mean temperature indicates low-temperature stress.

        Condition: t_mean < low_stress_threshold

        Args:
            t_mean: Daily mean temperature in °C.
        """
        if t_mean is None:
            return False
        return t_mean < self.low_stress_threshold

    def is_high_temp_stress(self, t_mean: Optional[float]) -> bool:
        """Return True if mean temperature indicates high-temperature stress.

        Condition: t_mean > high_stress_threshold

        Args:
            t_mean: Daily mean temperature in °C.
        """
        if t_mean is None:
            return False
        return t_mean > self.high_stress_threshold

    def is_frost_risk(self, t_min: Optional[float]) -> bool:
        """Return True if minimum temperature indicates frost risk.

        Condition: t_min <= frost_threshold

        Args:
            t_min: Daily minimum temperature in °C.
        """
        if t_min is None:
            return False
        return t_min <= self.frost_threshold

    def is_sterility_risk(self, t_max: Optional[float]) -> bool:
        """Return True if maximum temperature indicates sterility risk.

        Condition: t_max >= sterility_risk_threshold
        Only evaluated when `sterility_risk_threshold` is provided.
        For stages where sterility is irrelevant, leave as None.

        Args:
            t_max: Daily maximum temperature in °C.
        """
        if t_max is None or self.sterility_risk_threshold is None:
            return False
        return t_max >= self.sterility_risk_threshold

    def daily_gdd(self, t_mean: Optional[float]) -> float:
        """Return daily growing degree days (non-negative).

        Formula: max(t_mean - base_temperature, 0)
        Missing input (None) returns 0.0.
        """
        if t_mean is None:
            return 0.0
        delta = t_mean - self.base_temperature
        return delta if delta > 0 else 0.0


