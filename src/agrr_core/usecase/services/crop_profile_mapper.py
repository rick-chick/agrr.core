"""Mapper for CropProfile entities and DTOs.

This module provides mappers to convert between domain entities and data
transfer objects (DTOs) for crop profiles.
"""

from typing import Dict, Any

from agrr_core.entity.entities.crop_profile_entity import CropProfile
from agrr_core.entity.entities.stage_requirement_entity import StageRequirement
from agrr_core.entity.entities.temperature_profile_entity import TemperatureProfile
from agrr_core.entity.entities.sunshine_profile_entity import SunshineProfile
from agrr_core.entity.entities.thermal_requirement_entity import ThermalRequirement

class CropProfileMapper:
    """Map between CropProfile domain entities and data transfer objects.
    
    Responsibilities:
    - Convert CropProfile to response payload
    - Convert StageRequirement to dictionary
    - Handle nested entity structures
    
    Design Pattern: Mapper Pattern
    - Separates data transformation from business logic
    - Provides bidirectional conversion (if needed)
    - Centralizes entity-DTO mapping logic
    """
    
    @staticmethod
    def to_crop_profile_format(profile: CropProfile) -> Dict[str, Any]:
        """Convert CropProfile to standard file format.
        
        This method transforms a domain profile into the standard format
        used by progress and optimize-period commands.
        
        Args:
            profile: CropProfile domain entity
            
        Returns:
            Dictionary in standard crop profile file format
            
        Example:
            >>> crop = Crop("rice", "Rice", 0.25, variety="Koshihikari")
            >>> profile = CropProfile(crop, stage_reqs)
            >>> result = CropProfileMapper.to_crop_profile_format(profile)
            >>> result["crop"]["crop_id"]
            'rice'
        """
        return {
            "crop": {
                "crop_id": profile.crop.crop_id,
                "name": profile.crop.name,
                "variety": profile.crop.variety,
                "area_per_unit": profile.crop.area_per_unit,
                "revenue_per_area": profile.crop.revenue_per_area,
                "max_revenue": profile.crop.max_revenue,
                "groups": profile.crop.groups,
            },
            "stage_requirements": [
                {
                    "stage": {
                        "name": sr.stage.name,
                        "order": sr.stage.order,
                    },
                    "temperature": CropProfileMapper._temperature_to_dict(sr.temperature),
                    "thermal": CropProfileMapper._thermal_to_dict(sr.thermal),
                    "sunshine": CropProfileMapper._sunshine_to_dict(sr.sunshine),
                }
                for sr in profile.stage_requirements
            ],
        }
    
    @staticmethod
    def aggregate_to_payload(profile: CropProfile) -> Dict[str, Any]:
        """Convert CropProfile to response payload.
        
        This method transforms a domain profile into a dictionary suitable
        for API responses or presenter layers.
        
        Args:
            profile: CropProfile domain entity
            
        Returns:
            Dictionary representation suitable for response
            
        Example:
            >>> crop = Crop("rice", "Rice", 0.25, revenue_per_area=10000.0)
            >>> stage_reqs = [...]
            >>> profile = CropProfile(crop, stage_reqs)
            >>> payload = CropProfileMapper.aggregate_to_payload(profile)
            >>> payload["crop_id"]
            'rice'
        """
        return {
            "crop_id": profile.crop.crop_id,
            "crop_name": profile.crop.name,
            "variety": profile.crop.variety,
            "area_per_unit": profile.crop.area_per_unit,
            "revenue_per_area": profile.crop.revenue_per_area,
            "max_revenue": profile.crop.max_revenue,
            "groups": profile.crop.groups,
            "stages": [
                CropProfileMapper.stage_requirement_to_dict(sr)
                for sr in profile.stage_requirements
            ],
        }
    
    @staticmethod
    def stage_requirement_to_dict(stage_req: StageRequirement) -> Dict[str, Any]:
        """Convert StageRequirement entity to dictionary.
        
        Args:
            stage_req: StageRequirement entity
            
        Returns:
            Dictionary representation of stage requirement
            
        Example:
            >>> stage = GrowthStage("Growth", 1)
            >>> temp = TemperatureProfile(10.0, 20.0, 26.0, 12.0, 32.0, 0.0, 35.0)
            >>> sun = SunshineProfile(3.0, 6.0)
            >>> thermal = ThermalRequirement(400.0)
            >>> stage_req = StageRequirement(stage, temp, sun, thermal)
            >>> result = CropProfileMapper.stage_requirement_to_dict(stage_req)
            >>> result["name"]
            'Growth'
        """
        return {
            "name": stage_req.stage.name,
            "order": stage_req.stage.order,
            "temperature": CropProfileMapper._temperature_to_dict(
                stage_req.temperature
            ),
            "sunshine": CropProfileMapper._sunshine_to_dict(
                stage_req.sunshine
            ),
            "thermal": CropProfileMapper._thermal_to_dict(
                stage_req.thermal
            ),
        }
    
    @staticmethod
    def _temperature_to_dict(temperature: TemperatureProfile) -> Dict[str, float]:
        """Convert TemperatureProfile to dictionary.
        
        Args:
            temperature: TemperatureProfile entity
            
        Returns:
            Dictionary with temperature data
        """
        return {
            "base_temperature": temperature.base_temperature,
            "optimal_min": temperature.optimal_min,
            "optimal_max": temperature.optimal_max,
            "low_stress_threshold": temperature.low_stress_threshold,
            "high_stress_threshold": temperature.high_stress_threshold,
            "frost_threshold": temperature.frost_threshold,
            "sterility_risk_threshold": temperature.sterility_risk_threshold,
            "max_temperature": temperature.max_temperature,
        }
    
    @staticmethod
    def _sunshine_to_dict(sunshine: SunshineProfile) -> Dict[str, float]:
        """Convert SunshineProfile to dictionary.
        
        Args:
            sunshine: SunshineProfile entity
            
        Returns:
            Dictionary with sunshine data
        """
        return {
            "minimum_sunshine_hours": sunshine.minimum_sunshine_hours,
            "target_sunshine_hours": sunshine.target_sunshine_hours,
        }
    
    @staticmethod
    def _thermal_to_dict(thermal: ThermalRequirement) -> Dict[str, Any]:
        """Convert ThermalRequirement to dictionary.
        
        Args:
            thermal: ThermalRequirement entity
            
        Returns:
            Dictionary with thermal requirement data
        """
        result = {
            "required_gdd": thermal.required_gdd,
        }
        # Include harvest_start_gdd only if it's set (not None)
        if thermal.harvest_start_gdd is not None:
            result["harvest_start_gdd"] = thermal.harvest_start_gdd
        return result

# Backward compatibility alias
CropRequirementMapper = CropProfileMapper

