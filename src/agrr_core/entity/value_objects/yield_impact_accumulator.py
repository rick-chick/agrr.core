"""Yield impact accumulator value object.

Accumulates daily yield impacts from temperature stress across growth stages
with stage-specific sensitivity coefficients.

This value object:
- Receives daily stress impact rates from TemperatureProfile
- Applies stage-specific sensitivity coefficients  
- Accumulates multiplicative yield reduction
- Returns final yield factor (0-1)

Design:
- Immutable sensitivity configuration
- Mutable accumulation state
- Stage-aware sensitivity weighting

Literature-based sensitivity coefficients:
- Germination: Low sensitivity (0.2-0.3)
- Vegetative: Moderate sensitivity (0.2-0.3)
- Flowering/Heading: HIGH sensitivity (0.9-1.0) - CRITICAL PERIOD
- Grain filling: Moderate-High sensitivity (0.4-0.7)
- Ripening: Low sensitivity (0.1-0.3)

References:
- Porter, J. R., & Semenov, M. A. (2005). Crop responses to climatic variation.
- Matsui, T., et al. (2001). Effects of high temperature on flowering and seed-set in rice.
- Satake, T., & Hayase, H. (1970). Male sterility caused by cooling treatment.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

from agrr_core.entity.entities.growth_stage_entity import GrowthStage


@dataclass(frozen=True)
class StressSensitivity:
    """Stage-specific temperature stress sensitivity coefficients.
    
    All values range from 0 (no sensitivity) to 1 (full sensitivity).
    Higher values mean the stage is more vulnerable to that stress type.
    
    Fields:
        high_temp: Sensitivity to high temperature stress
        low_temp: Sensitivity to low temperature stress
        frost: Sensitivity to frost damage
        sterility: Sensitivity to sterility risk (flowering-specific)
    """
    
    high_temp: float = 0.5
    low_temp: float = 0.5
    frost: float = 0.7
    sterility: float = 0.9
    
    def __post_init__(self):
        """Validate sensitivity coefficients are in valid range."""
        for field_name in ["high_temp", "low_temp", "frost", "sterility"]:
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(
                    f"{field_name} sensitivity must be between 0 and 1, got {value}"
                )


# Default sensitivity by growth stage (literature-based)
DEFAULT_STAGE_SENSITIVITIES: Dict[str, StressSensitivity] = {
    # Germination: Relatively tolerant
    "germination": StressSensitivity(
        high_temp=0.2, low_temp=0.3, frost=0.5, sterility=0.0
    ),
    
    # Vegetative growth: Moderate sensitivity
    "vegetative": StressSensitivity(
        high_temp=0.3, low_temp=0.2, frost=0.5, sterility=0.3
    ),
    
    # Flowering/Heading: MOST SENSITIVE STAGE
    "flowering": StressSensitivity(
        high_temp=0.9, low_temp=0.9, frost=0.9, sterility=1.0
    ),
    "heading": StressSensitivity(
        high_temp=0.9, low_temp=0.9, frost=0.9, sterility=1.0
    ),
    
    # Grain filling: Moderate-high sensitivity (especially to heat)
    "grain_filling": StressSensitivity(
        high_temp=0.7, low_temp=0.4, frost=0.7, sterility=0.5
    ),
    
    # Ripening/Maturation: Lower sensitivity
    "ripening": StressSensitivity(
        high_temp=0.3, low_temp=0.1, frost=0.3, sterility=0.0
    ),
    "maturation": StressSensitivity(
        high_temp=0.3, low_temp=0.1, frost=0.3, sterility=0.0
    ),
}


@dataclass
class YieldImpactAccumulator:
    """Accumulates yield impacts from daily temperature stress.
    
    This accumulator:
    1. Receives daily stress impact rates from TemperatureProfile
    2. Applies stage-specific sensitivity coefficients
    3. Accumulates multiplicative yield reduction
    4. Provides final yield factor
    
    The yield factor is multiplicative across days:
        final_yield_factor = (1 - impact_day1) * (1 - impact_day2) * ...
    
    Usage:
        accumulator = YieldImpactAccumulator()
        for weather in weather_list:
            impacts = temperature_profile.calculate_daily_stress_impacts(weather)
            accumulator.accumulate_daily_impact(current_stage, impacts)
        
        yield_factor = accumulator.get_yield_factor()
        adjusted_revenue = original_revenue * yield_factor
    
    Fields:
        cumulative_yield_factor: Running product of daily impacts (1.0 = no impact)
        stage_sensitivities: Dict mapping stage names to sensitivity coefficients
    """
    
    cumulative_yield_factor: float = 1.0
    stage_sensitivities: Dict[str, StressSensitivity] = field(
        default_factory=lambda: DEFAULT_STAGE_SENSITIVITIES.copy()
    )
    
    def accumulate_daily_impact(
        self,
        stage: GrowthStage,
        daily_impacts: Dict[str, float],
    ) -> None:
        """Accumulate daily stress impact for a specific growth stage.
        
        Args:
            stage: Current growth stage
            daily_impacts: Dict of impact rates from TemperatureProfile.calculate_daily_stress_impacts()
                          Keys: 'high_temp', 'low_temp', 'frost', 'sterility'
                          Values: Daily impact rates (0.0 = no stress, 0.05 = 5% reduction, etc.)
        
        Effects:
            Updates cumulative_yield_factor (multiplicative accumulation)
        
        Example:
            Daily impact: high_temp=0.05, sensitivity=0.9
            → Weighted impact = 0.05 * 0.9 = 0.045 (4.5% reduction)
            → Daily factor = 1.0 - 0.045 = 0.955
            → cumulative_yield_factor *= 0.955
        """
        sensitivity = self._get_sensitivity(stage.name)
        
        # Apply sensitivity-weighted impacts (multiplicative across stress types)
        for stress_type, impact_rate in daily_impacts.items():
            if impact_rate > 0:
                # Get sensitivity coefficient for this stress type
                sens_value = getattr(sensitivity, stress_type)
                
                # Calculate weighted impact
                weighted_impact = impact_rate * sens_value
                
                # Apply multiplicative reduction
                daily_factor = 1.0 - weighted_impact
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
    
    def _get_sensitivity(self, stage_name: str) -> StressSensitivity:
        """Get sensitivity for a stage with fallback to default.
        
        Performs flexible matching:
        1. Exact match (case-insensitive, normalized)
        2. Partial match (substring)
        3. Fallback to moderate sensitivity
        
        Args:
            stage_name: Name of the growth stage
            
        Returns:
            StressSensitivity for the stage
        """
        # Normalize stage name (lowercase, remove spaces/underscores)
        normalized_name = stage_name.lower().replace(" ", "_").replace("-", "_")
        
        # Try exact match
        if normalized_name in self.stage_sensitivities:
            return self.stage_sensitivities[normalized_name]
        
        # Try partial match (for variations like "grain filling" vs "grain_filling")
        for key in self.stage_sensitivities.keys():
            if key in normalized_name or normalized_name in key:
                return self.stage_sensitivities[key]
        
        # Fallback to moderate sensitivity
        return StressSensitivity(
            high_temp=0.5,
            low_temp=0.5,
            frost=0.7,
            sterility=0.5,
        )
    
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

