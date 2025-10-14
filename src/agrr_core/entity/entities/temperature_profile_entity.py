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
- max_temperature: upper developmental threshold where growth stops (developmental arrest temperature).

Invariants
- base_temperature < optimal_min <= optimal_max < max_temperature
- base_temperature < max_temperature
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

    base_temperature: float  # GDD base (lower developmental threshold)
    optimal_min: float
    optimal_max: float
    low_stress_threshold: float
    high_stress_threshold: float
    frost_threshold: float
    max_temperature: float  # Upper developmental threshold (developmental arrest temperature)
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
        
        Note: This is the simple linear model. For temperature efficiency consideration,
        use daily_gdd_modified() instead.
        """
        if t_mean is None:
            return 0.0
        delta = t_mean - self.base_temperature
        return delta if delta > 0 else 0.0

    def daily_gdd_modified(self, t_mean: Optional[float]) -> float:
        """Return daily GDD with temperature efficiency (trapezoidal model).
        
        This method accounts for reduced developmental rate outside the optimal
        temperature range, based on DSSAT and APSIM crop models.
        
        Temperature efficiency zones:
        1. T <= base_temperature or T >= max_temperature: efficiency = 0 (no growth)
        2. base_temperature < T < optimal_min: linear ramp-up
        3. optimal_min <= T <= optimal_max: efficiency = 1.0 (optimal)
        4. optimal_max < T < max_temperature: linear ramp-down
        
        Formula:
            modified_gdd = (T - T_base) * efficiency(T)
        
        Args:
            t_mean: Daily mean temperature in °C.
        
        Returns:
            Modified GDD accounting for temperature efficiency (0.0 or positive).
            Missing input (None) returns 0.0.
        
        References:
            - DSSAT crop model (trapezoidal temperature response)
            - APSIM (three cardinal temperatures model)
        """
        if t_mean is None:
            return 0.0
        
        # Outside viable temperature range
        if t_mean <= self.base_temperature or t_mean >= self.max_temperature:
            return 0.0
        
        # Base GDD (linear model)
        base_gdd = t_mean - self.base_temperature
        
        # Calculate temperature efficiency (0-1)
        efficiency = self._calculate_temperature_efficiency(t_mean)
        
        # Modified GDD
        return base_gdd * efficiency
    
    def _calculate_temperature_efficiency(self, t_mean: float) -> float:
        """Calculate temperature efficiency using trapezoidal function.
        
        Args:
            t_mean: Daily mean temperature in °C.
        
        Returns:
            Efficiency coefficient (0.0 to 1.0).
        """
        # Optimal range: full efficiency
        if self.optimal_min <= t_mean <= self.optimal_max:
            return 1.0
        
        # Sub-optimal (cool side): linear ramp-up
        elif self.base_temperature < t_mean < self.optimal_min:
            efficiency = (t_mean - self.base_temperature) / \
                        (self.optimal_min - self.base_temperature)
            return max(0.0, min(1.0, efficiency))
        
        # Sub-optimal (warm side): linear ramp-down
        elif self.optimal_max < t_mean < self.max_temperature:
            efficiency = (self.max_temperature - t_mean) / \
                        (self.max_temperature - self.optimal_max)
            return max(0.0, min(1.0, efficiency))
        
        # Outside range (should not reach here due to earlier checks)
        else:
            return 0.0


