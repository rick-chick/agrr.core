"""Yield impact accumulator value object.

Accumulates daily yield impacts from temperature stress.

This value object:
- Receives daily stress impact rates from TemperatureProfile
- Accumulates multiplicative yield reduction
- Returns final yield factor (0-1)

Design:
- Simple accumulation without stage-specific sensitivity adjustments
- Daily impact rates are applied directly as defined in TemperatureProfile
- Mutable accumulation state

References:
- Porter, J. R., & Semenov, M. A. (2005). Crop responses to climatic variation.
- Matsui, T., et al. (2001). Effects of high temperature on flowering and seed-set in rice.
- Satake, T., & Hayase, H. (1970). Male sterility caused by cooling treatment.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class YieldImpactAccumulator:
    """Accumulates yield impacts from daily temperature stress.
    
    This accumulator:
    1. Receives daily stress impact rates from TemperatureProfile
    2. Accumulates multiplicative yield reduction (no stage-specific adjustments)
    3. Provides final yield factor
    
    The yield factor is multiplicative across days:
        final_yield_factor = (1 - impact_day1) * (1 - impact_day2) * ...
    
    Usage:
        accumulator = YieldImpactAccumulator()
        for weather in weather_list:
            impacts = temperature_profile.calculate_daily_stress_impacts(weather)
            accumulator.accumulate_daily_impact(impacts)
        
        yield_factor = accumulator.get_yield_factor()
        adjusted_revenue = original_revenue * yield_factor
    
    Fields:
        cumulative_yield_factor: Running product of daily impacts (1.0 = no impact)
    """
    
    cumulative_yield_factor: float = 1.0
    
    def accumulate_daily_impact(
        self,
        daily_impacts: Dict[str, float],
    ) -> None:
        """Accumulate daily stress impact.
        
        Args:
            daily_impacts: Dict of impact rates from TemperatureProfile.calculate_daily_stress_impacts()
                          Keys: 'high_temp', 'low_temp', 'frost', 'sterility'
                          Values: Daily impact rates (0.0 = no stress, 0.05 = 5% reduction, etc.)
        
        Effects:
            Updates cumulative_yield_factor (multiplicative accumulation)
        
        Example:
            Daily impact: high_temp=0.05 (5% reduction)
            → Daily factor = 1.0 - 0.05 = 0.95
            → cumulative_yield_factor *= 0.95
        """
        # Apply impacts directly (multiplicative across stress types)
        for stress_type, impact_rate in daily_impacts.items():
            if impact_rate > 0:
                # Apply multiplicative reduction
                daily_factor = 1.0 - impact_rate
                self.cumulative_yield_factor *= max(0.0, daily_factor)
    
    def get_yield_factor(self) -> float:
        """Get final cumulative yield factor.
        
        Returns:
            Yield factor (0-1): 
                - 1.0 = no yield impact
                - 0.9 = 10% yield reduction
                - 0.0 = complete yield loss
        
        The yield factor should be multiplied with the base revenue:
            adjusted_revenue = base_revenue * yield_factor
        """
        return max(0.0, self.cumulative_yield_factor)
    
    def get_yield_loss_percentage(self) -> float:
        """Get yield loss as a percentage.
        
        Returns:
            Yield loss percentage (0-100):
                - 0% = no loss
                - 10% = 10% yield reduction
                - 100% = complete loss
        """
        return (1.0 - self.get_yield_factor()) * 100.0
    
    def reset(self) -> None:
        """Reset accumulator to initial state.
        
        Useful for calculating yield impacts for multiple scenarios
        with the same accumulator instance.
        """
        self.cumulative_yield_factor = 1.0
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        yield_factor = self.get_yield_factor()
        loss_pct = self.get_yield_loss_percentage()
        return (
            f"YieldImpactAccumulator("
            f"yield_factor={yield_factor:.3f}, "
            f"yield_loss={loss_pct:.1f}%)"
        )

