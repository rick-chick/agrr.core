"""Stage requirement entity combining profiles and thermal needs.

This entity is a composition of temperature, sunshine, and thermal (GDD)
requirements for a specific growth stage. It exposes deterministic helpers to
judge daily conditions and compute indices from a `WeatherData` input.

Usage with LLMs
- Upstream LLM proposes profile values per crop/stage from literature/knowledge.
- Application constructs `StageRequirement` from those values.
- Use cases evaluate daily `WeatherData` to produce flags/indices.

Returns are simple primitives (bool/float) to make serialization and testing
straightforward.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any

from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement
from agrr_core.entity.entities.weather_entity import WeatherData
from agrr_core.entity.entities.growth_stage_entity import GrowthStage


@dataclass(frozen=True)
class StageRequirement:
    """Requirement set for a growth stage (temperature, sunshine, thermal).

    Fields
    - temperature: `TemperatureProfile` thresholds and GDD base
    - sunshine: `SunshineProfile` thresholds
    - thermal: `ThermalRequirement` cumulative GDD target
    """

    stage: GrowthStage
    temperature: TemperatureProfile
    sunshine: SunshineProfile
    thermal: ThermalRequirement

    def judge_temperature(self, weather: WeatherData) -> Dict[str, bool]:
        """Evaluate temperature-related flags for a given day.

        Returns dict with keys:
        - okTemperature
        - lowTempStress
        - highTempStress
        - frostRisk
        - sterilityRisk
        """
        t_mean = weather.temperature_2m_mean
        t_min = weather.temperature_2m_min
        t_max = weather.temperature_2m_max
        return {
            "okTemperature": self.temperature.is_ok_temperature(t_mean),
            "lowTempStress": self.temperature.is_low_temp_stress(t_mean),
            "highTempStress": self.temperature.is_high_temp_stress(t_mean),
            "frostRisk": self.temperature.is_frost_risk(t_min),
            "sterilityRisk": self.temperature.is_sterility_risk(t_max),
        }

    def judge_sunshine(self, weather: WeatherData) -> Dict[str, bool]:
        """Evaluate sunshine-related flags for a given day.

        Returns dict with keys:
        - lowSun
        - goodSun
        """
        sun_h = weather.sunshine_hours
        return {
            "lowSun": self.sunshine.is_low_sun(sun_h),
            "goodSun": self.sunshine.is_good_sun(sun_h),
        }

    def daily_gdd(self, weather: WeatherData) -> float:
        """Return daily GDD using the temperature profile's base temperature."""
        return self.temperature.daily_gdd(weather.temperature_2m_mean)

    def is_thermal_met(self, gdd_cumulative: float) -> bool:
        """Return True if cumulative GDD meets the thermal requirement."""
        return self.thermal.is_met(gdd_cumulative)


