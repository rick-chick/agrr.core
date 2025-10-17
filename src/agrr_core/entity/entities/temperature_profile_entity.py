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
    
    # Yield impact rates (literature-based, can be overridden per crop/stage)
    high_temp_daily_impact: float = 0.05  # 5% yield reduction per day
    low_temp_daily_impact: float = 0.08   # 8% yield reduction per day
    frost_daily_impact: float = 0.15      # 15% yield reduction per day
    sterility_daily_impact: float = 0.20  # 20% yield reduction per day

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
        """Return daily growing degree days with temperature efficiency (trapezoidal model).
        
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

    def daily_gdd_simple(self, t_mean: Optional[float]) -> float:
        """Return daily GDD using simple linear model (for backward compatibility).

        Formula: max(t_mean - base_temperature, 0)
        Missing input (None) returns 0.0.
        
        Note: This is the simple linear model without temperature efficiency.
        The default daily_gdd() method now uses the trapezoidal model.
        """
        if t_mean is None:
            return 0.0
        delta = t_mean - self.base_temperature
        return delta if delta > 0 else 0.0
    
    def daily_gdd_modified(self, t_mean: Optional[float]) -> float:
        """Alias for daily_gdd() for backward compatibility.
        
        This method now simply calls daily_gdd() as the trapezoidal model
        is now the default behavior.
        """
        return self.daily_gdd(t_mean)
    
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
    
    def calculate_daily_stress_impacts(
        self,
        weather: "WeatherData",
    ) -> dict:
        """Calculate daily stress impact rates from temperature conditions.
        
        This method evaluates temperature stress and returns impact rates for
        each stress type. These rates represent the daily yield reduction factor
        (0.0 = no stress, 0.05 = 5% reduction, etc.) before applying stage-specific
        sensitivity coefficients.
        
        The impact rates are based on literature review:
        - High temperature stress: 5% per day (Matsui et al., 2001)
        - Low temperature stress: 8% per day (Satake & Hayase, 1970)
        - Frost damage: 15% per day (Porter & Gawith, 1999)
        - Sterility risk: 20% per day (high temperature during flowering)
        
        Enhanced with GDD efficiency-based attenuation:
        - If daily mean temperature has high GDD efficiency (close to optimal),
          stress impacts from peak temperatures are attenuated
        - This prevents over-penalization from brief temperature spikes
        - Based on DSSAT/APSIM trapezoidal temperature response models
        
        Args:
            weather: Daily weather data containing temperature observations.
        
        Returns:
            Dict with keys: 'high_temp', 'low_temp', 'frost', 'sterility'
            Values are daily impact rates (0.0 to 1.0).
            
        Example:
            >>> profile = TemperatureProfile(...)
            >>> weather = WeatherData(temperature_2m_mean=36.0, ...)
            >>> impacts = profile.calculate_daily_stress_impacts(weather)
            >>> impacts['high_temp']  # Attenuated if mean temp has high efficiency
        """
        # Import WeatherData type for type checking
        from agrr_core.entity.entities.weather_entity import WeatherData
        
        impacts = {
            "high_temp": 0.0,
            "low_temp": 0.0,
            "frost": 0.0,
            "sterility": 0.0,
        }
        
        # Calculate GDD efficiency for daily mean temperature
        # This represents how favorable the overall day is for growth
        mean_temp_efficiency = self._calculate_temperature_efficiency(weather.temperature_2m_mean)
        
        # High temperature stress (use max temperature for daily peak)
        # Apply GDD efficiency-based attenuation
        if self.is_high_temp_stress(weather.temperature_2m_max):
            # Calculate the proportion of day above threshold
            # Assumption: temperature varies linearly from min to max
            temp_range = weather.temperature_2m_max - weather.temperature_2m_min
            if temp_range > 0 and self.high_stress_threshold is not None:
                temp_above_threshold = weather.temperature_2m_max - self.high_stress_threshold
                stress_proportion = min(1.0, temp_above_threshold / temp_range)
                base_impact = self.high_temp_daily_impact * stress_proportion
                
                # Attenuate stress impact based on mean temperature efficiency
                # High efficiency (close to optimal) → lower stress impact
                # Low efficiency (far from optimal) → full stress impact
                # Formula: impact = base_impact * (1 - efficiency * 0.7)
                # - efficiency=1.0 (optimal): 70% reduction in stress impact
                # - efficiency=0.5 (sub-optimal): 35% reduction
                # - efficiency=0.0 (poor): no reduction (full impact)
                attenuation_factor = 1.0 - (mean_temp_efficiency * 0.7)
                impacts["high_temp"] = base_impact * attenuation_factor
            else:
                impacts["high_temp"] = self.high_temp_daily_impact
        
        # Low temperature stress
        # Use mean temperature for evaluation (already based on daily average)
        if self.is_low_temp_stress(weather.temperature_2m_mean):
            impacts["low_temp"] = self.low_temp_daily_impact
        
        # Frost risk (critical damage, no attenuation)
        if self.is_frost_risk(weather.temperature_2m_min):
            impacts["frost"] = self.frost_daily_impact
        
        # Sterility risk (critical reproductive damage, no attenuation)
        if self.is_sterility_risk(weather.temperature_2m_max):
            impacts["sterility"] = self.sterility_daily_impact
        
        return impacts


